import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json
from bson import json_util
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "sustainable_tourism_crm"

async def list_collections():
    """List all collections in the database"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    collections = await db.list_collection_names()
    logger.info(f"Collections in database: {collections}")
    return collections

async def check_users_collection():
    """Check users collection for CLIENT role users"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Find users with role CLIENT
    client_users = await db.users.find({"role": "client"}).to_list(length=None)
    logger.info(f"Found {len(client_users)} users with role CLIENT")
    
    # Print details of each client user
    for i, user in enumerate(client_users):
        logger.info(f"CLIENT USER {i+1}:")
        logger.info(f"  ID: {user.get('id')}")
        logger.info(f"  Name: {user.get('name')}")
        logger.info(f"  Email: {user.get('email')}")
        logger.info(f"  Client ID: {user.get('client_id')}")
        logger.info(f"  Clerk User ID: {user.get('clerk_user_id')}")
    
    return client_users

async def check_clients_collection():
    """Check clients collection for the 5 specific clients"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get all clients
    all_clients = await db.clients.find().to_list(length=None)
    logger.info(f"Found {len(all_clients)} clients in clients collection")
    
    # Look for the 5 specific clients
    target_clients = ["DENEME OTEL", "TEST OTEL", "SES123", "Can", "ALP OTEL"]
    found_clients = []
    
    for client_doc in all_clients:
        client_name = client_doc.get("name", "")
        hotel_name = client_doc.get("hotel_name", "")
        
        # Check if this client matches any of our targets
        for target in target_clients:
            if (target.lower() in client_name.lower() or 
                target.lower() in hotel_name.lower()):
                logger.info(f"Found target client: {client_name} / {hotel_name}")
                logger.info(f"  ID: {client_doc.get('id')}")
                logger.info(f"  Contact: {client_doc.get('contact_person')}")
                logger.info(f"  Email: {client_doc.get('email')}")
                found_clients.append(client_doc)
                break
    
    # Print all clients if we didn't find our targets
    if not found_clients:
        logger.info("Target clients not found. Listing all clients:")
        for i, client_doc in enumerate(all_clients):
            logger.info(f"CLIENT {i+1}:")
            logger.info(f"  Name: {client_doc.get('name')}")
            logger.info(f"  Hotel Name: {client_doc.get('hotel_name')}")
            logger.info(f"  ID: {client_doc.get('id')}")
            logger.info(f"  Contact: {client_doc.get('contact_person')}")
            logger.info(f"  Email: {client_doc.get('email')}")
    
    return all_clients, found_clients

async def count_documents_per_client():
    """Count documents per client_id"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get all clients
    all_clients = await db.clients.find().to_list(length=None)
    
    # Count documents for each client
    for client_doc in all_clients:
        client_id = client_doc.get("id")
        client_name = client_doc.get("name")
        hotel_name = client_doc.get("hotel_name")
        
        # Count documents
        doc_count = await db.documents.count_documents({"client_id": client_id})
        
        logger.info(f"Client: {client_name} / {hotel_name}")
        logger.info(f"  ID: {client_id}")
        logger.info(f"  Document count: {doc_count}")
        
        # If there are documents, show some details
        if doc_count > 0:
            docs = await db.documents.find({"client_id": client_id}).to_list(length=5)
            logger.info(f"  Sample documents (up to 5):")
            for i, doc in enumerate(docs):
                logger.info(f"    Doc {i+1}: {doc.get('name')} - Type: {doc.get('document_type')}")

async def count_trainings_per_client():
    """Count trainings per client_id"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get all clients
    all_clients = await db.clients.find().to_list(length=None)
    
    # Count trainings for each client
    for client_doc in all_clients:
        client_id = client_doc.get("id")
        client_name = client_doc.get("name")
        hotel_name = client_doc.get("hotel_name")
        
        # Count trainings
        training_count = await db.trainings.count_documents({"client_id": client_id})
        
        logger.info(f"Client: {client_name} / {hotel_name}")
        logger.info(f"  ID: {client_id}")
        logger.info(f"  Training count: {training_count}")
        
        # If there are trainings, show some details
        if training_count > 0:
            trainings = await db.trainings.find({"client_id": client_id}).to_list(length=5)
            logger.info(f"  Sample trainings (up to 5):")
            for i, training in enumerate(trainings):
                logger.info(f"    Training {i+1}: {training.get('name')} - Status: {training.get('status')}")

async def check_email_management_collections():
    """Check collections related to email management"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Check if there are specific email management collections
    collections = await db.list_collection_names()
    email_collections = [coll for coll in collections if 'email' in coll.lower()]
    
    if email_collections:
        logger.info(f"Found email-related collections: {email_collections}")
        for coll_name in email_collections:
            count = await db[coll_name].count_documents({})
            logger.info(f"Collection {coll_name} has {count} documents")
            
            if count > 0:
                docs = await db[coll_name].find().to_list(length=5)
                logger.info(f"Sample documents from {coll_name} (up to 5):")
                for i, doc in enumerate(docs):
                    logger.info(f"  Doc {i+1}: {json.dumps(json_util.dumps(doc))}")
    else:
        logger.info("No email-specific collections found")
        
        # Check if email management data might be in other collections
        logger.info("Checking for email-related fields in other collections...")
        
        # Check documents collection for email-related fields
        email_docs = await db.documents.find({"document_type": {"$regex": "email", "$options": "i"}}).to_list(length=5)
        if email_docs:
            logger.info(f"Found {len(email_docs)} documents with email-related document_type")
            for i, doc in enumerate(email_docs):
                logger.info(f"  Doc {i+1}: {doc.get('name')} - Type: {doc.get('document_type')}")

async def main():
    """Main function to run all checks"""
    logger.info("Starting database investigation")
    
    # List all collections
    logger.info("\n=== COLLECTIONS IN DATABASE ===")
    collections = await list_collections()
    
    # Check users collection
    logger.info("\n=== USERS WITH CLIENT ROLE ===")
    client_users = await check_users_collection()
    
    # Check clients collection
    logger.info("\n=== CLIENTS COLLECTION ===")
    all_clients, found_clients = await check_clients_collection()
    
    # Count documents per client
    logger.info("\n=== DOCUMENTS PER CLIENT ===")
    await count_documents_per_client()
    
    # Count trainings per client
    logger.info("\n=== TRAININGS PER CLIENT ===")
    await count_trainings_per_client()
    
    # Check email management collections
    logger.info("\n=== EMAIL MANAGEMENT COLLECTIONS ===")
    await check_email_management_collections()
    
    logger.info("\nDatabase investigation complete")

if __name__ == "__main__":
    asyncio.run(main())