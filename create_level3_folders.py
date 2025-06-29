#!/usr/bin/env python3
"""
Script to manually create Level 3 folders for existing clients
This script will create D1.1-D1.4, D2.1-D2.6, D3.1-D3.6 folders for all existing clients
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get MongoDB URL from environment
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = 'rota_crm'

async def create_level3_folders():
    """Create Level 3 folders for all existing clients"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        logging.info("🔗 Connected to MongoDB")
        
        # Get all clients
        clients = await db.clients.find({}).to_list(length=None)
        logging.info(f"📋 Found {len(clients)} clients")
        
        if not clients:
            logging.warning("⚠️ No clients found in database")
            return False
        
        # Define Level 3 sub-folders for D column
        d_level3_structure = {
            "D1": ["D1.1", "D1.2", "D1.3", "D1.4"],
            "D2": ["D2.1", "D2.2", "D2.3", "D2.4", "D2.5", "D2.6"],
            "D3": ["D3.1", "D3.2", "D3.3", "D3.4", "D3.5", "D3.6"]
        }
        
        total_created = 0
        
        for client in clients:
            client_id = client["id"]
            client_name = client["name"]
            
            logging.info(f"🏢 Processing client: {client_name} (ID: {client_id})")
            
            # Find D1, D2, D3 folders for this client
            d_folders = await db.folders.find({
                "client_id": client_id,
                "level": 2,
                "name": {"$in": ["D1", "D2", "D3"]}
            }).to_list(length=None)
            
            logging.info(f"📁 Found {len(d_folders)} D folders for client {client_name}")
            
            for d_folder in d_folders:
                d_folder_name = d_folder["name"]
                d_folder_id = d_folder["id"]
                d_folder_path = d_folder["folder_path"]
                
                if d_folder_name in d_level3_structure:
                    level3_folder_names = d_level3_structure[d_folder_name]
                    
                    for level3_folder_name in level3_folder_names:
                        # Check if Level 3 folder already exists
                        existing_level3 = await db.folders.find_one({
                            "client_id": client_id,
                            "parent_folder_id": d_folder_id,
                            "name": level3_folder_name
                        })
                        
                        if existing_level3:
                            logging.info(f"✅ Level 3 folder already exists: {d_folder_name}/{level3_folder_name}")
                            continue
                        
                        # Create Level 3 folder
                        level3_folder = {
                            "id": str(uuid.uuid4()),
                            "client_id": client_id,
                            "name": level3_folder_name,
                            "parent_folder_id": d_folder_id,
                            "folder_path": f"{d_folder_path}/{level3_folder_name}",
                            "level": 3,
                            "created_at": datetime.utcnow()
                        }
                        
                        await db.folders.insert_one(level3_folder)
                        logging.info(f"🆕 Created Level 3 folder: {client_name}/{d_folder_name}/{level3_folder_name}")
                        total_created += 1
        
        logging.info(f"✅ Successfully created {total_created} Level 3 folders")
        
        # Verify creation by counting Level 3 folders
        level3_count = await db.folders.count_documents({"level": 3})
        logging.info(f"📊 Total Level 3 folders in database: {level3_count}")
        
        client.close()
        return True
        
    except Exception as e:
        logging.error(f"❌ Error creating Level 3 folders: {str(e)}")
        return False

if __name__ == "__main__":
    logging.info("🚀 Starting Level 3 folder creation script...")
    success = asyncio.run(create_level3_folders())
    
    if success:
        logging.info("✅ Script completed successfully!")
        sys.exit(0)
    else:
        logging.error("❌ Script failed!")
        sys.exit(1)