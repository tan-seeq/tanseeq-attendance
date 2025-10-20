"""
UAE DateTime Utilities
======================
توفير وظائف للتعامل مع التواريخ والأوقات بتوقيت دولة الإمارات العربية المتحدة

UAE Timezone: Asia/Dubai (UTC+4)
التقويم: ميلادي فقط (Gregorian Calendar Only)
"""

from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

# UAE Timezone
UAE_TZ = ZoneInfo("Asia/Dubai")  # UTC+4


def get_uae_now() -> datetime:
    """
    الحصول على التاريخ والوقت الحالي بتوقيت الإمارات
    Get current datetime in UAE timezone
    
    Returns:
        datetime: Current datetime in UAE timezone (Asia/Dubai - UTC+4)
    """
    return datetime.now(UAE_TZ)


def get_uae_today() -> date:
    """
    الحصول على تاريخ اليوم بتوقيت الإمارات
    Get today's date in UAE timezone
    
    Returns:
        date: Today's date in UAE
    """
    return get_uae_now().date()


def get_uae_time() -> time:
    """
    الحصول على الوقت الحالي بتوقيت الإمارات
    Get current time in UAE timezone
    
    Returns:
        time: Current time in UAE
    """
    return get_uae_now().time()


def convert_to_uae_time(dt: datetime) -> datetime:
    """
    تحويل datetime إلى توقيت الإمارات
    Convert datetime to UAE timezone
    
    Args:
        dt: datetime object (can be naive or aware)
        
    Returns:
        datetime: datetime in UAE timezone
    """
    if dt.tzinfo is None:
        # If naive, assume UTC and convert
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(UAE_TZ)


def format_uae_datetime(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    تنسيق datetime بتوقيت الإمارات
    Format datetime in UAE timezone
    
    Args:
        dt: datetime object (if None, uses current UAE time)
        format_str: strftime format string
        
    Returns:
        str: Formatted datetime string
    """
    if dt is None:
        dt = get_uae_now()
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(UAE_TZ)
    else:
        dt = dt.astimezone(UAE_TZ)
    
    return dt.strftime(format_str)


def format_uae_date(d: Optional[date] = None, format_str: str = "%Y-%m-%d") -> str:
    """
    تنسيق التاريخ بالصيغة الميلادية
    Format date in Gregorian format
    
    Args:
        d: date object (if None, uses today's UAE date)
        format_str: strftime format string
        
    Returns:
        str: Formatted date string (Gregorian)
    """
    if d is None:
        d = get_uae_today()
    return d.strftime(format_str)


def parse_uae_datetime(datetime_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    تحويل string إلى datetime بتوقيت الإمارات
    Parse string to datetime in UAE timezone
    
    Args:
        datetime_str: datetime string
        format_str: strptime format string
        
    Returns:
        datetime: datetime object in UAE timezone
    """
    dt = datetime.strptime(datetime_str, format_str)
    return dt.replace(tzinfo=UAE_TZ)


def get_month_start_end_uae(year: int, month: int) -> tuple[datetime, datetime]:
    """
    الحصول على بداية ونهاية الشهر بتوقيت الإمارات
    Get start and end of month in UAE timezone
    
    Args:
        year: Year (e.g., 2025)
        month: Month (1-12)
        
    Returns:
        tuple: (start_of_month, end_of_month) in UAE timezone
    """
    start = datetime(year, month, 1, 0, 0, 0, tzinfo=UAE_TZ)
    
    # Get last day of month
    if month == 12:
        end = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=UAE_TZ) - timedelta(microseconds=1)
    else:
        end = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=UAE_TZ) - timedelta(microseconds=1)
    
    return start, end


def is_weekend_uae(d: date) -> bool:
    """
    التحقق من أن التاريخ هو عطلة نهاية أسبوع في الإمارات
    Check if date is weekend in UAE (Saturday & Sunday)
    
    Args:
        d: date object
        
    Returns:
        bool: True if weekend (Saturday or Sunday)
    """
    # UAE weekend: Saturday (5) and Sunday (6)
    return d.weekday() in [5, 6]


def get_working_days_uae(start_date: date, end_date: date) -> int:
    """
    حساب عدد أيام العمل بين تاريخين (باستثناء عطل نهاية الأسبوع)
    Calculate working days between two dates (excluding weekends)
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        int: Number of working days
    """
    working_days = 0
    current_date = start_date
    
    while current_date <= end_date:
        if not is_weekend_uae(current_date):
            working_days += 1
        current_date += timedelta(days=1)
    
    return working_days


def to_iso_string_uae(dt: Optional[datetime] = None) -> str:
    """
    تحويل datetime إلى ISO string بتوقيت الإمارات
    Convert datetime to ISO string in UAE timezone
    
    Args:
        dt: datetime object (if None, uses current UAE time)
        
    Returns:
        str: ISO format string (e.g., "2025-10-08T15:30:00+04:00")
    """
    if dt is None:
        dt = get_uae_now()
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=UAE_TZ)
    else:
        dt = dt.astimezone(UAE_TZ)
    
    return dt.isoformat()


