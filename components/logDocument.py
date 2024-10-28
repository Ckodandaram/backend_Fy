from datetime import datetime
from schemas import DocumentSchema
import os
from motor.motor_asyncio import AsyncIOMotorClient


MONGODB_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGODB_URL)
database = client["audit_logs_db"]
documents_collection = database.get_collection("documents")

# Function to log document processing in the database
async def log_document_processing(user_id: str, document_name: str, status: str, size: int, doc_type: str, pages: int, processing_duration: float) -> str:
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