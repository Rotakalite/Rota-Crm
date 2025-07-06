import asyncio
import json
import os
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"

# Search terms
SEARCH_TERMS = ['DENEME OTEL', 'TEST OTEL', 'SES123', 'Can', 'ALP OTEL']

async def search_database():
    """Search for the 5 specific clients across all databases and collections"""
    logger.info("Starting comprehensive database search...")
    
    # Connect to MongoDB
    client = MongoClient(MONGO_URL)
    
    # Get all databases
    databases = client.list_database_names()
    logger.info(f"Found databases: {databases}")
    
    # Search each database
    for db_name in databases:
        if db_name in ['admin', 'config', 'local']:
            logger.info(f"Skipping system database: {db_name}")
            continue
            
        logger.info(f"\n=== Searching database: {db_name} ===")
        db = client[db_name]
        
        # Get all collections
        collections = db.list_collection_names()
        logger.info(f"Collections in {db_name}: {collections}")
        
        # Search each collection
        for collection_name in collections:
            logger.info(f"\n--- Searching collection: {collection_name} ---")
            collection = db[collection_name]
            
            # Get sample document to understand schema
            sample_doc = collection.find_one()
            if not sample_doc:
                logger.info(f"Collection {collection_name} is empty")
                continue
                
            logger.info(f"Sample document fields: {list(sample_doc.keys())}")
            
            # Check if collection has client-related fields
            client_fields = []
            for field in sample_doc.keys():
                if 'client' in field.lower() or 'name' in field.lower() or 'hotel' in field.lower():
                    client_fields.append(field)
            
            if not client_fields:
                logger.info(f"No client-related fields found in {collection_name}")
                continue
                
            logger.info(f"Client-related fields: {client_fields}")
            
            # Search for each term in each client-related field
            for term in SEARCH_TERMS:
                logger.info(f"Searching for '{term}'...")
                
                # Build query to search across all client-related fields
                query = {"$or": []}
                for field in client_fields:
                    if isinstance(sample_doc.get(field), str):
                        query["$or"].append({field: {"$regex": term, "$options": "i"}})
                
                if not query["$or"]:
                    logger.info(f"No string fields to search for '{term}'")
                    continue
                    
                # Execute query
                results = list(collection.find(query).limit(10))
                logger.info(f"Found {len(results)} documents matching '{term}'")
                
                # Print results
                for doc in results:
                    # Convert ObjectId to string for printing
                    if '_id' in doc:
                        doc['_id'] = str(doc['_id'])
                    
                    # Print relevant fields only
                    relevant_doc = {}
                    for field in client_fields:
                        if field in doc:
                            relevant_doc[field] = doc[field]
                    
                    logger.info(f"Match: {relevant_doc}")
    
    # Check if there are any other MongoDB connections defined in environment variables
    logger.info("\n=== Checking for other MongoDB connections ===")
    env_vars = os.environ
    for key, value in env_vars.items():
        if 'MONGO' in key or 'DB' in key or 'DATABASE' in key:
            logger.info(f"Found environment variable: {key}={value}")
    
    logger.info("\n=== Search complete ===")

if __name__ == "__main__":
    asyncio.run(search_database())