def normalize_datetime_fields(data: dict, fields: list = None) -> dict:
    """
    ✅ NEW: Normalize datetime fields to UAE timezone ISO format
    Ensures consistent +04:00 timezone in all datetime fields
    
    Args:
        data: Dictionary containing datetime fields
        fields: List of field names to normalize (if None, auto-detect)
        
    Returns:
        dict: Data with normalized datetime fields
    """
    if fields is None:
        # Auto-detect common datetime field names
        fields = [
            'created_at', 'updated_at', 'timestamp', 'sent_at',
            'locked_at', 'unlocked_at', 'approved_at', 'rejected_at',
            'start_date', 'end_date', 'date', 'processed_at',
            'completed_at', 'modified_at', 'deleted_at'
        ]
    
    for field in fields:
        if field in data and data[field] is not None:
            value = data[field]
            
            # Handle datetime objects
            if isinstance(value, datetime):
                data[field] = to_iso_string_uae(value)
            
            # Handle string datetimes without timezone
            elif isinstance(value, str) and 'T' in value and '+' not in value and 'Z' not in value:
                try:
                    dt = datetime.fromisoformat(value)
                    data[field] = to_iso_string_uae(dt)
                except:
                    pass  # Keep original if parsing fails
    
    return data


# Convenience functions for common formats
def get_uae_date_str() -> str:
    """Get current date as string (YYYY-MM-DD)"""
    return format_uae_date()


def get_uae_datetime_str() -> str:
    """Get current datetime as string (YYYY-MM-DD HH:MM:SS)"""
    return format_uae_datetime()


def get_uae_month_str() -> str:
    """Get current month as string (YYYY-MM)"""
    return format_uae_date(format_str="%Y-%m")


def format_uae_date_dmy(d: Optional[date] = None) -> str:
    """
    تنسيق التاريخ بصيغة dd/MM/yyyy (Gregorian)
    Format date as dd/MM/yyyy (Gregorian calendar only)
    
    Args:
        d: date object (if None, uses today's UAE date)
        
    Returns:
        str: Date formatted as dd/MM/yyyy (e.g., "09/10/2025")
    
    Example:
        >>> format_uae_date_dmy(date(2025, 10, 9))
        '09/10/2025'
    """
    if d is None:
        d = get_uae_today()
    return d.strftime("%d/%m/%Y")


def format_uae_datetime_dmy(dt: Optional[datetime] = None) -> str:
    """
    تنسيق التاريخ والوقت بصيغة dd/MM/yyyy HH:mm (Asia/Dubai)
    Format datetime as dd/MM/yyyy HH:mm (UAE timezone)
    
    Args:
        dt: datetime object (if None, uses current UAE time)
        
    Returns:
        str: Datetime formatted as dd/MM/yyyy HH:mm (e.g., "09/10/2025 14:30")
    
    Example:
        >>> format_uae_datetime_dmy(datetime(2025, 10, 9, 14, 30, 0, tzinfo=UAE_TZ))
        '09/10/2025 14:30'
    """
    if dt is None:
        dt = get_uae_now()
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(UAE_TZ)
    else:
        dt = dt.astimezone(UAE_TZ)
    
    return dt.strftime("%d/%m/%Y %H:%M")


# Example usage and tests
if __name__ == "__main__":
    print("🇦🇪 UAE DateTime Utilities Test")
    print("=" * 50)
    
    # Test all functions
    now = get_uae_now()
    today = get_uae_today()
    iso_str = to_iso_string_uae()
    date_str = get_uae_date_str()
    month_str = get_uae_month_str()
    
    print(f"Current UAE time: {now}")
    print(f"Current UAE date: {today}")
    print(f"ISO string: {iso_str}")
    print(f"Date string: {date_str}")
    
    # Test weekend check
    print(f"\nIs today ({today}) a weekend? {is_weekend_uae(today)}")
    
    # Test month boundaries
    start, end = get_month_start_end_uae(2025, 10)
    print(f"\nOctober 2025:")
    print(f"  Start: {start}")
    print(f"  End: {end}")
    
    # Test working days
    working_days = get_working_days_uae(date(2025, 10, 1), date(2025, 10, 31))
    print(f"Working days in {month_str}: {working_days}")
    
    # Test new formatting functions
    print("\n📅 Testing new dd/MM/yyyy formatters:")
    test_date = date(2025, 10, 9)
    test_datetime = datetime(2025, 10, 9, 14, 30, 0, tzinfo=UAE_TZ)
    
    formatted_date = format_uae_date_dmy(test_date)
    formatted_datetime = format_uae_datetime_dmy(test_datetime)
    
    print(f"  format_uae_date_dmy({test_date}) = '{formatted_date}'")
    print(f"  format_uae_datetime_dmy({test_datetime}) = '{formatted_datetime}'")
    print(f"  format_uae_date_dmy() (today) = '{format_uae_date_dmy()}'")
    print(f"  format_uae_datetime_dmy() (now) = '{format_uae_datetime_dmy()}'")
    
    print("\n✅ All tests completed!")
