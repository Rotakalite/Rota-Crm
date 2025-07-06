import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import json
from bson import json_util

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "sustainable_tourism_crm"
ALT_DB_NAME = "rotacrm"

# Parse MongoDB document to JSON
def parse_json(data):
    return json.loads(json_util.dumps(data))

async def list_all_folders():
    logger.info("Listing all folders in both databases")
    
    # Connect to sustainable_tourism_crm
    client1 = AsyncIOMotorClient(MONGO_URL)
    db1 = client1[DB_NAME]
    
    # Connect to rotacrm
    client2 = AsyncIOMotorClient(MONGO_URL)
    db2 = client2[ALT_DB_NAME]
    
    # Check if folders collection exists in sustainable_tourism_crm
    collections1 = await db1.list_collection_names()
    if "folders" in collections1:
        logger.info(f"Folders in {DB_NAME}:")
        async for doc in db1.folders.find():
            logger.info(f"Folder: {parse_json(doc)}")
    else:
        logger.info(f"No folders collection in {DB_NAME}")
    
    # Check if folders collection exists in rotacrm
    collections2 = await db2.list_collection_names()
    if "folders" in collections2:
        logger.info(f"Folders in {ALT_DB_NAME}:")
        # Get root folders first
        logger.info("Root folders:")
        async for doc in db2.folders.find({"level": 0}):
            logger.info(f"Root Folder: {parse_json(doc)}")
        
        # Get column folders (A, B, C, D SÜTUNU)
        logger.info("Column folders:")
        async for doc in db2.folders.find({"level": 1, "name": {"$in": ["A SÜTUNU", "B SÜTUNU", "C SÜTUNU", "D SÜTUNU"]}}):
            logger.info(f"Column Folder: {parse_json(doc)}")
    else:
        logger.info(f"No folders collection in {ALT_DB_NAME}")

if __name__ == "__main__":
    asyncio.run(list_all_folders())