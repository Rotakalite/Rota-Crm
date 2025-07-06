import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "sustainable_tourism_crm"

# Alternative database
ALT_DB_NAME = "rotacrm"

# Client names to search for
CLIENT_NAMES = ["Can", "DENEME OTEL", "TEST OTEL", "SES123", "ALP OTEL"]

# Folder structure names to search for
FOLDER_NAMES = ["A SÜTUNU", "B SÜTUNU", "C SÜTUNU", "D SÜTUNU"]

async def search_database(db_name):
    logger.info(f"Searching in database: {db_name}")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[db_name]
    
    # Get all collections in the database
    collections = await db.list_collection_names()
    logger.info(f"Collections in {db_name}: {collections}")
    
    # Search for client names in all collections
    for collection_name in collections:
        logger.info(f"Searching in collection: {collection_name}")
        collection = db[collection_name]
        
        # Search for exact client names
        for name in CLIENT_NAMES:
            # Search in any field that might contain the name
            query = {"$or": [
                {"name": name},
                {"hotel_name": name},
                {"client_name": name},
                {"company_name": name},
                {"title": name},
                {"description": {"$regex": name, "$options": "i"}},
                {"content": {"$regex": name, "$options": "i"}}
            ]}
            
            count = await collection.count_documents(query)
            if count > 0:
                logger.info(f"Found {count} documents with name '{name}' in collection '{collection_name}'")
                
                # Get the documents
                async for doc in collection.find(query):
                    logger.info(f"Document: {doc}")
        
        # Search for folder structure names
        for folder_name in FOLDER_NAMES:
            # Search in any field that might contain the folder name
            query = {"$or": [
                {"name": folder_name},
                {"folder_name": folder_name},
                {"folder_path": {"$regex": folder_name, "$options": "i"}},
                {"path": {"$regex": folder_name, "$options": "i"}}
            ]}
            
            count = await collection.count_documents(query)
            if count > 0:
                logger.info(f"Found {count} documents with folder name '{folder_name}' in collection '{collection_name}'")
                
                # Get the documents
                async for doc in collection.find(query):
                    logger.info(f"Document: {doc}")
    
    # Also search for variations of client names (case insensitive)
    logger.info("Searching for case variations of client names...")
    for collection_name in collections:
        collection = db[collection_name]
        
        for name in CLIENT_NAMES:
            # Case insensitive search
            query = {"$or": [
                {"name": {"$regex": f"^{name}$", "$options": "i"}},
                {"hotel_name": {"$regex": f"^{name}$", "$options": "i"}},
                {"client_name": {"$regex": f"^{name}$", "$options": "i"}},
                {"company_name": {"$regex": f"^{name}$", "$options": "i"}}
            ]}
            
            count = await collection.count_documents(query)
            if count > 0:
                logger.info(f"Found {count} documents with case variation of '{name}' in collection '{collection_name}'")
                
                # Get the documents
                async for doc in collection.find(query):
                    logger.info(f"Document: {doc}")
    
    # Search for Turkish character variations
    logger.info("Searching for Turkish character variations...")
    turkish_variations = {
        "SÜTUNU": "SUTUNU"
    }
    
    for original, variation in turkish_variations.items():
        for collection_name in collections:
            collection = db[collection_name]
            
            query = {"$or": [
                {"name": {"$regex": variation, "$options": "i"}},
                {"folder_name": {"$regex": variation, "$options": "i"}},
                {"folder_path": {"$regex": variation, "$options": "i"}},
                {"path": {"$regex": variation, "$options": "i"}}
            ]}
            
            count = await collection.count_documents(query)
            if count > 0:
                logger.info(f"Found {count} documents with Turkish variation '{variation}' (original: '{original}') in collection '{collection_name}'")
                
                # Get the documents
                async for doc in collection.find(query):
                    logger.info(f"Document: {doc}")

async def main():
    # Search in both databases
    await search_database(DB_NAME)
    await search_database(ALT_DB_NAME)

if __name__ == "__main__":
    asyncio.run(main())