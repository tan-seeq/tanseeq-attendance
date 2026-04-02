"""
Telegram Bot Service for TANSEEQ HR
Sends automated attendance notifications via Telegram.
Uses direct HTTP calls to Telegram Bot API (no webhooks needed).
"""
import os
import httpx
import logging
import asyncio
from datetime import datetime, timezone

logger = logging.getLogger("telegram_service")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
_last_update_id = 0


async def _call_api(method: str, data: dict = None):
    """Call Telegram Bot API."""
    if not BOT_TOKEN:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{BOT_API}/{method}", json=data or {})
            result = resp.json()
            if not result.get("ok"):
                if method != "getUpdates":  # Don't spam logs for polling
                    logger.warning(f"Telegram API error: {result.get('description')}")
                return None
            return result.get("result")
    except Exception as e:
        if method != "getUpdates":
            logger.error(f"Telegram API call failed: {e}")
        return None


async def send_message(chat_id: int, text: str):
    """Send a text message to a Telegram user."""
    return await _call_api("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    })


async def get_bot_info():
    """Get bot information."""
    return await _call_api("getMe")


async def poll_updates(db):
    """Poll for new messages and handle /start link commands."""
    global _last_update_id
    if not BOT_TOKEN:
        return

    result = await _call_api("getUpdates", {
        "offset": _last_update_id + 1,
        "timeout": 0,
        "limit": 50,
    })
    if not result:
        return

    for update in result:
        _last_update_id = update["update_id"]
        message = update.get("message")
        if not message or not message.get("text"):
            continue

        chat_id = message["chat"]["id"]
        text = message["text"].strip()
        user_name = message["from"].get("first_name", "")

        # Handle /start with link code
        if text.startswith("/start"):
            parts = text.split(" ", 1)
            if len(parts) == 2:
                link_code = parts[1].strip()
                await _handle_link(db, chat_id, link_code, user_name)
            else:
                await send_message(chat_id,
                    "Welcome to TANSEEQ HR Bot!\n\n"
                    "To link your account, use the link from the HR app.\n"
                    "Go to: Push Notifications > Telegram section."
                )

        elif text == "/status":
            linked = await db.telegram_links.find_one(
                {"chat_id": chat_id}, {"_id": 0}
            )
            if linked:
                await send_message(chat_id,
                    f"Your account is linked to: <b>{linked.get('employee_name', 'Unknown')}</b>\n"
                    f"You will receive attendance notifications here."
                )
            else:
                await send_message(chat_id,
                    "Your account is not linked yet.\n"
                    "Use the link from the HR app to connect."
                )

        elif text == "/help":
            await send_message(chat_id,
                "<b>TANSEEQ HR Bot Commands</b>\n\n"
                "/start - Link your account\n"
                "/status - Check link status\n"
                "/help - Show this help"
            )


async def _handle_link(db, chat_id: int, link_code: str, telegram_name: str):
    """Handle /start LINK_CODE to link employee account."""
    # Find the pending link
    pending = await db.telegram_pending_links.find_one(
        {"code": link_code, "used": False},
        {"_id": 0}
    )
    if not pending:
        await send_message(chat_id,
            "Invalid or expired link code.\n"
            "Please generate a new link from the HR app."
        )
        return

    employee_id = pending["employee_id"]
    employee_name = pending["employee_name"]

    # Check if already linked
    existing = await db.telegram_links.find_one(
        {"employee_id": employee_id}, {"_id": 0}
    )
    if existing:
        # Update chat_id
        await db.telegram_links.update_one(
            {"employee_id": employee_id},
            {"$set": {
                "chat_id": chat_id,
                "telegram_name": telegram_name,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        await db.telegram_links.insert_one({
            "employee_id": employee_id,
            "employee_name": employee_name,
            "chat_id": chat_id,
            "telegram_name": telegram_name,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    # Mark code as used
    await db.telegram_pending_links.update_one(
        {"code": link_code},
        {"$set": {"used": True, "used_at": datetime.now(timezone.utc).isoformat()}}
    )

    await send_message(chat_id,
        f"Account linked successfully!\n\n"
        f"Employee: <b>{employee_name}</b>\n"
        f"You will now receive attendance notifications here."
    )
    logger.info(f"Telegram linked: {employee_name} -> chat_id {chat_id}")


async def notify_late_telegram(db, employee_name: str, employee_id: str, late_minutes: int, date: str):
    """Send late notification via Telegram."""
    settings = await db.system_config.find_one({"type": "push_settings"}, {"_id": 0})
    if settings and not settings.get("late_notifications", True):
        return

    # Notify employee
    if not settings or settings.get("notify_employee", True):
        link = await db.telegram_links.find_one(
            {"employee_id": employee_id}, {"_id": 0}
        )
        if link:
            await send_message(link["chat_id"],
                f"<b>Late Check-in Alert</b>\n\n"
                f"You checked in <b>{late_minutes} minutes</b> late on {date}."
            )

    # Notify admins
    if not settings or settings.get("notify_admin", True):
        admins = await db.users.find(
            {"role": "super_admin", "is_active": True},
            {"_id": 0, "id": 1}
        ).to_list(20)
        for admin in admins:
            admin_link = await db.telegram_links.find_one(
                {"employee_id": admin["id"]}, {"_id": 0}
            )
            if admin_link:
                await send_message(admin_link["chat_id"],
                    f"<b>Employee Late: {employee_name}</b>\n\n"
                    f"Late by <b>{late_minutes} minutes</b> on {date}."
                )


async def notify_absence_telegram(db, employee_name: str, employee_id: str, date: str):
    """Send absence notification via Telegram."""
    settings = await db.system_config.find_one({"type": "push_settings"}, {"_id": 0})
    if settings and not settings.get("absence_notifications", True):
        return

    if not settings or settings.get("notify_employee", True):
        link = await db.telegram_links.find_one(
            {"employee_id": employee_id}, {"_id": 0}
        )
        if link:
            await send_message(link["chat_id"],
                f"<b>Absence Recorded</b>\n\n"
                f"You were marked absent on {date}."
            )

    if not settings or settings.get("notify_admin", True):
        admins = await db.users.find(
            {"role": "super_admin", "is_active": True},
            {"_id": 0, "id": 1}
        ).to_list(20)
        for admin in admins:
            admin_link = await db.telegram_links.find_one(
                {"employee_id": admin["id"]}, {"_id": 0}
            )
            if admin_link:
                await send_message(admin_link["chat_id"],
                    f"<b>Employee Absent: {employee_name}</b>\n\n"
                    f"Absent on {date}."
                )
