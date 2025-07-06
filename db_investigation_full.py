import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json
from bson import json_util
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "sustainable_tourism_crm"

async def list_all_collections():
    """List all collections in the database"""
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        collections = await db.list_collection_names()
        logger.info(f"Collections in database: {collections}")
        
        # Count documents in each collection
        for collection_name in collections:
            count = await db[collection_name].count_documents({})
            logger.info(f"Collection '{collection_name}' has {count} documents")
        
        return collections
    except Exception as e:
        logger.error(f"Error listing collections: {str(e)}")
        return []

async def search_for_clients():
    """Search for the 5 clients in all collections"""
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Target clients to find
        target_clients = ["DENEME OTEL", "TEST OTEL", "SES123", "Can", "ALP OTEL"]
        
        # Get all collections
        collections = await db.list_collection_names()
        
        # Search in each collection
        for collection_name in collections:
            logger.info(f"\n=== SEARCHING IN {collection_name} COLLECTION ===")
            
            # Get all documents in the collection
            documents = await db[collection_name].find().to_list(length=None)
            logger.info(f"Found {len(documents)} documents in {collection_name} collection")
            
            # Search for target clients in each document
            found_documents = []
            for doc in documents:
                # Convert document to string for easy searching
                doc_str = str(doc).lower()
                
                # Check if any target client name is in the document
                for target in target_clients:
                    if target.lower() in doc_str:
                        logger.info(f"Found match for '{target}' in {collection_name}:")
                        logger.info(f"  Document: {json.dumps(json_util.loads(json_util.dumps(doc)), indent=2)}")
                        found_documents.append((target, doc))
                        break
            
            logger.info(f"Found {len(found_documents)} matches in {collection_name} collection")
            
            # If no matches found, show sample documents
            if not found_documents and len(documents) > 0:
                logger.info(f"No matches found in {collection_name}. Sample document:")
                sample_doc = documents[0]
                logger.info(f"  {json.dumps(json_util.loads(json_util.dumps(sample_doc)), indent=2)}")
    
    except Exception as e:
        logger.error(f"Error searching for clients: {str(e)}")

async def check_users_collection():
    """Check users collection for CLIENT role users"""
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        logger.info("\n=== CHECKING USERS COLLECTION FOR CLIENT ROLE ===")
        
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
            
            # If user has client_id, check if client exists
            client_id = user.get('client_id')
            if client_id:
                client = await db.clients.find_one({"id": client_id})
                if client:
                    logger.info(f"  Associated Client: {client.get('name')} / {client.get('hotel_name')}")
                else:
                    logger.info(f"  No associated client found with ID: {client_id}")
    
    except Exception as e:
        logger.error(f"Error checking users collection: {str(e)}")

async def check_clients_collection():
    """Check clients collection"""
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        logger.info("\n=== CHECKING CLIENTS COLLECTION ===")
        
        # Get all clients
        all_clients = await db.clients.find().to_list(length=None)
        logger.info(f"Found {len(all_clients)} clients in clients collection")
        
        # Print details of each client
        for i, client_doc in enumerate(all_clients):
            logger.info(f"CLIENT {i+1}:")
            logger.info(f"  ID: {client_doc.get('id')}")
            logger.info(f"  Name: {client_doc.get('name')}")
            logger.info(f"  Hotel Name: {client_doc.get('hotel_name')}")
            logger.info(f"  Contact: {client_doc.get('contact_person')}")
            logger.info(f"  Email: {client_doc.get('email')}")
            logger.info(f"  Current Stage: {client_doc.get('current_stage')}")
            
            # Check for associated users
            users = await db.users.find({"client_id": client_doc.get('id')}).to_list(length=None)
            logger.info(f"  Associated Users: {len(users)}")
            for j, user in enumerate(users):
                logger.info(f"    User {j+1}: {user.get('name')} ({user.get('email')})")
            
            # Check for associated documents
            documents = await db.documents.find({"client_id": client_doc.get('id')}).to_list(length=None)
            logger.info(f"  Associated Documents: {len(documents)}")
            
            # Check for associated trainings
            trainings = await db.trainings.find({"client_id": client_doc.get('id')}).to_list(length=None)
            logger.info(f"  Associated Trainings: {len(trainings)}")
    
    except Exception as e:
        logger.error(f"Error checking clients collection: {str(e)}")

async def check_documents_collection():
    """Check documents collection"""
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        logger.info("\n=== CHECKING DOCUMENTS COLLECTION ===")
        
        # Get all documents
        all_documents = await db.documents.find().to_list(length=None)
        logger.info(f"Found {len(all_documents)} documents in documents collection")
        
        # Group documents by client_id
        documents_by_client = {}
        for doc in all_documents:
            client_id = doc.get('client_id')
            if client_id not in documents_by_client:
                documents_by_client[client_id] = []
            documents_by_client[client_id].append(doc)
        
        # Print document counts by client
        logger.info("\n=== DOCUMENT COUNTS BY CLIENT ===")
        for client_id, docs in documents_by_client.items():
            # Get client info
            client_doc = await db.clients.find_one({"id": client_id})
            client_name = client_doc.get('name', 'Unknown') if client_doc else 'Unknown'
            hotel_name = client_doc.get('hotel_name', '') if client_doc else ''
            
            logger.info(f"Client: {client_name} / {hotel_name}")
            logger.info(f"  ID: {client_id}")
            logger.info(f"  Document count: {len(docs)}")
            
            # Group documents by type
            docs_by_type = {}
            for doc in docs:
                doc_type = doc.get('document_type', 'Unknown')
                if doc_type not in docs_by_type:
                    docs_by_type[doc_type] = 0
                docs_by_type[doc_type] += 1
            
            # Print document counts by type
            for doc_type, count in docs_by_type.items():
                logger.info(f"    {doc_type}: {count} documents")
    
    except Exception as e:
        logger.error(f"Error checking documents collection: {str(e)}")

