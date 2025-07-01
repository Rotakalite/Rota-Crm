#!/usr/bin/env python3
"""
Railway Database Initialization Script
Initializes empty Railway MongoDB with essential data
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pymongo import MongoClient
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway MongoDB URL - UPDATE THIS WITH YOUR ACTUAL RAILWAY MONGO URL
RAILWAY_MONGO_URL = "mongodb://mongo:OeJzgbhMhSQbSKMtcTUW@roundhouse.proxy.rlwy.net:58050"

def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())

def init_railway_database():
    """Initialize Railway MongoDB with essential data"""
    try:
        logger.info("🚀 Starting Railway Database Initialization...")
        
        # Connect to Railway MongoDB
        client = MongoClient(RAILWAY_MONGO_URL)
        db = client['rotacrm']
        
        # Test connection
        client.admin.command('ping')
        logger.info("✅ Connected to Railway MongoDB successfully")
        
        # 1. Create Admin Users
        logger.info("👤 Creating admin users...")
        
        admin_users = [
            {
                "id": generate_uuid(),
                "clerk_user_id": "admin_test_001",
                "email": "admin@rotakalitedanismanlik.com",
                "name": "Admin User",
                "role": "admin",
                "client_id": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": generate_uuid(),
                "clerk_user_id": "admin_test_002", 
                "email": "rota@rotakalitedanismanlik.com",
                "name": "Rota Admin",
                "role": "admin",
                "client_id": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Insert admin users (update if exist)
        for user in admin_users:
            db.users.update_one(
                {"email": user["email"]}, 
                {"$set": user}, 
                upsert=True
            )
            logger.info(f"✅ Admin user created: {user['email']}")
        
        # 2. Create Test Clients
        logger.info("🏨 Creating test clients...")
        
        test_clients = [
            {
                "id": "KAYA_CLIENT_001",
                "client_id": "KAYA_CLIENT_001",
                "client_name": "KAYA Kalite Danışmanlık",
                "contact_person": "info@kayakalitedanismanlik.com",
                "hotel_name": "KAYA Kalite Danışmanlık",
                "current_stage": "I.Aşama",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": "CANO_CLIENT_001", 
                "client_id": "CANO_CLIENT_001",
                "client_name": "CANO Otel",
                "contact_person": "canerpal@gmail.com", 
                "hotel_name": "CANO Otel",
                "current_stage": "II.Aşama",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": "DENEME_CLIENT_001",
                "client_id": "DENEME_CLIENT_001", 
                "client_name": "DENEME Otel",
                "contact_person": "palavancaner@gmail.com",
                "hotel_name": "DENEME Otel", 
                "current_stage": "I.Aşama",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Insert test clients (update if exist)
        for client in test_clients:
            db.clients.update_one(
                {"client_id": client["client_id"]}, 
                {"$set": client}, 
                upsert=True
            )
            logger.info(f"✅ Test client created: {client['client_name']}")
        
        # 3. Create Client Users and Link them to Clients
        logger.info("👥 Creating client users...")
        
        client_users = [
            {
                "id": generate_uuid(),
                "clerk_user_id": "client_kaya_001",
                "email": "info@kayakalitedanismanlik.com", 
                "name": "KAYA User",
                "role": "client",
                "client_id": "KAYA_CLIENT_001",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": generate_uuid(),
                "clerk_user_id": "client_cano_001",
                "email": "canerpal@gmail.com",
                "name": "CANO User", 
                "role": "client",
                "client_id": "CANO_CLIENT_001",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": generate_uuid(),
                "clerk_user_id": "client_deneme_001", 
                "email": "palavancaner@gmail.com",
                "name": "DENEME User",
                "role": "client", 
                "client_id": "DENEME_CLIENT_001",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Insert client users (update if exist)
        for user in client_users:
            db.users.update_one(
                {"email": user["email"]}, 
                {"$set": user}, 
                upsert=True
            )
            logger.info(f"✅ Client user created and linked: {user['email']} -> {user['client_id']}")
        
        # 4. Create Initial Folder Structure for Each Client
        logger.info("📁 Creating folder structures...")
        
        for client in test_clients:
            client_id = client["client_id"]
            client_name = client["client_name"]
            
            # Root folder
            root_folder = {
                "id": generate_uuid(),
                "client_id": client_id,
                "name": f"{client_name} SYS",
                "level": 0,
                "parent_folder_id": None,
                "folder_path": f"{client_name} SYS",
                "created_at": datetime.utcnow()
            }
            
            db.folders.update_one(
                {"client_id": client_id, "level": 0},
                {"$set": root_folder},
                upsert=True
            )
            
            # Column folders
            columns = ["A SÜTUNU", "B SÜTUNU", "C SÜTUNU", "D SÜTUNU"]
            for column in columns:
                column_folder = {
                    "id": generate_uuid(),
                    "client_id": client_id,
                    "name": column,
                    "level": 1,
                    "parent_folder_id": root_folder["id"],
                    "folder_path": f"{client_name} SYS/{column}",
                    "created_at": datetime.utcnow()
                }
                
                db.folders.update_one(
                    {"client_id": client_id, "name": column, "level": 1},
                    {"$set": column_folder},
                    upsert=True
                )
            
            logger.info(f"✅ Folder structure created for: {client_name}")
        
        # 5. Create some test documents
        logger.info("📄 Creating test documents...")
        
        test_documents = [
            {
                "id": generate_uuid(),
                "client_id": "KAYA_CLIENT_001",
                "document_name": "Test Document 1.pdf",
                "document_type": "TR1_CRITERIA",
                "stage": "I.Aşama",
                "file_path": "/uploads/test_doc_1.pdf",
                "file_size": 1024,
                "original_filename": "test_doc_1.pdf",
                "folder_id": None,
                "created_at": datetime.utcnow()
            }
        ]
        
        for doc in test_documents:
            db.documents.update_one(
                {"file_path": doc["file_path"]},
                {"$set": doc},
                upsert=True
            )
            logger.info(f"✅ Test document created: {doc['document_name']}")
        
        # 6. Create some test trainings
        logger.info("🎓 Creating test trainings...")
        
        test_trainings = [
            {
                "id": generate_uuid(),
                "client_id": "KAYA_CLIENT_001",
                "name": "Temel Kalite Eğitimi",
                "subject": "Kalite Yönetim Sistemi",
                "participant_count": 25,
                "trainer": "Rota Kalite",
                "training_date": datetime.utcnow(),
                "description": "Temel kalite yönetim sistemi eğitimi",
                "status": "completed",
                "created_at": datetime.utcnow()
            }
        ]
        
        for training in test_trainings:
            db.trainings.update_one(
                {"name": training["name"], "client_id": training["client_id"]},
                {"$set": training},
                upsert=True
            )
            logger.info(f"✅ Test training created: {training['name']}")
        
        # Verify collections were created
        logger.info("\n📊 Database initialization summary:")
        collections = db.list_collection_names()
        for collection in ['users', 'clients', 'folders', 'documents', 'trainings']:
            if collection in collections:
                count = db[collection].count_documents({})
                logger.info(f"✅ {collection}: {count} records")
            else:
                logger.warning(f"❌ {collection}: Collection not found")
        
        logger.info("\n🎉 Railway Database Initialization COMPLETED!")
        logger.info("\n📋 What was created:")
        logger.info("   • 2 Admin users")
        logger.info("   • 3 Test clients (KAYA, CANO, DENEME)")
        logger.info("   • 3 Client users (properly linked)")
        logger.info("   • Folder structures for all clients")
        logger.info("   • Sample documents and trainings")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing Railway database: {e}")
        return False
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    print("🚨 RAILWAY DATABASE INITIALIZATION")
    print("This will initialize your Railway MongoDB with test data.")
    print("⚠️  WARNING: This will modify your production database!")
    
    # Get Railway MongoDB URL from user
    mongo_url = input("\n📝 Enter your Railway MongoDB URL: ").strip()
    if mongo_url:
        RAILWAY_MONGO_URL = mongo_url
    
    confirm = input(f"\n❓ Initialize Railway database at: {RAILWAY_MONGO_URL[:50]}...? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        success = init_railway_database()
        if success:
            print("\n✅ SUCCESS! Railway database initialized.")
            print("You can now login with:")
            print("   Admin: admin@rotakalitedanismanlik.com")
            print("   Client: info@kayakalitedanismanlik.com, canerpal@gmail.com, or palavancaner@gmail.com")
        else:
            print("\n❌ FAILED! Check logs for details.")
            sys.exit(1)
    else:
        print("\n🚫 Cancelled by user.")