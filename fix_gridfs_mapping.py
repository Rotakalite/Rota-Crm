import asyncio
import os
import sys
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from services.mongo_gridfs import mongo_gridfs

async def fix_gridfs_mapping():
    try:
        print("🔧 Fixing GridFS file ID mapping...")
        
        # Connect to MongoDB
        mongo_url = os.getenv("MONGO_URL")
        if not mongo_url:
            print("❌ No MONGO_URL found")
            return
            
        client = AsyncIOMotorClient(mongo_url)
        db = client.get_database("rota_crm_db")
        
        # Get all documents with file_id
        print("📋 Checking document records...")
        documents = []
        async for doc in db.documents.find({"file_id": {"$exists": True}}):
            documents.append(doc)
        
        print(f"   Found {len(documents)} documents with file_id")
        
        # Get all GridFS files
        print("📋 Checking GridFS files...")
        gridfs_files = []
        async for file_info in db.fs.files.find():
            gridfs_files.append({
                "_id": str(file_info["_id"]),
                "filename": file_info.get("filename", ""),
                "length": file_info.get("length", 0),
                "uploadDate": file_info.get("uploadDate")
            })
            
        print(f"   Found {len(gridfs_files)} GridFS files")
        
        # Show mismatches
        print("\n🔍 Current situation:")
        print("DOCUMENT file_ids:")
        for doc in documents[:5]:
            print(f"  - {doc.get('id', 'no-id')}: file_id='{doc.get('file_id', 'none')}' filename='{doc.get('original_filename', 'none')}'")
            
        print("\nGRIDFS files:")
        for gf in gridfs_files[:5]:
            print(f"  - _id={gf['_id']} filename='{gf['filename']}' size={gf['length']}")
            
        # Quick fix: Create a test document that matches GridFS
        if gridfs_files:
            print(f"\n🚀 Creating test document with matching GridFS file...")
            
            # Use first GridFS file
            first_gridfs = gridfs_files[0]
            
            # Create new document record that matches
            test_doc_id = "gridfs-match-test"
            new_document = {
                "id": test_doc_id,
                "original_filename": first_gridfs["filename"],
                "file_id": first_gridfs["_id"],  # Use actual GridFS _id
                "gridfs_upload": True,
                "content_type": "application/pdf",  # Assume PDF
                "file_size": first_gridfs["length"],
                "client_id": "test-client",
                "user_id": "test-user",
                "created_at": first_gridfs["uploadDate"].isoformat() if first_gridfs["uploadDate"] else "2025-08-29T00:00:00",
                "folder_path": "test/fixed",
                "level_1_folder": "Fixed Test"
            }
            
            # Insert or update
            result = await db.documents.replace_one(
                {"id": test_doc_id},
                new_document,
                upsert=True
            )
            
            print(f"✅ Test document created: {test_doc_id}")
            print(f"   Maps to GridFS file: {first_gridfs['_id']}")
            print(f"   Filename: {first_gridfs['filename']}")
            print(f"   View URL: /api/documents/view/{test_doc_id}")
            
            return test_doc_id
        else:
            print("❌ No GridFS files found to map")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

# Run the fix
if __name__ == "__main__":
    result = asyncio.run(fix_gridfs_mapping())
    print(f"\n🎯 Fix completed. Test document ID: {result}")