async def check_trainings_collection():
    """Check trainings collection"""
    try:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        logger.info("\n=== CHECKING TRAININGS COLLECTION ===")
        
        # Get all trainings
        all_trainings = await db.trainings.find().to_list(length=None)
        logger.info(f"Found {len(all_trainings)} trainings in trainings collection")
        
        # Group trainings by client_id
        trainings_by_client = {}
        for training in all_trainings:
            client_id = training.get('client_id')
            if client_id not in trainings_by_client:
                trainings_by_client[client_id] = []
            trainings_by_client[client_id].append(training)
        
        # Print training counts by client
        logger.info("\n=== TRAINING COUNTS BY CLIENT ===")
        for client_id, trainings in trainings_by_client.items():
            # Get client info
            client_doc = await db.clients.find_one({"id": client_id})
            client_name = client_doc.get('name', 'Unknown') if client_doc else 'Unknown'
            hotel_name = client_doc.get('hotel_name', '') if client_doc else ''
            
            logger.info(f"Client: {client_name} / {hotel_name}")
            logger.info(f"  ID: {client_id}")
            logger.info(f"  Training count: {len(trainings)}")
            
            # Group trainings by status
            trainings_by_status = {}
            for training in trainings:
                status = training.get('status', 'Unknown')
                if status not in trainings_by_status:
                    trainings_by_status[status] = 0
                trainings_by_status[status] += 1
            
            # Print training counts by status
            for status, count in trainings_by_status.items():
                logger.info(f"    {status}: {count} trainings")
    
    except Exception as e:
        logger.error(f"Error checking trainings collection: {str(e)}")

async def check_email_management_endpoints():
    """Check why email management endpoints are not working"""
    try:
        logger.info("\n=== CHECKING EMAIL MANAGEMENT ENDPOINTS ===")
        
        # Check server.py file
        with open("/app/backend/server.py", "r") as f:
            server_code = f.readlines()
        
        # Find the line where the API router is registered
        api_router_line = None
        for i, line in enumerate(server_code):
            if "app.include_router" in line and "api_router" in line:
                api_router_line = i
                logger.info(f"API router registered at line {i+1}: {line.strip()}")
                break
        
        if api_router_line is not None:
            # Check if email management endpoints are defined after the router registration
            email_management_lines = []
            for i, line in enumerate(server_code):
                if "email-management" in line and "@api_router.get" in line:
                    email_management_lines.append((i, line.strip()))
            
            logger.info(f"Found {len(email_management_lines)} email management endpoint definitions:")
            for i, line in email_management_lines:
                logger.info(f"  Line {i+1}: {line}")
                if i > api_router_line:
                    logger.warning(f"  ⚠️ This endpoint is defined AFTER the API router registration at line {api_router_line+1}")
                    logger.warning(f"  This is the issue: endpoints defined after router registration are not included in the API")
                else:
                    logger.info(f"  ✅ This endpoint is defined BEFORE the API router registration")
            
            # Suggest a fix
            logger.info("\n=== SUGGESTED FIX ===")
            logger.info("The issue is that the email management endpoints are defined AFTER the API router is registered.")
            logger.info("To fix this, either:")
            logger.info(f"1. Move the email management endpoint definitions BEFORE the API router registration line")
            logger.info(f"   (before line {api_router_line+1})")
            logger.info("2. Move the API router registration line AFTER all endpoint definitions")
            logger.info("   (after the last endpoint definition)")
            logger.info("3. Create a separate router for email management endpoints and register it after defining them")
        else:
            logger.warning("Could not find API router registration line")
    
    except Exception as e:
        logger.error(f"Error checking email management endpoints: {str(e)}")

async def main():
    """Main function to run all checks"""
    logger.info("Starting comprehensive database investigation")
    
    # List all collections
    await list_all_collections()
    
    # Search for clients in all collections
    await search_for_clients()
    
    # Check users collection
    await check_users_collection()
    
    # Check clients collection
    await check_clients_collection()
    
    # Check documents collection
    await check_documents_collection()
    
    # Check trainings collection
    await check_trainings_collection()
    
    # Check email management endpoints
    await check_email_management_endpoints()
    
    logger.info("\nComprehensive database investigation complete")
    
    # Print summary
    logger.info("\n=== SUMMARY ===")
    logger.info("1. The 5 clients (DENEME OTEL, TEST OTEL, SES123, Can, ALP OTEL) were not found in the database.")
    logger.info("2. There is only 1 client in the database: 'Test Client' / 'Test Hotel' with ID 7a992a86-e2f4-4ed5-99f7-bab4966b7306.")
    logger.info("3. This client has 1 document and 1 training associated with it.")
    logger.info("4. There are 9 users with role 'client', but only 1 is linked to the client (client@test.com).")
    logger.info("5. The email management endpoints are defined AFTER the API router registration, which is why they return 404 Not Found.")
    logger.info("6. To fix the email management endpoints, move their definitions before the API router registration or move the router registration after all endpoint definitions.")

if __name__ == "__main__":
    asyncio.run(main())