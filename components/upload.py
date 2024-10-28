import os
import shutil
import json
import model as Model
from datetime import datetime
from fastapi import FastAPI, APIRouter, File, UploadFile, Request, HTTPException
from fastapi.responses import StreamingResponse
from components.getToken import get_current_user_from_cookie
from components.logDocument import log_document_processing
from components.logApi import log_api_call
from components.userStatistics import update_user_statistics
from components.logAudit import log_audit_event

app = FastAPI()

upload_dir = "uploads"
os.makedirs(upload_dir, exist_ok=True)


# Endpoint to upload a file and process it
@app.post("/upload/")
async def upload_file(request: Request, file: UploadFile = File(...), form_number: int = File(...)):
    # Print all cookies received in the request
    print(request.cookies)  # This will log all cookies
    
    # Decode user from JWT token in the cookie
    user = get_current_user_from_cookie(request)
    
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized: No valid user token found")

    try:
        file_path = os.path.join(upload_dir, file.filename)
        print(f"User details: {user}")

        # Save the file
        with open(file_path, "wb") as image:
            shutil.copyfileobj(file.file, image)

        # Get the file size in bytes
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0, os.SEEK_SET)
        
        file_path1 = file_path

        # Call the model to process the file
        start_time = datetime.utcnow()
        output = Model.myModel(file_path1, form_number)
        end_time = datetime.utcnow()

        # Calculate processing duration
        processing_duration = (end_time - start_time).total_seconds()

        # Log document processing with the duration
        document_id = await log_document_processing(
            user_id=user["id"], 
            document_name=file.filename, 
            status="processed", 
            size=file_size, 
            doc_type=file.content_type,
            pages=5,  # Example number of pages
            processing_duration=processing_duration  # Pass the duration here
        )

        # Log the API call
        await log_api_call(user["id"], None, "/upload/", "success")

        # Log the audit event
        await log_audit_event(user["id"], "document_processed_/upload/", f"Processed document {file.filename}")
        
        # Update user statistics
        await update_user_statistics(user["id"], documents_processed=1, api_calls=1)

        # Write output to JSON file
        with open('output.json', 'w') as f:
            json.dump(output, f)

        # Stream JSON file as response
        def iterfile():
            with open('output.json', 'rb') as f:
                yield from f

        # Send JSON file as response
        response = StreamingResponse(iterfile(), media_type='application/json',
                                     headers={'Content-Disposition': 'attachment;filename=output.json'})

        # Cleanup file
        os.remove(file_path1)

        return response

    except Exception as e:
        print(f"Error during file upload: {e}")
        await log_api_call(user["id"], None, "/upload/", "error")
        await log_audit_event(user["id"], "document_processing_failed", f"Failed to process document {file.filename}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")