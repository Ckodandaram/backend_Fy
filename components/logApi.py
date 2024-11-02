from datetime import datetime
from schemas import APICallSchema
from typing import Optional
import os
from motor.motor_asyncio import AsyncIOMotorClient


MONGODB_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGODB_URL)
database = client["audit_logs_db"]
api_calls_collection = database.get_collection("api_calls")


# Function to log API calls in the database
async def log_api_call(user_id: str, document_id: Optional[str], api_endpoint: str, status: str):
    api_call = APICallSchema(
        document_id=document_id,
        user_id=user_id,
        api_endpoint=api_endpoint,
        timestamp=datetime.utcnow(),
        status=status
    )
    await api_calls_collection.insert_one(api_call.dict(by_alias=True))
