from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import time
import shutil
import os
import model as Model
import json
import jwt  # JWT for decoding token
import csv
import PyPDF2
from reportlab.pdfgen import canvas
from fastapi.responses import FileResponse
from typing import Optional
from dotenv import load_dotenv
from schemas import DocumentSchema, APICallSchema, UserStatisticSchema, AuditLogSchema
from motor.motor_asyncio import AsyncIOMotorClient
from components.getToken import get_current_user_from_cookie
from components.logDocument import log_document_processing
from components.logApi import log_api_call
from components.userStatistics import update_user_statistics
from components.logAudit import log_audit_event
from components.upload import upload_file
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet 
from reportlab.lib.units import inch


# Load environment variables from .env file
load_dotenv()

app = FastAPI()

upload_dir = "uploads"
os.makedirs(upload_dir, exist_ok=True)

# CORS setup to allow frontend from localhost:3000 to interact with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Your frontend origin
    allow_credentials=True,  # Required to include cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to log requests and responses
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log the request
    print(f"Request: {request.method} {request.url}")

    # Process the request
    response = await call_next(request)

    # Log the response
    print(f"Response: {response.status_code}")

    return response

# Get the secret key and mongodb url from the .env file
SECRET_KEY = os.getenv("SECRET_KEY")
MONGODB_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGODB_URL)
database = client["audit_logs_db"]

documents_collection = database.get_collection("documents")
api_calls_collection = database.get_collection("api_calls")
user_statistics_collection = database.get_collection("user_statistics")
audit_logs_collection = database.get_collection("audit_logs")

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
        
        # Get the number of pages in the PDF
        reader = PyPDF2.PdfReader(file.file)
        num_pages = len(reader.pages)
        
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
            pages=num_pages,  # Example number of pages
            processing_duration=processing_duration  # Pass the duration here
        )

        # Log the API call
        await log_api_call(user["id"], None, "/upload/", "success")

        # Log the audit event
        await log_audit_event(user["id"], "document_processed", f"{file.filename}")
        await log_audit_event(user["id"], "API_call_made", "/upload/")
        
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

# Endpoint to extract signature from a document
@app.post("/get_signature/")
async def get_signature(request: Request, file: UploadFile = File(...), form_number: int = File(...)):
    user = get_current_user_from_cookie(request)

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized: No valid user token found")

    try:
        # Save the file
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as image:
            shutil.copyfileobj(file.file, image)

        # Get the file size in bytes
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0, os.SEEK_SET)
        
        # Get the number of pages in the PDF
        reader = PyPDF2.PdfReader(file.file)
        num_pages = len(reader.pages)
        
        start_time = time.time()
        # Analyze the document for signature
        coordinates = Model.analyze_document(file_path, form_number)
        end_time = time.time()

        # Modify the PDF with the extracted signature
        modified_pdf_path = Model.modify_pdf_with_signature(file_path, coordinates)

        # Return the modified PDF
        response = FileResponse(modified_pdf_path, filename="output.pdf", media_type="application/pdf")

        # Log document processing
        processing_duration = end_time - start_time
        await log_document_processing(
            user_id=user["id"], 
            document_name=file.filename, 
            status="processed", 
            size=file_size, 
            doc_type="pdf",
            pages=num_pages,  # Example number of pages
            processing_duration=processing_duration  # Pass the duration here
        )

        # Log the API call
        await log_api_call(user["id"], None, "/get_signature/", "success")
        
        
        # Log the audit event
        await log_audit_event(user["id"], "API_call_made", "/get_signature/")

        # Update user statistics
        # await update_user_statistics(user["id"], documents_processed=1, api_calls=1)
        # as the no.of documents processed will not change as we are processing the same document in upload 
        # and get_signature(this is a optional call)
        await update_user_statistics(user["id"], documents_processed=0, api_calls=1)

        # Clean up
        os.remove(file_path)

        return response

    except Exception as e:
        print(f"Error during signature extraction: {e}")
        await log_api_call(user["id"], None, "/get_signature/", "error")
        await log_audit_event(user["id"], "document_processing_failed", f"Failed to process document {file.filename}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/billing/")
async def get_billing(request: Request):
    user = get_current_user_from_cookie(request)

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized: No valid user token found")

    user_id = user["id"]
    user_stats = await user_statistics_collection.find_one({"user_id": user_id})
    if not user_stats:
        raise HTTPException(status_code=404, detail="User statistics not found")

    documents = await documents_collection.find({"user_id": user_id}).to_list(length=100)
    api_calls = await api_calls_collection.find({"user_id": user_id}).to_list(length=100)

    document_rate_per_kb = 0.02
    api_rate = 0.05

    total_document_cost = 0
    document_summary = []
    for doc in documents:
        doc_size_in_kb = doc["size"] / 1024
        doc_charge = doc_size_in_kb * document_rate_per_kb
        document_summary.append({
            "document_id": str(doc["_id"]),
            "document_name": doc["document_name"],
            "type": doc["type"],
            "size": doc["size"],
            "number_of_pages": doc.get("number_of_pages", None),
            "processing_timestamp": doc["processing_timestamp"],
            "charges": doc_charge
        })
        total_document_cost += doc_charge

    total_api_cost = 0
    api_call_summary = []
    for api_call in api_calls:
        api_call_charge = api_rate
        api_call_summary.append({
            "api_request_id": str(api_call["_id"]),
            "timestamp": api_call["timestamp"],
            "api_endpoint": api_call["api_endpoint"],
            "status": api_call["status"],
            "charges": api_call_charge
        })
        total_api_cost += api_call_charge

    total_cost = total_document_cost + total_api_cost

    return {
        "total_documents_processed": user_stats["total_documents_processed"],
        "total_api_calls": user_stats["total_api_calls"],
        "billing_period_start": user_stats["billing_period_start"],
        "billing_period_end": user_stats["billing_period_end"],
        "total_charges": total_cost,
        "documents": document_summary,
        "api_calls": api_call_summary
    }


