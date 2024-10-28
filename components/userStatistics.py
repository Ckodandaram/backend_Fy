from datetime import datetime
from schemas import UserStatisticSchema
from typing import Optional
import calendar
import os
from motor.motor_asyncio import AsyncIOMotorClient


MONGODB_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGODB_URL)
database = client["audit_logs_db"]
user_statistics_collection = database.get_collection("user_statistics")

# Function to update user statistics for billing
async def update_user_statistics(user_id: str, documents_processed: int, api_calls: int):
    current_month = datetime.utcnow().strftime("%Y-%m")
    
    # Check if there is an entry for the current month
    user_stats = await user_statistics_collection.find_one({"user_id": user_id, "month": current_month})
    
    if user_stats:
        # Update existing user statistics by incrementing values
        await user_statistics_collection.update_one(
            {"user_id": user_id, "month": current_month},
            {"$inc": {"total_documents_processed": documents_processed, "total_api_calls": api_calls}}
        )
    else:
        # Calculate the last day of the current month
        now = datetime.utcnow()
        last_day_of_month = calendar.monthrange(now.year, now.month)[1]
        billing_period_end = datetime(now.year, now.month, last_day_of_month, 23, 59, 59)
        
        # Insert new user statistics for the new month
        user_stat = UserStatisticSchema(
            user_id=user_id,
            month=current_month,
            billing_period_start=now,
            billing_period_end=billing_period_end,
            total_documents_processed=documents_processed,
            total_api_calls=api_calls
        )
        await user_statistics_collection.insert_one(user_stat.dict(by_alias=True))