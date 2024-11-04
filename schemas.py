# from pydantic import BaseModel, Field
# from typing import Optional
# from datetime import datetime
# from bson import ObjectId
# from pydantic.errors import PydanticUserError

# class PyObjectId(ObjectId):
#     @classmethod
#     def __get_validators__(cls):
#         yield cls.validate

#     @classmethod
#     def validate(cls, v):
#         if not ObjectId.is_valid(v):
#             raise ValueError('Invalid objectid')
#         return ObjectId(v)

#     @classmethod
#     def __get_pydantic_json_schema__(cls, schema):
#         schema.update(type='string')

# class DocumentSchema(BaseModel):
#     id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
#     user_id: str
#     document_name: str
#     processing_timestamp: datetime
#     status: str
#     size: int
#     type: str

#     class Config:
#         populate_by_name = True
#         arbitrary_types_allowed = True
#         json_encoders = {ObjectId: str}

# class APICallSchema(BaseModel):
#     id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
#     document_id: Optional[PyObjectId]
#     user_id: str
#     api_endpoint: str
#     timestamp: datetime
#     status: str

#     class Config:
#         populate_by_name = True
#         arbitrary_types_allowed = True
#         json_encoders = {ObjectId: str}

# class UserStatisticSchema(BaseModel):
#     id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
#     user_id: str
#     billing_period_start: datetime
#     billing_period_end: datetime
#     total_documents_processed: int
#     total_api_calls: int

#     class Config:
#         populate_by_name = True
#         arbitrary_types_allowed = True
#         json_encoders = {ObjectId: str}

# class AuditLogSchema(BaseModel):
#     id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
#     user_id: str
#     event_type: str
#     event_details: str
#     timestamp: datetime

#     class Config:
#         populate_by_name = True
#         arbitrary_types_allowed = True
#         json_encoders = {ObjectId: str}






# updated schemas.py(on 23rd oct 2024)
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, field):
        schema.update(type='string')
        return schema

class DocumentSchema(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    document_name: str
    processing_timestamp: datetime
    status: Optional[str] = None
    size: int
    type: str
    number_of_pages: int
    processing_duration: float

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Schema for API Call Logging
class APICallSchema(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    document_id: Optional[PyObjectId]  # Nullable if the API call isn’t document-specific
    user_id: str  # User who made the API call
    api_endpoint: str  # Which API endpoint was called
    timestamp: datetime  # When the API call was made
    status: str  # API call success, error, etc.
    api_calls_count: int = 1  # Number of API calls in this session

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Schema for User Statistics (For Billing)
class UserStatisticSchema(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    month: str  # Add month field to store the month information
    billing_period_start: datetime
    billing_period_end: datetime
    total_documents_processed: int
    total_api_calls: int

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Schema for Audit Logs
class AuditLogSchema(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str  # Link to the user who performed the action
    event_type: str  # Type of event (e.g., Document Processed, API Call)
    event_details: str  # Event details (e.g., document name, endpoint)
    timestamp: datetime  # When the event occurred

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
