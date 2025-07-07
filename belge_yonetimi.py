#!/usr/bin/env python3
"""
🚀 YENİ BELGE YÖNETİMİ SİSTEMİ - SIFIRDAN TASARIM
- Basit, güvenilir, hata payı sıfır
- Kalıcı storage
- Orijinal format korunması
- Klasör entegrasyonu
"""

import os
import uuid
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pymongo
from pymongo import MongoClient
import asyncio
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Rota CRM - Belge Yönetimi")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["rotacrm"]

# KALICI STORAGE DIRECTORY
DOCUMENTS_DIR = "/app/documents"
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

def create_client_folder_structure(client_id: str):
    """Create folder structure for a client"""
    client_doc_dir = os.path.join(DOCUMENTS_DIR, client_id)
    os.makedirs(client_doc_dir, exist_ok=True)
    return client_doc_dir

def get_safe_filename(filename: str) -> str:
    """Get safe filename for storage"""
    # Remove dangerous characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    safe_filename = "".join(c if c in safe_chars else "_" for c in filename)
    return safe_filename[:100]  # Limit length

@app.post("/api/belge/upload")
async def upload_document(
    file: UploadFile = File(...),
    client_id: str = Form(...),
    folder_id: str = Form(...),
    document_name: str = Form(...),
    document_type: str = Form(...),
    stage: str = Form(...),
    description: str = Form(default="")
):
    """
    🚀 YENİ BELGE YÜKLEME - HATA PAYI SIFIR
    """
    try:
        logger.info(f"📤 BELGE UPLOAD: {file.filename} -> Client: {client_id}")
        
        # 1. VALIDATE CLIENT
        client = db.clients.find_one({"id": client_id})
        if not client:
            raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
        logger.info(f"✅ Client validated: {client.get('name')}")
        
        # 2. VALIDATE FOLDER
        folder = db.folders.find_one({"id": folder_id})
        if not folder:
            raise HTTPException(status_code=404, detail="Klasör bulunamadı")
        logger.info(f"✅ Folder validated: {folder.get('name')}")
        
        # 3. CREATE STORAGE STRUCTURE
        client_dir = create_client_folder_structure(client_id)
        folder_dir = os.path.join(client_dir, folder_id)
        os.makedirs(folder_dir, exist_ok=True)
        logger.info(f"✅ Storage structure created: {folder_dir}")
        
        # 4. GENERATE UNIQUE DOCUMENT ID AND FILENAME
        document_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
        safe_filename = get_safe_filename(file.filename or "document")
        unique_filename = f"{document_id}_{safe_filename}"
        file_path = os.path.join(folder_dir, unique_filename)
        
        logger.info(f"🆔 Document ID: {document_id}")
        logger.info(f"💾 File path: {file_path}")
        
        # 5. SAVE FILE TO DISK (PERSISTENT)
        file_content = await file.read()
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Verify file was written
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Dosya kaydedilemedi")
        
        actual_size = os.path.getsize(file_path)
        logger.info(f"✅ File saved: {actual_size} bytes")
        
        # 6. CREATE DOCUMENT RECORD IN MONGODB
        document_data = {
            "id": document_id,
            "client_id": client_id,
            "folder_id": folder_id,
            "name": document_name,
            "document_name": document_name,
            "document_type": document_type,
            "stage": stage,
            "description": description,
            "original_filename": file.filename,
            "stored_filename": unique_filename,
            "file_path": file_path,
            "content_type": file.content_type,
            "file_size": actual_size,
            "uploaded_by": "user",  # TODO: Add auth
            "created_at": datetime.utcnow(),
            "folder_path": folder.get("folder_path", ""),
            "folder_level": folder.get("level", 0),
            "status": "active"
        }
        
        result = db.documents.insert_one(document_data)
        logger.info(f"✅ MongoDB record created: {result.inserted_id}")
        
        # 7. VERIFY EVERYTHING
        verification = db.documents.find_one({"id": document_id})
        if not verification:
            raise HTTPException(status_code=500, detail="Veritabanı kaydı doğrulanamadı")
        
        logger.info(f"🎉 UPLOAD SUCCESS: {document_id}")
        
        return {
            "success": True,
            "message": "Belge başarıyla yüklendi",
            "document_id": document_id,
            "filename": file.filename,
            "size": actual_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ UPLOAD ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload hatası: {str(e)}")

@app.get("/api/belge/download/{document_id}")
async def download_document(document_id: str):
    """
    🚀 YENİ BELGE İNDİRME - ORİJİNAL FORMAT
    """
    try:
        logger.info(f"📥 BELGE DOWNLOAD: {document_id}")
        
        # 1. FIND DOCUMENT IN MONGODB
        document = db.documents.find_one({"id": document_id, "status": "active"})
        if not document:
            raise HTTPException(status_code=404, detail="Belge bulunamadı")
        
        logger.info(f"✅ Document found: {document.get('name')}")
        
        # 2. CHECK FILE EXISTS ON DISK
        file_path = document.get("file_path")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        logger.info(f"✅ File exists: {file_path}")
        
        # 3. VERIFY FILE INTEGRITY
        actual_size = os.path.getsize(file_path)
        expected_size = document.get("file_size", 0)
        
        if actual_size != expected_size:
            logger.warning(f"⚠️ Size mismatch: {actual_size} vs {expected_size}")
        
        # 4. RETURN FILE WITH ORIGINAL NAME
        original_filename = document.get("original_filename", "document.pdf")
        content_type = document.get("content_type", "application/octet-stream")
        
        logger.info(f"🎉 DOWNLOAD SUCCESS: {original_filename}")
        
        return FileResponse(
            path=file_path,
            filename=original_filename,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{original_filename}",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ DOWNLOAD ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download hatası: {str(e)}")

@app.get("/api/belge/list")
async def list_documents(client_id: Optional[str] = None):
    """
    📋 BELGE LİSTESİ
    """
    try:
        query = {"status": "active"}
        if client_id:
            query["client_id"] = client_id
        
        documents = list(db.documents.find(query).sort([("created_at", -1)]))
        
        # Format for frontend
        formatted_docs = []
        for doc in documents:
            formatted_docs.append({
                "id": doc.get("id"),
                "name": doc.get("name"),
                "document_name": doc.get("document_name"),
                "document_type": doc.get("document_type"),
                "stage": doc.get("stage"),
                "original_filename": doc.get("original_filename"),
                "file_size": doc.get("file_size"),
                "created_at": doc.get("created_at"),
                "client_id": doc.get("client_id"),
                "folder_id": doc.get("folder_id"),
                "folder_path": doc.get("folder_path")
            })
        
        return {"documents": formatted_docs}
        
    except Exception as e:
        logger.error(f"❌ LIST ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Liste hatası: {str(e)}")

@app.delete("/api/belge/delete/{document_id}")
async def delete_document(document_id: str):
    """
    🗑️ BELGE SİLME
    """
    try:
        # Find document
        document = db.documents.find_one({"id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Belge bulunamadı")
        
        # Mark as deleted in database
        db.documents.update_one(
            {"id": document_id},
            {"$set": {"status": "deleted", "deleted_at": datetime.utcnow()}}
        )
        
        # Optionally remove file from disk
        file_path = document.get("file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        return {"success": True, "message": "Belge silindi"}
        
    except Exception as e:
        logger.error(f"❌ DELETE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Silme hatası: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)