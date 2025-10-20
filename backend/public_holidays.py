"""
Public Holidays Management
===========================
إدارة الإجازات الرسمية (الأعياد الوطنية والدينية)
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from motor.motor_asyncio import AsyncIOMotorDatabase


class PublicHoliday(BaseModel):
    """Public holiday model"""
    id: str = ""
    date: str  # YYYY-MM-DD
    name: str
    name_ar: str
    country: str = "UAE"
    is_recurring: bool = False  # For annual holidays like National Day
    created_at: str = ""


# UAE Public Holidays for 2025-2026
UAE_HOLIDAYS_2025_2026 = [
    # 2025
    {"date": "2025-01-01", "name": "New Year's Day", "name_ar": "رأس السنة الميلادية", "is_recurring": True},
    {"date": "2025-04-01", "name": "Eid Al Fitr Holiday", "name_ar": "عطلة عيد الفطر", "is_recurring": False},
    {"date": "2025-04-02", "name": "Eid Al Fitr", "name_ar": "عيد الفطر", "is_recurring": False},
    {"date": "2025-04-03", "name": "Eid Al Fitr Holiday", "name_ar": "عطلة عيد الفطر", "is_recurring": False},
    {"date": "2025-06-06", "name": "Arafat Day", "name_ar": "وقفة عرفة", "is_recurring": False},
    {"date": "2025-06-07", "name": "Eid Al Adha", "name_ar": "عيد الأضحى", "is_recurring": False},
    {"date": "2025-06-08", "name": "Eid Al Adha Holiday", "name_ar": "عطلة عيد الأضحى", "is_recurring": False},
    {"date": "2025-06-09", "name": "Eid Al Adha Holiday", "name_ar": "عطلة عيد الأضحى", "is_recurring": False},
    {"date": "2025-06-27", "name": "Islamic New Year", "name_ar": "رأس السنة الهجرية", "is_recurring": False},
    {"date": "2025-09-05", "name": "Prophet's Birthday", "name_ar": "المولد النبوي", "is_recurring": False},
    {"date": "2025-12-02", "name": "UAE National Day", "name_ar": "اليوم الوطني الإماراتي", "is_recurring": True},
    {"date": "2025-12-03", "name": "UAE National Day Holiday", "name_ar": "عطلة اليوم الوطني", "is_recurring": True},
    
    # 2026
    {"date": "2026-01-01", "name": "New Year's Day", "name_ar": "رأس السنة الميلادية", "is_recurring": True},
    {"date": "2026-03-21", "name": "Eid Al Fitr Holiday", "name_ar": "عطلة عيد الفطر", "is_recurring": False},
    {"date": "2026-03-22", "name": "Eid Al Fitr", "name_ar": "عيد الفطر", "is_recurring": False},
    {"date": "2026-03-23", "name": "Eid Al Fitr Holiday", "name_ar": "عطلة عيد الفطر", "is_recurring": False},
    {"date": "2026-05-27", "name": "Arafat Day", "name_ar": "وقفة عرفة", "is_recurring": False},
    {"date": "2026-05-28", "name": "Eid Al Adha", "name_ar": "عيد الأضحى", "is_recurring": False},
    {"date": "2026-05-29", "name": "Eid Al Adha Holiday", "name_ar": "عطلة عيد الأضحى", "is_recurring": False},
    {"date": "2026-05-30", "name": "Eid Al Adha Holiday", "name_ar": "عطلة عيد الأضحى", "is_recurring": False},
    {"date": "2026-06-17", "name": "Islamic New Year", "name_ar": "رأس السنة الهجرية", "is_recurring": False},
    {"date": "2026-08-26", "name": "Prophet's Birthday", "name_ar": "المولد النبوي", "is_recurring": False},
    {"date": "2026-12-02", "name": "UAE National Day", "name_ar": "اليوم الوطني الإماراتي", "is_recurring": True},
    {"date": "2026-12-03", "name": "UAE National Day Holiday", "name_ar": "عطلة اليوم الوطني", "is_recurring": True},
]


async def seed_public_holidays(db: AsyncIOMotorDatabase):
    """
    Seed public holidays into database
    """
    collection = db.public_holidays
    
    # Check if already seeded
    existing_count = await collection.count_documents({})
    if existing_count > 0:
        print(f"⏭️ Public holidays already seeded ({existing_count} records)")
        return existing_count
    
    # Insert holidays
    holidays_to_insert = []
    for holiday_data in UAE_HOLIDAYS_2025_2026:
        holiday = PublicHoliday(
            id=str(__import__('uuid').uuid4()),
            date=holiday_data["date"],
            name=holiday_data["name"],
            name_ar=holiday_data["name_ar"],
            country="UAE",
            is_recurring=holiday_data["is_recurring"],
            created_at=datetime.now().isoformat()
        )
        holidays_to_insert.append(holiday.dict())
    
    result = await collection.insert_many(holidays_to_insert)
    
    # Create index
    await collection.create_index("date", unique=True)
    
    print(f"✅ Seeded {len(result.inserted_ids)} public holidays")
    return len(result.inserted_ids)


async def is_public_holiday(db: AsyncIOMotorDatabase, check_date: date) -> bool:
    """
    Check if a date is a public holiday
    
    Args:
        db: MongoDB database instance
        check_date: Date to check
        
    Returns:
        True if it's a public holiday, False otherwise
    """
    date_str = check_date.strftime("%Y-%m-%d")
    
    holiday = await db.public_holidays.find_one({"date": date_str})
    
    return holiday is not None


async def get_public_holidays_in_range(
    db: AsyncIOMotorDatabase,
    start_date: date,
    end_date: date
) -> List[dict]:
    """
    Get all public holidays in a date range
    
    Args:
        db: MongoDB database instance
        start_date: Start of range
        end_date: End of range
        
    Returns:
        List of holiday records
    """
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    holidays = await db.public_holidays.find({
        "date": {
            "$gte": start_str,
            "$lte": end_str
        }
    }).to_list(None)
    
    return holidays


async def is_employee_on_approved_leave(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    check_date: date
) -> bool:
    """
    Check if employee has an approved leave on this date
    
    Args:
        db: MongoDB database instance
        employee_id: Employee ID
        check_date: Date to check
        
    Returns:
        True if employee has approved leave, False otherwise
    """
    date_str = check_date.strftime("%Y-%m-%d")
    
    # Check leaves collection
    leave = await db.leaves.find_one({
        "user_id": employee_id,
        "status": "approved",
        "start_date": {"$lte": date_str},
        "end_date": {"$gte": date_str}
    })
    
    return leave is not None


async def get_employee_leaves_in_range(
    db: AsyncIOMotorDatabase,
    employee_id: str,
    start_date: date,
    end_date: date
) -> List[dict]:
    """
    Get all approved leaves for an employee in a date range
    
    Args:
        db: MongoDB database instance
        employee_id: Employee ID
        start_date: Start of range
        end_date: End of range
        
    Returns:
        List of approved leave records
    """
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    leaves = await db.leaves.find({
        "user_id": employee_id,
        "status": "approved",
        "$or": [
            # Leave starts within range
            {
                "start_date": {"$gte": start_str, "$lte": end_str}
            },
            # Leave ends within range
            {
                "end_date": {"$gte": start_str, "$lte": end_str}
            },
            # Leave spans entire range
            {
                "start_date": {"$lte": start_str},
                "end_date": {"$gte": end_str}
            }
        ]
    }).to_list(None)
    
    return leaves


def is_date_in_leave_range(check_date: date, leave_start: str, leave_end: str) -> bool:
    """
    Check if a date falls within a leave range
    
    Args:
        check_date: Date to check
        leave_start: Leave start date (YYYY-MM-DD)
        leave_end: Leave end date (YYYY-MM-DD)
        
    Returns:
        True if date is within leave range
    """
    from datetime import datetime
    
    check_dt = check_date
    start_dt = datetime.strptime(leave_start, "%Y-%m-%d").date()
    end_dt = datetime.strptime(leave_end, "%Y-%m-%d").date()
    
    return start_dt <= check_dt <= end_dt
