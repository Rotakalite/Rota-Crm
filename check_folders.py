#!/usr/bin/env python3
"""
Script to check folder structure for all clients
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get MongoDB URL from environment
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = 'sustainable_tourism_crm'

async def check_folder_structure():
    """Check folder structure for all clients"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        logging.info("🔗 Connected to MongoDB")
        
        # Get all clients
        clients = await db.clients.find({}).to_list(length=None)
        logging.info(f"📋 Found {len(clients)} clients")
        
        for client_doc in clients:
            client_id = client_doc["id"]
            client_name = client_doc["name"]
            
            logging.info(f"\n🏢 Client: {client_name} (ID: {client_id})")
            
            # Get folders for this client
            folders = await db.folders.find({"client_id": client_id}).to_list(length=None)
            logging.info(f"📁 Total folders: {len(folders)}")
            
            # Group by level
            level_0 = [f for f in folders if f.get("level") == 0]
            level_1 = [f for f in folders if f.get("level") == 1]
            level_2 = [f for f in folders if f.get("level") == 2]
            level_3 = [f for f in folders if f.get("level") == 3]
            
            logging.info(f"  Level 0 (Root): {len(level_0)} folders")
            for folder in level_0:
                logging.info(f"    - {folder['name']}")
            
            logging.info(f"  Level 1 (Columns): {len(level_1)} folders")
            for folder in level_1:
                logging.info(f"    - {folder['name']}")
            
            logging.info(f"  Level 2 (Sub-folders): {len(level_2)} folders")
            for folder in level_2:
                logging.info(f"    - {folder['name']} (parent: {folder.get('parent_folder_id')})")
            
            logging.info(f"  Level 3 (Level 3 folders): {len(level_3)} folders")
            for folder in level_3:
                logging.info(f"    - {folder['name']} (parent: {folder.get('parent_folder_id')})")
        
        client.close()
        return True
        
    except Exception as e:
        logging.error(f"❌ Error checking folder structure: {str(e)}")
        return False

if __name__ == "__main__":
    logging.info("🚀 Starting folder structure check...")
    success = asyncio.run(check_folder_structure())