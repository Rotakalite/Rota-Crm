#!/usr/bin/env python3
"""
Script to create complete folder structure for KAYA client
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get MongoDB URL from environment
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = 'sustainable_tourism_crm'

async def create_kaya_folders():
    """Create complete folder structure for KAYA client"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        logging.info("🔗 Connected to MongoDB")
        
        # Find KAYA client
        kaya_client = await db.clients.find_one({"name": "KAYA"})
        
        if not kaya_client:
            logging.error("❌ KAYA client not found")
            return False
        
        client_id = kaya_client["id"]
        client_name = kaya_client["name"]
        
        logging.info(f"🏢 Found KAYA client: {client_name} (ID: {client_id})")
        
        # Create root folder
        root_folder_name = f"{client_name} SYS"
        root_folder = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "name": root_folder_name,
            "parent_folder_id": None,
            "folder_path": root_folder_name,
            "level": 0,
            "created_at": datetime.utcnow()
        }
        
        await db.folders.insert_one(root_folder)
        logging.info(f"📁 Created root folder: {root_folder_name}")
        
        # Define folder structure
        column_structure = {
            "A SÜTUNU": ["A1", "A2", "A3", "A4", "A5", "A7.1", "A7.2", "A7.3", "A7.4", "A8", "A9", "A10"],
            "B SÜTUNU": ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"],
            "C SÜTUNU": ["C1", "C2", "C3", "C4"],
            "D SÜTUNU": ["D1", "D2", "D3"]
        }
        
        d_level3_structure = {
            "D1": ["D1.1", "D1.2", "D1.3", "D1.4"],
            "D2": ["D2.1", "D2.2", "D2.3", "D2.4", "D2.5", "D2.6"],
            "D3": ["D3.1", "D3.2", "D3.3", "D3.4", "D3.5", "D3.6"]
        }
        
        # Create column folders
        for column_name, sub_folders in column_structure.items():
            # Create column folder
            column_folder_id = str(uuid.uuid4())
            column_folder = {
                "id": column_folder_id,
                "client_id": client_id,
                "name": column_name,
                "parent_folder_id": root_folder["id"],
                "folder_path": f"{root_folder_name}/{column_name}",
                "level": 1,
                "created_at": datetime.utcnow()
            }
            
            await db.folders.insert_one(column_folder)
            logging.info(f"📁 Created column folder: {column_name}")
            
            # Create sub-folders
            for sub_folder_name in sub_folders:
                sub_folder = {
                    "id": str(uuid.uuid4()),
                    "client_id": client_id,
                    "name": sub_folder_name,
                    "parent_folder_id": column_folder_id,
                    "folder_path": f"{root_folder_name}/{column_name}/{sub_folder_name}",
                    "level": 2,
                    "created_at": datetime.utcnow()
                }
                
                await db.folders.insert_one(sub_folder)
                logging.info(f"📁 Created sub-folder: {column_name}/{sub_folder_name}")
                
                # Create Level 3 sub-folders for D column
                if column_name == "D SÜTUNU" and sub_folder_name in d_level3_structure:
                    level3_folders = d_level3_structure[sub_folder_name]
                    for level3_folder_name in level3_folders:
                        level3_folder = {
                            "id": str(uuid.uuid4()),
                            "client_id": client_id,
                            "name": level3_folder_name,
                            "parent_folder_id": sub_folder["id"],
                            "folder_path": f"{root_folder_name}/{column_name}/{sub_folder_name}/{level3_folder_name}",
                            "level": 3,
                            "created_at": datetime.utcnow()
                        }
                        
                        await db.folders.insert_one(level3_folder)
                        logging.info(f"📁 Created Level 3 folder: {column_name}/{sub_folder_name}/{level3_folder_name}")
        
        logging.info("✅ Successfully created complete folder structure for KAYA")
        
        # Verify creation
        total_folders = await db.folders.count_documents({"client_id": client_id})
        logging.info(f"📊 Total folders created for KAYA: {total_folders}")
        
        client.close()
        return True
        
    except Exception as e:
        logging.error(f"❌ Error creating KAYA folders: {str(e)}")
        return False

if __name__ == "__main__":
    logging.info("🚀 Starting KAYA folder creation...")
    success = asyncio.run(create_kaya_folders())