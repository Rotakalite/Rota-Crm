#!/usr/bin/env python3
"""
SIMPLE UPLOAD & DOWNLOAD SYSTEM - NO GRIDFS, JUST WORKS
"""
import os
import uuid
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import pymongo

app = FastAPI()

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
client = pymongo.MongoClient(MONGO_URL)
db = client["rotacrm"]

# Create uploads directory
os.makedirs("/app/uploads", exist_ok=True)

@app.post("/simple-upload")
async def simple_upload(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    folder_id: str = Form(...),
    document_name: str = Form(...),
    document_type: str = Form(...),
    stage: str = Form(...)
):
    """SIMPLE UPLOAD - SAVE TO DISK"""
    try:
        # Generate unique filename
        doc_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'pdf'
        saved_filename = f"{doc_id}.{file_extension}"
        file_path = f"/app/uploads/{saved_filename}"
        
        # Save file to disk
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Save document record to MongoDB
        document_data = {
            "id": doc_id,
            "client_id": client_id,
            "name": document_name,
            "document_name": document_name,
            "document_type": document_type,
            "stage": stage,
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size": len(content),
            "original_filename": file.filename,
            "created_at": datetime.utcnow(),
            "folder_id": folder_id,
            "file_path": file_path,
            "saved_filename": saved_filename
        }
        
        db.documents.insert_one(document_data)
        
        return {"message": "Upload successful", "document_id": doc_id}
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/simple-download/{doc_id}")
async def simple_download(doc_id: str):
    """SIMPLE DOWNLOAD - FROM DISK"""
    try:
        # Find document in MongoDB
        doc = db.documents.find_one({"id": doc_id})
        if not doc:
            return {"error": "Document not found"}
        
        # Get file path
        file_path = doc.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return {"error": "File not found on disk"}
        
        # Return file
        return FileResponse(
            path=file_path,
            filename=doc.get("original_filename", "document.pdf"),
            media_type=doc.get("content_type", "application/pdf")
        )
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)