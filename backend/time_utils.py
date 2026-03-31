"""
Robust time parsing utilities for handling various check_in/check_out formats
from the production MongoDB database.

Supported formats:
- "09:00:00" (time-only HH:MM:SS)
- "09:00" (time-only HH:MM)
- "2025-10-01 09:00:00" (datetime with space)
- "2025-10-01T09:00:00" (ISO format)
- "2025-10-01T09:00:00+04:00" (ISO with timezone)
"""

from datetime import datetime, time
from typing import Optional


def safe_parse_time(value) -> Optional[time]:
    """Parse any time/datetime string into a time object. Returns None on failure."""
    if value is None:
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    # ISO format with T separator: "2025-10-01T09:00:00"
    if 'T' in s:
        s = s.split('T', 1)[1]
        # Remove timezone info if present (+04:00 or Z)
        for sep in ('+', 'Z'):
            if sep in s:
                s = s.split(sep, 1)[0]
    # Space-separated datetime: "2025-10-01 09:00:00"
    elif ' ' in s:
        parts = s.split(' ', 1)
        if '-' in parts[0]:
            s = parts[1]
    # Now s should be a time-only string like "09:00:00" or "09:00"
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(s.strip()[:8], fmt).time()
        except (ValueError, IndexError):
            continue
    return None


def safe_parse_datetime(value, label="time") -> Optional[datetime]:
    """Parse any time/datetime string into a full datetime object.
    For time-only strings, uses today's date as reference."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    # ISO format: "2025-10-01T09:00:00"
    if 'T' in s:
        date_part, time_part = s.split('T', 1)
        # Remove timezone
        for sep in ('+', 'Z'):
            if sep in time_part:
                time_part = time_part.split(sep, 1)[0]
        try:
            return datetime.strptime(f"{date_part} {time_part[:8]}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.strptime(f"{date_part} {time_part[:5]}", "%Y-%m-%d %H:%M")
            except ValueError:
                return None
    # Space-separated: "2025-10-01 09:00:00"
    if ' ' in s:
        date_part, time_part = s.split(' ', 1)
        if '-' in date_part:
            try:
                return datetime.strptime(f"{date_part} {time_part[:8]}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    return datetime.strptime(f"{date_part} {time_part[:5]}", "%Y-%m-%d %H:%M")
                except ValueError:
                    return None
    # Time-only: "09:00:00" or "09:00"
    if ':' in s:
        ref_date = datetime.now().strftime("%Y-%m-%d")
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                t = datetime.strptime(s[:8], fmt).time()
                return datetime.strptime(f"{ref_date} {t.strftime('%H:%M')}", "%Y-%m-%d %H:%M")
            except (ValueError, IndexError):
                continue
    return None
