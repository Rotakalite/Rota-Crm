import os
import sys
import json
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
db_name = "sustainable_tourism_crm"

async def list_collections():
    """List all collections in the database"""
    logger.info("\n=== Listing collections in database ===")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # List all collections
        collections = await db.list_collection_names()
        logger.info(f"Found {len(collections)} collections in the database")
        
        # Print collection names
        for i, collection_name in enumerate(collections):
            logger.info(f"Collection {i+1}: {collection_name}")
            
            # Count documents in each collection
            count = await db[collection_name].count_documents({})
            logger.info(f"  Documents in {collection_name}: {count}")
            
            # Show a sample document from each collection
            if count > 0:
                sample = await db[collection_name].find_one({})
                logger.info(f"  Sample document keys: {list(sample.keys())}")
        
        return collections
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        return []

async def main():
    """Main function to run database queries"""
    logger.info("Starting database queries...")
    
    # List collections
    await list_collections()

if __name__ == "__main__":
    asyncio.run(main())