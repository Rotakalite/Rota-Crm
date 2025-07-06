import asyncio
import logging
import json
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
db_name = "sustainable_tourism_crm"

async def check_mongodb_connection():
    """Check if we can connect to MongoDB"""
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Try to ping the database
        await db.command("ping")
        logger.info("✅ Successfully connected to MongoDB")
        return True, client, db
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
        return False, None, None

async def list_collections(db):
    """List all collections in the database"""
    try:
        collections = await db.list_collection_names()
        logger.info(f"📋 Collections in database: {collections}")
        return collections
    except Exception as e:
        logger.error(f"❌ Failed to list collections: {str(e)}")
        return []

async def count_documents(db, collection_name):
    """Count documents in a collection"""
    try:
        count = await db[collection_name].count_documents({})
        logger.info(f"📊 Collection '{collection_name}' has {count} documents")
        return count
    except Exception as e:
        logger.error(f"❌ Failed to count documents in '{collection_name}': {str(e)}")
        return 0

async def get_all_clients(db):
    """Get all clients from the database"""
    try:
        clients = await db.clients.find().to_list(length=None)
        
        # Format for better readability
        formatted_clients = []
        for client in clients:
            if "_id" in client:
                del client["_id"]
            
            # Convert datetime objects to strings
            for key, value in client.items():
                if isinstance(value, datetime):
                    client[key] = value.isoformat()
            
            formatted_clients.append(client)
        
        logger.info(f"👥 Found {len(formatted_clients)} clients")
        
        # Print client details
        for client in formatted_clients:
            logger.info(f"  - ID: {client.get('id')}")
            logger.info(f"    Name: {client.get('name')}")
            logger.info(f"    Hotel Name: {client.get('hotel_name')}")
            logger.info(f"    Email: {client.get('email')}")
            logger.info(f"    Contact Person: {client.get('contact_person')}")
            logger.info(f"    Current Stage: {client.get('current_stage')}")
            logger.info(f"    Created At: {client.get('created_at')}")
            logger.info("")
        
        return formatted_clients
    except Exception as e:
        logger.error(f"❌ Failed to get clients: {str(e)}")
        return []

async def get_documents_by_client_id(db, client_id):
    """Get documents for a specific client"""
    try:
        documents = await db.documents.find({"client_id": client_id}).to_list(length=None)
        
        # Format for better readability
        formatted_documents = []
        for doc in documents:
            if "_id" in doc:
                del doc["_id"]
            
            # Convert datetime objects to strings
            for key, value in doc.items():
                if isinstance(value, datetime):
                    doc[key] = value.isoformat()
            
            formatted_documents.append(doc)
        
        logger.info(f"📄 Found {len(formatted_documents)} documents for client ID: {client_id}")
        
        # Print document details
        for doc in formatted_documents:
            logger.info(f"  - ID: {doc.get('id')}")
            logger.info(f"    Name: {doc.get('name')}")
            logger.info(f"    Document Type: {doc.get('document_type')}")
            logger.info(f"    Stage: {doc.get('stage')}")
            logger.info(f"    File Path: {doc.get('file_path')}")
            logger.info(f"    Created At: {doc.get('created_at')}")
            logger.info("")
        
        return formatted_documents
    except Exception as e:
        logger.error(f"❌ Failed to get documents for client {client_id}: {str(e)}")
        return []

async def get_trainings_by_client_id(db, client_id):
    """Get trainings for a specific client"""
    try:
        trainings = await db.trainings.find({"client_id": client_id}).to_list(length=None)
        
        # Format for better readability
        formatted_trainings = []
        for training in trainings:
            if "_id" in training:
                del training["_id"]
            
            # Convert datetime objects to strings
            for key, value in training.items():
                if isinstance(value, datetime):
                    training[key] = value.isoformat()
            
            formatted_trainings.append(training)
        
        logger.info(f"🎓 Found {len(formatted_trainings)} trainings for client ID: {client_id}")
        
        # Print training details
        for training in formatted_trainings:
            logger.info(f"  - ID: {training.get('id')}")
            logger.info(f"    Name: {training.get('name')}")
            logger.info(f"    Subject: {training.get('subject')}")
            logger.info(f"    Trainer: {training.get('trainer')}")
            logger.info(f"    Participant Count: {training.get('participant_count')}")
            logger.info(f"    Training Date: {training.get('training_date')}")
            logger.info(f"    Status: {training.get('status')}")
            logger.info(f"    Created At: {training.get('created_at')}")
            logger.info("")
        
        return formatted_trainings
    except Exception as e:
        logger.error(f"❌ Failed to get trainings for client {client_id}: {str(e)}")
        return []

