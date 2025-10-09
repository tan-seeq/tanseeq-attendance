"""
نظام الرواتب المتكامل مع الخصومات والسلف - TANSEEQ HR
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid
import calendar
from uae_datetime_utils import to_iso_string_uae

# بقية التعاريف والنماذج كما هي (اختُصرت هنا للحجم)

class PayrollDB:
    """مساعد قاعدة البيانات للرواتب"""
    @staticmethod
    def prepare_for_mongo(data: dict) -> dict:
        """تحضير البيانات للحفظ في MongoDB مع فرض Asia/Dubai +04:00 للحقول الزمنية"""
        prepared = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                # حفظ بتوقيت الإمارات +04:00
                prepared[key] = to_iso_string_uae(value)
            elif isinstance(value, date):
                # التاريخ فقط بدون منطقة زمنية
                prepared[key] = value.isoformat()
            elif isinstance(value, Enum):
                prepared[key] = value.value
            elif isinstance(value, BaseModel):
                prepared[key] = PayrollDB.prepare_for_mongo(value.dict())
            elif isinstance(value, list):
                out_list = []
                for item in value:
                    if isinstance(item, BaseModel):
                        out_list.append(PayrollDB.prepare_for_mongo(item.dict()))
                    else:
                        out_list.append(item)
                prepared[key] = out_list
            else:
                prepared[key] = value
        return prepared

    @staticmethod
    def parse_from_mongo(data: dict) -> dict:
        if "_id" in data:
            del data["_id"]
        # لا تعديل هنا – التحويل يتم لاحقًا إن لزم
        return data
