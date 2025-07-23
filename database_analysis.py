#!/usr/bin/env python3
"""
🔍 DATABASE CONNECTIVITY AND DOCUMENT ANALYSIS
Testing database connection and analyzing document data for bulk download
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# MongoDB connection from environment
MONGO_URL = "mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster"
DB_NAME = "rotacrm"

async def test_database_connection():
    """Test MongoDB connection and analyze document data"""
    
    print("🔍 DATABASE CONNECTIVITY AND DOCUMENT ANALYSIS")
    print("=" * 60)
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        print("✅ MongoDB connection established")
        
        # Test 1: Check clients collection
        print("\n1️⃣ Analyzing clients collection...")
        clients = await db.clients.find({}).to_list(length=None)
        print(f"   Total clients: {len(clients)}")
        
        if clients:
            # Show client types
            registered_clients = [c for c in clients if c.get("client_type") == "registered"]
            bulk_clients = [c for c in clients if c.get("client_type") == "bulk"]
            
            print(f"   Registered clients: {len(registered_clients)}")
            print(f"   Bulk clients: {len(bulk_clients)}")
            
            # Show first few clients for testing
            print("\n   Sample clients for testing:")
            for i, client in enumerate(clients[:3]):
                client_name = client.get("hotel_name") or client.get("name", "Unknown")
                print(f"   {i+1}. ID: {client['id'][:8]}... | Name: {client_name} | Type: {client.get('client_type', 'unknown')}")
        
        # Test 2: Check documents collection
        print("\n2️⃣ Analyzing documents collection...")
        documents = await db.documents.find({}).to_list(length=None)
        print(f"   Total documents: {len(documents)}")
        
        if documents:
            # Analyze document storage types
            binary_storage_docs = [d for d in documents if d.get("binary_storage", False)]
            gridfs_docs = [d for d in documents if d.get("gridfs_id")]
            file_path_docs = [d for d in documents if d.get("file_path")]
            
            print(f"   Binary storage documents: {len(binary_storage_docs)}")
            print(f"   GridFS documents: {len(gridfs_docs)}")
            print(f"   File path documents: {len(file_path_docs)}")
            
            # Show document distribution by client
            client_doc_count = {}
            for doc in documents:
                client_id = doc.get("client_id", "unknown")
                client_doc_count[client_id] = client_doc_count.get(client_id, 0) + 1
            
            print(f"\n   Documents per client:")
            for client_id, count in sorted(client_doc_count.items(), key=lambda x: x[1], reverse=True)[:5]:
                # Find client name
                client = next((c for c in clients if c.get("id") == client_id), None)
                client_name = "Unknown"
                if client:
                    client_name = client.get("hotel_name") or client.get("name", "Unknown")
                print(f"   {client_id[:8]}... ({client_name}): {count} documents")
            
            # Show sample documents
            print(f"\n   Sample documents:")
            for i, doc in enumerate(documents[:3]):
                filename = doc.get("original_filename", doc.get("name", "Unknown"))
                storage_type = "Unknown"
                if doc.get("binary_storage"):
                    storage_type = "Binary"
                elif doc.get("gridfs_id"):
                    storage_type = "GridFS"
                elif doc.get("file_path"):
                    storage_type = "File Path"
                
                print(f"   {i+1}. ID: {doc['id'][:8]}... | File: {filename} | Storage: {storage_type}")
        
        # Test 3: Check folders collection
        print("\n3️⃣ Analyzing folders collection...")
        folders = await db.folders.find({}).to_list(length=None)
        print(f"   Total folders: {len(folders)}")
        
        if folders:
            # Analyze folder structure
            root_folders = [f for f in folders if not f.get("parent_folder_id")]
            nested_folders = [f for f in folders if f.get("parent_folder_id")]
            
            print(f"   Root folders: {len(root_folders)}")
            print(f"   Nested folders: {len(nested_folders)}")
            
            # Show folder distribution by client
            client_folder_count = {}
            for folder in folders:
                client_id = folder.get("client_id", "unknown")
                client_folder_count[client_id] = client_folder_count.get(client_id, 0) + 1
            
            print(f"\n   Folders per client:")
            for client_id, count in sorted(client_folder_count.items(), key=lambda x: x[1], reverse=True)[:5]:
                # Find client name
                client = next((c for c in clients if c.get("id") == client_id), None)
                client_name = "Unknown"
                if client:
                    client_name = client.get("hotel_name") or client.get("name", "Unknown")
                print(f"   {client_id[:8]}... ({client_name}): {count} folders")
            
            # Show sample folders
            print(f"\n   Sample folders:")
            for i, folder in enumerate(folders[:5]):
                folder_name = folder.get("name", "Unknown")
                level = folder.get("level", 0)
                print(f"   {i+1}. ID: {folder['id'][:8]}... | Name: {folder_name} | Level: {level}")
        
        # Test 4: Find clients with both documents and folders for testing
        print("\n4️⃣ Finding clients suitable for bulk download testing...")
        suitable_clients = []
        
        for client in clients[:10]:  # Check first 10 clients
            client_id = client["id"]
            client_docs = [d for d in documents if d.get("client_id") == client_id]
            client_folders = [f for f in folders if f.get("client_id") == client_id]
            
            if client_docs and client_folders:
                client_name = client.get("hotel_name") or client.get("name", "Unknown")
                suitable_clients.append({
                    "id": client_id,
                    "name": client_name,
                    "doc_count": len(client_docs),
                    "folder_count": len(client_folders),
                    "client_type": client.get("client_type", "unknown")
                })
        
        print(f"   Found {len(suitable_clients)} clients suitable for bulk download testing:")
        for i, client in enumerate(suitable_clients[:3]):
            print(f"   {i+1}. {client['name']} (ID: {client['id'][:8]}...)")
            print(f"      Documents: {client['doc_count']}, Folders: {client['folder_count']}, Type: {client['client_type']}")
        
        # Test 5: Check document file data availability
        print("\n5️⃣ Checking document file data availability...")
        docs_with_data = 0
        docs_without_data = 0
        
        for doc in documents[:20]:  # Check first 20 documents
            has_data = False
            
            if doc.get("binary_storage", False) and doc.get("file_content"):
                has_data = True
            elif doc.get("gridfs_id"):
                has_data = True
            elif doc.get("file_path"):
                has_data = True
            
            if has_data:
                docs_with_data += 1
            else:
                docs_without_data += 1
        
        print(f"   Documents with file data: {docs_with_data}")
        print(f"   Documents without file data: {docs_without_data}")
        
        if docs_with_data > 0:
            print("   ✅ Documents with file data found - bulk download should work")
        else:
            print("   ⚠️  WARNING: No documents with file data found")
        
        # Test 6: Test folder hierarchy reconstruction
        print("\n6️⃣ Testing folder hierarchy reconstruction...")
        if folders:
            # Create folder mapping
            folder_map = {f["id"]: f for f in folders}
            
            def get_folder_path(folder_id):
                """Reconstruct full folder path"""
                if not folder_id or folder_id not in folder_map:
                    return ""
                
                folder = folder_map[folder_id]
                path_parts = [folder["name"]]
                
                # Walk up the parent chain
                parent_id = folder.get("parent_folder_id")
                while parent_id and parent_id in folder_map:
                    parent = folder_map[parent_id]
                    path_parts.insert(0, parent["name"])
                    parent_id = parent.get("parent_folder_id")
                
                return "/".join(path_parts)
            
            # Test path reconstruction for sample folders
            print("   Sample folder paths:")
            for i, folder in enumerate(folders[:5]):
                folder_path = get_folder_path(folder["id"])
                print(f"   {i+1}. {folder['name']} -> {folder_path}")
        
        print("\n✅ Database analysis completed successfully")
        
        # Return summary for testing
        return {
            "clients_count": len(clients),
            "documents_count": len(documents),
            "folders_count": len(folders),
            "suitable_clients": suitable_clients,
            "docs_with_data": docs_with_data,
            "connection_success": True
        }
        
    except Exception as e:
        print(f"❌ Database analysis failed: {str(e)}")
        return {
            "connection_success": False,
            "error": str(e)
        }
    finally:
        if 'client' in locals():
            client.close()

async def main():
    """Run database analysis"""
    print(f"🎯 DATABASE ANALYSIS FOR BULK DOWNLOAD TESTING")
    print("=" * 70)
    print(f"MongoDB URL: {MONGO_URL[:50]}...")
    print(f"Database: {DB_NAME}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    result = await test_database_connection()
    
    print("\n" + "=" * 70)
    print("🏁 DATABASE ANALYSIS COMPLETED")
    print("=" * 70)
    
    if result.get("connection_success"):
        print("\n📋 SUMMARY:")
        print(f"✅ Database connection: SUCCESS")
        print(f"✅ Clients found: {result.get('clients_count', 0)}")
        print(f"✅ Documents found: {result.get('documents_count', 0)}")
        print(f"✅ Folders found: {result.get('folders_count', 0)}")
        print(f"✅ Suitable test clients: {len(result.get('suitable_clients', []))}")
        print(f"✅ Documents with data: {result.get('docs_with_data', 0)}")
        
        print("\n🎯 BULK DOWNLOAD READINESS:")
        if result.get('documents_count', 0) > 0 and result.get('docs_with_data', 0) > 0:
            print("✅ READY: Database has documents with file data for bulk download testing")
        else:
            print("⚠️  LIMITED: Database has limited data for bulk download testing")
    else:
        print(f"\n❌ Database connection failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())