async def get_all_documents(db):
    """Get all documents from the database"""
    try:
        documents = await db.documents.find().to_list(length=None)
        
        # Format for better readability
        formatted_documents = []
        for doc in documents:
            if "_id" in doc:
                del doc["_id"]
            
            # Convert datetime objects to strings
            for key, value in doc.items():
                if isinstance(value, datetime):
                    doc[key] = value.isoformat()
            
            formatted_documents.append(doc)
        
        logger.info(f"📄 Found {len(formatted_documents)} total documents")
        
        # Count documents by client_id
        client_doc_counts = {}
        for doc in formatted_documents:
            client_id = doc.get("client_id")
            if client_id not in client_doc_counts:
                client_doc_counts[client_id] = 0
            client_doc_counts[client_id] += 1
        
        logger.info("📊 Document counts by client_id:")
        for client_id, count in client_doc_counts.items():
            logger.info(f"  - Client ID: {client_id}, Document Count: {count}")
        
        return formatted_documents
    except Exception as e:
        logger.error(f"❌ Failed to get all documents: {str(e)}")
        return []

async def get_all_trainings(db):
    """Get all trainings from the database"""
    try:
        trainings = await db.trainings.find().to_list(length=None)
        
        # Format for better readability
        formatted_trainings = []
        for training in trainings:
            if "_id" in training:
                del training["_id"]
            
            # Convert datetime objects to strings
            for key, value in training.items():
                if isinstance(value, datetime):
                    training[key] = value.isoformat()
            
            formatted_trainings.append(training)
        
        logger.info(f"🎓 Found {len(formatted_trainings)} total trainings")
        
        # Count trainings by client_id
        client_training_counts = {}
        for training in formatted_trainings:
            client_id = training.get("client_id")
            if client_id not in client_training_counts:
                client_training_counts[client_id] = 0
            client_training_counts[client_id] += 1
        
        logger.info("📊 Training counts by client_id:")
        for client_id, count in client_training_counts.items():
            logger.info(f"  - Client ID: {client_id}, Training Count: {count}")
        
        return formatted_trainings
    except Exception as e:
        logger.error(f"❌ Failed to get all trainings: {str(e)}")
        return []

async def main():
    """Main function to check MongoDB data"""
    logger.info("🔍 Starting MongoDB data check for Email Management")
    
    # Check MongoDB connection
    success, client, db = await check_mongodb_connection()
    if not success:
        logger.error("❌ Cannot proceed without MongoDB connection")
        return
    
    try:
        # List collections
        collections = await list_collections(db)
        
        # Count documents in key collections
        await count_documents(db, "clients")
        await count_documents(db, "documents")
        await count_documents(db, "trainings")
        
        # Get all clients
        logger.info("\n=== CLIENTS ===")
        clients = await get_all_clients(db)
        
        # Get all documents
        logger.info("\n=== DOCUMENTS ===")
        documents = await get_all_documents(db)
        
        # Get all trainings
        logger.info("\n=== TRAININGS ===")
        trainings = await get_all_trainings(db)
        
        # For each client, get their documents and trainings
        logger.info("\n=== DETAILED CLIENT DATA ===")
        for client in clients:
            client_id = client.get("id")
            logger.info(f"\n👥 Client: {client.get('name')} (ID: {client_id})")
            
            # Get documents for this client
            client_documents = await get_documents_by_client_id(db, client_id)
            
            # Get trainings for this client
            client_trainings = await get_trainings_by_client_id(db, client_id)
        
        logger.info("\n✅ MongoDB data check complete")
    
    except Exception as e:
        logger.error(f"❌ Error during MongoDB data check: {str(e)}")
    finally:
        # Close MongoDB connection
        if client:
            client.close()
            logger.info("🔌 MongoDB connection closed")

if __name__ == "__main__":
    asyncio.run(main())