# Route to generate PDF
@app.get("/billing/pdf/")
async def generate_billing_pdf(request: Request):
    # Fetch billing data
    billing_data = await get_billing(request)
    user_data = get_current_user_from_cookie(request)  # Assumed you have a function to get user data
    pdf_file = "billing_invoice.pdf"

    # Create a PDF document with A4 page size
    pdf = SimpleDocTemplate(pdf_file, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Add company logo (ensure .svg path is correct)
    logo_path = "aeroqube-logo.webp"
    logo = Image(logo_path, 6 * inch, 1.5 * inch)
    logo.hAlign = 'CENTER'
    elements.append(logo)

    # Add a formal title for the billing statement
    title = Paragraph(f"<b><font size=18 color='#2E86C1'>Monthly Billing Statement</font></b>", styles['Title'])
    elements.append(title)

    # User Information Section
    user_info = f"""
    <br/><br/>
    <b>User: {user_data['email']}</b><br/>
    Billing Date: <b>{datetime.now().strftime("%Y-%m-%d")}</b><br/>
    Billing Period: <b>{billing_data['billing_period_start']} - {billing_data['billing_period_end']}</b><br/>
    Total Documents Processed: <b>{billing_data['total_documents_processed']}</b><br/>
    Total API Calls: <b>{billing_data['total_api_calls']}</b><br/>
    Total Charges: <b>Rs. {billing_data['total_charges']:.2f}</b><br/><br/>
    """
    elements.append(Paragraph(user_info, styles['Normal']))

    # Document Summary Table
    elements.append(Paragraph("<b>Document Summary:</b>", styles['Heading2']))

    doc_table_data = [["Document Name", "Size (KB)", "Pages", "Date Processed", "Charges (Rs.)"]]

    for i, doc in enumerate(billing_data['documents']):
        row_background = colors.whitesmoke if i % 2 == 0 else colors.lightgrey  # Alternate row colors
        doc_table_data.append([doc['document_name'], f"{doc['size'] / 1024:.2f}", doc['number_of_pages'], doc['processing_timestamp'], f"Rs. {doc['charges']:.2f}"])

    doc_table = Table(doc_table_data)
    doc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),  # Remove this line
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
    ]))

    # Apply alternating background colors for rows after the header
    for i in range(1, len(doc_table_data)):
        bg_color = colors.whitesmoke if i % 2 == 0 else colors.lightgrey
        doc_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), bg_color)]))

    elements.append(doc_table)


    # API Call Summary Table
    elements.append(Paragraph("<b>API Call Summary:</b>", styles['Heading2']))
    api_table_data = [["API Endpoint", "Date", "Charges (Rs.)"]]

    for i, api in enumerate(billing_data['api_calls']):
        row_background = colors.whitesmoke if i % 2 == 0 else colors.lightgrey  # Alternate row colors
        api_table_data.append([api['api_endpoint'], api['timestamp'], f"Rs. {api['charges']}"])

    api_table = Table(api_table_data)
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
    ]))

    # Apply alternating background colors for rows after the header
    for i in range(1, len(api_table_data)):
        bg_color = colors.whitesmoke if i % 2 == 0 else colors.lightgrey
        api_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), bg_color)]))

    elements.append(api_table)


    # Billing Summary Section
    elements.append(Paragraph("<b>Billing Summary:</b>", styles['Heading2']))
    summary = f"""
    <br/>
    <b>Total Documents Processed:</b> {billing_data['total_documents_processed']}<br/>
    <b>Total API Calls:</b> {billing_data['total_api_calls']}<br/>
    <b>Total Charges:</b> Rs. {(billing_data['total_charges']):.2f}<br/><br/>
    """
    elements.append(Paragraph(summary, styles['Normal']))

    # Build the PDF document
    pdf.build(elements)

    # Return the PDF file as a response
    return FileResponse(pdf_file, media_type="application/pdf", filename="billing_invoice.pdf")


# Route to generate CSV
@app.get("/billing/csv/")
async def generate_billing_csv(request: Request):
    user = get_current_user_from_cookie(request)  # Assumed you have a function to get user data
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized: No valid user token found")

    billing_data = {
        "api_calls": [
            {"api_endpoint": "/upload/", "timestamp": "2023-10-01T12:00:00Z", "status": "success", "charges": 10},
            {"api_endpoint": "/get_signature/", "timestamp": "2023-10-02T12:00:00Z", "status": "success", "charges": 15},
        ]
    }

    csv_file = "billing_report.csv"
    with open(csv_file, mode="w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([])
        writer.writerow(["API Endpoint", "Date", "Time", "Status", "Charges (Rs.)"])
        for api in billing_data['api_calls']:
            writer.writerow([api['api_endpoint'], api['timestamp'], api['status'], api['charges']])

    return FileResponse(csv_file, media_type="text/csv", filename="billing_report.csv")