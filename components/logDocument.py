from datetime import datetime
from schemas import DocumentSchema
from bson import ObjectId
import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient


MONGODB_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGODB_URL)
database = client["audit_logs_db"]
documents_collection = database.get_collection("documents")

# Function to log document processing in the database
async def log_document_processing(user_id: str, document_name: str, size: int, doc_type: str, pages: int, processing_duration: float, status: Optional[str] = None) -> str:
    document = DocumentSchema(
        user_id=user_id,
        document_name=document_name,
        processing_timestamp=datetime.utcnow(),
        status=status,
        size=size,
        type=doc_type,
        number_of_pages=pages,
        processing_duration=processing_duration
    )
    result = await documents_collection.insert_one(document.dict(by_alias=True))
    return str(result.inserted_id)  # Return the document_id


async def update_document_processing(user_id: str, doc_id: str, status: str, processing_duration: float):
    doc = await documents_collection.find_one({"_id": ObjectId(doc_id), "user_id": user_id})
    if not doc:
        raise ValueError("Document not found")
    new_processing_duration = doc["processing_duration"] + processing_duration
    # Check if the current status is 'processed' and the given status is 'error'
    # or if the current status is 'error' and the given status is 'processed'
    if (doc["status"] == "processed" and status == "failed") or (doc["status"] == "failed" and status == "processed"):
        status = "partially_processed"
    await documents_collection.update_one(
        {"_id": ObjectId(doc_id), "user_id": user_id},
        {"$set": {"status": status, "processing_duration": new_processing_duration}}
    )