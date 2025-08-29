import asyncio
import sys
import os
from datetime import datetime
import uuid

# Add the backend directory to Python path
sys.path.append('/app/backend')

# Import GridFS service
from services.mongo_gridfs import mongo_gridfs
from motor.motor_asyncio import AsyncIOMotorClient

async def test_gridfs_upload():
    try:
        print("🚀 Testing GridFS upload...")
        
        # Create test file content
        test_content = b"""GERCEK GRIDFS TEST BELGESI!

Bu bir test belgesidir.
MongoDB GridFS'de saklanmaktadir.

Turkish characters: İĞÜŞÖÇ ığüşöç

Tarih: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode()

        # Upload to GridFS
        if mongo_gridfs and mongo_gridfs.fs:
            print("✅ GridFS service available")
            
            result = await mongo_gridfs.upload_file(
                file_content=test_content,
                filename="Türkçe_GridFS_Test_Belgesi.txt",
                user_id="test-user-123",
                content_type="text/plain",
                metadata={
                    "test_file": True,
                    "upload_method": "manual_gridfs_test"
                }
            )
            
            print(f"✅ File uploaded to GridFS: {result}")
            
            # Create document record in MongoDB
            mongo_url = os.getenv("MONGO_URL")
            if mongo_url:
                client = AsyncIOMotorClient(mongo_url)
                db = client.get_database("rota_crm_db")
                
                document_id = f"gridfs-test-{uuid.uuid4()}"
                
                document_record = {
                    "id": document_id,
                    "original_filename": "Türkçe_GridFS_Test_Belgesi.txt",
                    "file_id": result["file_id"],  # GridFS file ID
                    "gridfs_upload": True,
                    "content_type": "text/plain",
                    "file_size": len(test_content),
                    "client_id": "test-client-123",
                    "user_id": "test-user-123", 
                    "created_at": datetime.utcnow().isoformat(),
                    "folder_path": "test/gridfs",
                    "level_1_folder": "Test Folder",
                    "level_2_folder": "GridFS Test"
                }
                
                await db.documents.insert_one(document_record)
                print(f"✅ Document record created: {document_id}")
                
                # Test download
                print("🔄 Testing download...")
                file_content, metadata = await mongo_gridfs.download_file(result["file_id"])
                print(f"✅ Downloaded {len(file_content)} bytes")
                print(f"   Content preview: {file_content[:50]}...")
                
                return document_id
            else:
                print("❌ No MONGO_URL found")
                return None
        else:
            print("❌ GridFS service not available")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

# Run the test
if __name__ == "__main__":
    doc_id = asyncio.run(test_gridfs_upload())
    print(f"\n🎯 Test completed. Document ID: {doc_id}")
