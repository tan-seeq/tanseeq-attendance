"""
Push Notification Service for TANSEEQ HR
Uses Web Push protocol with VAPID authentication
"""
import os
import json
import logging
from pywebpush import webpush, WebPushException

logger = logging.getLogger("push_service")

VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_SUBJECT = os.environ.get("VAPID_SUBJECT", "mailto:admin@tanseeq.com")


def get_vapid_claims():
    return {
        "sub": VAPID_SUBJECT,
    }


async def send_push_notification(db, user_id: str, title: str, body: str, url: str = "/attendance", tag: str = "default"):
    """Send push notification to a specific user's subscribed devices."""
    if not VAPID_PRIVATE_KEY:
        logger.warning("VAPID keys not configured, skipping push notification")
        return 0

    subscriptions = await db.push_subscriptions.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(None)

    if not subscriptions:
        return 0

    sent = 0
    failed_ids = []

    for sub in subscriptions:
        subscription_info = sub.get("subscription")
        if not subscription_info:
            continue
        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps({
                    "title": title,
                    "body": body,
                    "url": url,
                    "tag": tag,
                    "icon": "/icon-192.png",
                    "badge": "/icon-192.png",
                }),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=get_vapid_claims(),
            )
            sent += 1
        except WebPushException:
            # Any push failure = subscription is invalid, clean it up
            failed_ids.append(sub.get("id"))
        except Exception:
            failed_ids.append(sub.get("id"))

    # Clean up expired subscriptions
    if failed_ids:
        await db.push_subscriptions.delete_many({"id": {"$in": failed_ids}})

    return sent


async def send_push_to_admins(db, title: str, body: str, url: str = "/attendance-management", tag: str = "admin"):
    """Send push notification to all super admins."""
    admins = await db.users.find(
        {"role": "super_admin", "is_active": True},
        {"_id": 0, "id": 1}
    ).to_list(20)

    total = 0
    for admin in admins:
        total += await send_push_notification(db, admin["id"], title, body, url, tag)
    return total


async def notify_late_checkin(db, employee_name: str, employee_id: str, late_minutes: int, date: str):
    """Send push notification for late check-in."""
    # Notify the employee
    await send_push_notification(
        db, employee_id,
        f"Late Check-in Alert",
        f"You checked in {late_minutes} minutes late on {date}.",
        "/attendance",
        f"late-{date}"
    )
    # Notify admins
    await send_push_to_admins(
        db,
        f"Employee Late: {employee_name}",
        f"{employee_name} checked in {late_minutes} min late on {date}.",
        "/attendance-management",
        f"admin-late-{employee_name}-{date}"
    )


async def notify_absence(db, employee_name: str, employee_id: str, date: str):
    """Send push notification for absence."""
    await send_push_notification(
        db, employee_id,
        f"Absence Recorded",
        f"You were marked absent on {date}.",
        "/attendance",
        f"absent-{date}"
    )
    await send_push_to_admins(
        db,
        f"Employee Absent: {employee_name}",
        f"{employee_name} was absent on {date}.",
        "/attendance-management",
        f"admin-absent-{employee_name}-{date}"
    )
