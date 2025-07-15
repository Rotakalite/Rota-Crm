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

# Backend URL
BACKEND_URL = "https://7397d81a-245d-49b9-a61b-31977569672c.preview.emergentagent.com/api"

# Test JWT token for authentication
TEST_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"

async def search_for_specific_clients():
    """Search for the 5 specific clients in the database"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Target clients to find
    target_clients = ["DENEME OTEL", "TEST OTEL", "SES123", "Can", "ALP OTEL"]
    
    # Search in clients collection
    logger.info("\n=== SEARCHING FOR CLIENTS IN CLIENTS COLLECTION ===")
    all_clients = await db.clients.find().to_list(length=None)
    logger.info(f"Found {len(all_clients)} clients in clients collection")
    
    found_in_clients = []
    for client_doc in all_clients:
        client_name = client_doc.get("name", "")
        hotel_name = client_doc.get("hotel_name", "")
        
        # Check if this client matches any of our targets
        for target in target_clients:
            if (target.lower() in client_name.lower() or 
                target.lower() in hotel_name.lower()):
                logger.info(f"Found target client in clients collection: {client_name} / {hotel_name}")
                logger.info(f"  ID: {client_doc.get('id')}")
                logger.info(f"  Contact: {client_doc.get('contact_person')}")
                logger.info(f"  Email: {client_doc.get('email')}")
                found_in_clients.append(client_doc)
                break
    
    # Search in users collection
    logger.info("\n=== SEARCHING FOR CLIENTS IN USERS COLLECTION ===")
    all_users = await db.users.find().to_list(length=None)
    logger.info(f"Found {len(all_users)} users in users collection")
    
    found_in_users = []
    for user_doc in all_users:
        user_name = user_doc.get("name", "")
        user_email = user_doc.get("email", "")
        
        # Check if this user matches any of our targets
        for target in target_clients:
            if (target.lower() in user_name.lower() or 
                target.lower() in user_email.lower()):
                logger.info(f"Found target client in users collection: {user_name} / {user_email}")
                logger.info(f"  ID: {user_doc.get('id')}")
                logger.info(f"  Role: {user_doc.get('role')}")
                logger.info(f"  Client ID: {user_doc.get('client_id')}")
                found_in_users.append(user_doc)
                break
    
    # If we didn't find any matches, list all clients and users
    if not found_in_clients and not found_in_users:
        logger.info("\n=== NO MATCHES FOUND, LISTING ALL CLIENTS ===")
        for i, client_doc in enumerate(all_clients):
            logger.info(f"CLIENT {i+1}:")
            logger.info(f"  Name: {client_doc.get('name')}")
            logger.info(f"  Hotel Name: {client_doc.get('hotel_name')}")
            logger.info(f"  ID: {client_doc.get('id')}")
            logger.info(f"  Contact: {client_doc.get('contact_person')}")
            logger.info(f"  Email: {client_doc.get('email')}")
        
        logger.info("\n=== LISTING ALL USERS ===")
        for i, user_doc in enumerate(all_users):
            if user_doc.get("role") == "client":
                logger.info(f"USER {i+1} (CLIENT):")
                logger.info(f"  Name: {user_doc.get('name')}")
                logger.info(f"  Email: {user_doc.get('email')}")
                logger.info(f"  ID: {user_doc.get('id')}")
                logger.info(f"  Client ID: {user_doc.get('client_id')}")
    
    return found_in_clients, found_in_users

async def check_documents_for_clients(client_ids):
    """Check documents for specific client IDs"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    logger.info("\n=== CHECKING DOCUMENTS FOR SPECIFIC CLIENTS ===")
    
    for client_id in client_ids:
        # Count documents
        doc_count = await db.documents.count_documents({"client_id": client_id})
        
        # Get client info
        client_doc = await db.clients.find_one({"id": client_id})
        client_name = client_doc.get("name", "Unknown") if client_doc else "Unknown"
        hotel_name = client_doc.get("hotel_name", "") if client_doc else ""
        
        logger.info(f"Client: {client_name} / {hotel_name}")
        logger.info(f"  ID: {client_id}")
        logger.info(f"  Document count: {doc_count}")
        
        # If there are documents, show some details
        if doc_count > 0:
            docs = await db.documents.find({"client_id": client_id}).to_list(length=5)
            logger.info(f"  Sample documents (up to 5):")
            for i, doc in enumerate(docs):
                logger.info(f"    Doc {i+1}: {doc.get('name')} - Type: {doc.get('document_type')}")

