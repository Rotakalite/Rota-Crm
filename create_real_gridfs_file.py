import asyncio
import os
import sys
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from services.mongo_gridfs import mongo_gridfs
import uuid
from datetime import datetime

async def create_real_gridfs_file():
    try:
        print("🚀 Creating REAL GridFS file for testing...")
        
        # Test file content
        content = """GERÇEK GRIDFS BELGESİ!

Bu artık DEMO CONTENT değil!
MongoDB GridFS'den gerçek dosya içeriği!

Bu dosyayı görüyorsan GridFS entegrasyonu ÇALIŞIYOR! 🎉

Tarih: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """

Turkish characters test: İĞÜŞÖÇ ığüşöç

END OF REAL DOCUMENT"""

        file_content = content.encode('utf-8')
        
        # Check GridFS service
        if not mongo_gridfs or not mongo_gridfs.fs:
            print("❌ GridFS service not available")
            return None
            
        print("✅ GridFS service available")
        
        # Upload to GridFS
        upload_result = await mongo_gridfs.upload_file(
            file_content=file_content,
            filename="Real_Test_Document.txt",
            user_id="test-user",
            content_type="text/plain",
            metadata={"test_file": True, "purpose": "gridfs_integration_test"}
        )
        
        print(f"✅ File uploaded to GridFS: {upload_result}")
        gridfs_file_id = upload_result["file_id"]
        
        # Create matching document record
        mongo_url = os.getenv("MONGO_URL")
        if not mongo_url:
            print("❌ No MONGO_URL")
            return None
            
        client = AsyncIOMotorClient(mongo_url)
        db = client.get_database("rota_crm_db")
        
        document_id = "real-gridfs-test"
        document_record = {
            "id": document_id,
            "original_filename": "Real_Test_Document.txt",
            "file_id": gridfs_file_id,  # CRITICAL: Use GridFS _id
            "gridfs_upload": True,
            "content_type": "text/plain",
            "file_size": len(file_content),
            "client_id": "test-client",
            "user_id": "test-user",
            "created_at": datetime.utcnow().isoformat(),
            "folder_path": "test",
            "level_1_folder": "Test Folder"
        }
        
        # Insert document record
        await db.documents.replace_one(
            {"id": document_id},
            document_record,
            upsert=True
        )
        
        print(f"✅ Document record created: {document_id}")
        
        # Verify by downloading
        print("🔄 Verifying download...")
        downloaded_content, metadata = await mongo_gridfs.download_file(gridfs_file_id)
        print(f"✅ Download successful: {len(downloaded_content)} bytes")
        print(f"   Content preview: {downloaded_content[:100].decode('utf-8', errors='ignore')}")
        
        print(f"\n🎯 SUCCESS! Test document ready:")
        print(f"   Document ID: {document_id}")
        print(f"   GridFS File ID: {gridfs_file_id}")
        print(f"   View URL: /api/documents/view/{document_id}")
        
        return document_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

# Run
if __name__ == "__main__":
    doc_id = asyncio.run(create_real_gridfs_file())
    print(f"\nFINAL RESULT: {doc_id}")
