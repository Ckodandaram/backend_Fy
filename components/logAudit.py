from datetime import datetime
from schemas import AuditLogSchema
from typing import Optional
import os
from motor.motor_asyncio import AsyncIOMotorClient


MONGODB_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGODB_URL)
database = client["audit_logs_db"]
audit_logs_collection = database.get_collection("audit_logs")


async def log_audit_event(user_id: str, event_type: str, event_details: str):
    audit_log = AuditLogSchema(
        user_id=user_id,
        event_type=event_type,
        event_details=event_details,
        timestamp=datetime.utcnow()
    )
    await audit_logs_collection.insert_one(audit_log.dict(by_alias=True))
 