async def check_trainings_for_clients(client_ids):
    """Check trainings for specific client IDs"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    logger.info("\n=== CHECKING TRAININGS FOR SPECIFIC CLIENTS ===")
    
    for client_id in client_ids:
        # Count trainings
        training_count = await db.trainings.count_documents({"client_id": client_id})
        
        # Get client info
        client_doc = await db.clients.find_one({"id": client_id})
        client_name = client_doc.get("name", "Unknown") if client_doc else "Unknown"
        hotel_name = client_doc.get("hotel_name", "") if client_doc else ""
        
        logger.info(f"Client: {client_name} / {hotel_name}")
        logger.info(f"  ID: {client_id}")
        logger.info(f"  Training count: {training_count}")
        
        # If there are trainings, show some details
        if training_count > 0:
            trainings = await db.trainings.find({"client_id": client_id}).to_list(length=5)
            logger.info(f"  Sample trainings (up to 5):")
            for i, training in enumerate(trainings):
                logger.info(f"    Training {i+1}: {training.get('name')} - Status: {training.get('status')}")

def test_email_management_endpoints():
    """Test the email management endpoints"""
    logger.info("\n=== TESTING EMAIL MANAGEMENT ENDPOINTS ===")
    
    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}
    
    # Test clients-real endpoint
    logger.info("\n--- Testing /api/email-management/clients-real ---")
    url = f"{BACKEND_URL}/email-management/clients-real"
    try:
        response = requests.get(url, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response data: {json.dumps(data, indent=2)}")
        else:
            logger.info(f"Response text: {response.text}")
    except Exception as e:
        logger.error(f"Error testing clients-real endpoint: {str(e)}")
    
    # Test documents-real endpoint
    logger.info("\n--- Testing /api/email-management/documents-real ---")
    url = f"{BACKEND_URL}/email-management/documents-real"
    try:
        response = requests.get(url, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response data: {json.dumps(data, indent=2)}")
        else:
            logger.info(f"Response text: {response.text}")
    except Exception as e:
        logger.error(f"Error testing documents-real endpoint: {str(e)}")
    
    # Test trainings-real endpoint
    logger.info("\n--- Testing /api/email-management/trainings-real ---")
    url = f"{BACKEND_URL}/email-management/trainings-real"
    try:
        response = requests.get(url, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response data: {json.dumps(data, indent=2)}")
        else:
            logger.info(f"Response text: {response.text}")
    except Exception as e:
        logger.error(f"Error testing trainings-real endpoint: {str(e)}")

def check_api_router_registration():
    """Check the API router registration in server.py"""
    logger.info("\n=== CHECKING API ROUTER REGISTRATION ===")
    
    try:
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
                else:
                    logger.info(f"  ✅ This endpoint is defined BEFORE the API router registration")
        else:
            logger.warning("Could not find API router registration line")
    
    except Exception as e:
        logger.error(f"Error checking API router registration: {str(e)}")

async def main():
    """Main function to run all checks"""
    logger.info("Starting comprehensive client investigation")
    
    # Search for specific clients
    found_in_clients, found_in_users = await search_for_specific_clients()
    
    # Get all client IDs from both collections
    client_ids = [client.get("id") for client in found_in_clients]
    user_client_ids = [user.get("client_id") for user in found_in_users if user.get("client_id")]
    all_client_ids = list(set(client_ids + user_client_ids))
    
    # Check documents and trainings for these clients
    if all_client_ids:
        await check_documents_for_clients(all_client_ids)
        await check_trainings_for_clients(all_client_ids)
    else:
        logger.info("No client IDs found to check documents and trainings")
    
    # Test email management endpoints
    test_email_management_endpoints()
    
    # Check API router registration
    check_api_router_registration()
    
    logger.info("\nComprehensive client investigation complete")

if __name__ == "__main__":
    asyncio.run(main())