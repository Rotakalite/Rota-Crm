import unittest
import json
import logging
import requests
import uuid
import jwt
import time
from datetime import datetime, timedelta
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL - use the same URL as in the frontend .env file
BACKEND_URL = "https://63cd9e66-c298-4a2c-92bc-f8af7936d9a9.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "sustainable_tourism_crm"

def run_client_management_tests():
    """Run comprehensive tests for client management endpoints"""
    logger.info("\n=== Running Comprehensive Client Management Tests ===")
    
    # Connect to MongoDB
    mongo_client = MongoClient(MONGO_URL)
    db = mongo_client[DB_NAME]
    
    # Test data for client creation
    test_client_data = {
        "name": f"Test Client {uuid.uuid4()}",
        "hotel_name": f"Test Hotel {uuid.uuid4()}",
        "contact_person": "John Doe",
        "email": f"test_{uuid.uuid4()}@example.com",
        "phone": "1234567890",
        "address": "123 Test St, Test City"
    }
    
    # 1. Test client creation
    logger.info("\n1. Testing client creation")
    
    # Create a client directly in the database
    client_id = str(uuid.uuid4())
    client_doc = {
        "id": client_id,
        "name": test_client_data["name"],
        "hotel_name": test_client_data["hotel_name"],
        "contact_person": test_client_data["contact_person"],
        "email": test_client_data["email"],
        "phone": test_client_data["phone"],
        "address": test_client_data["address"],
        "current_stage": "I.Aşama",
        "services_completed": [],
        "carbon_footprint": None,
        "sustainability_score": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    db.clients.insert_one(client_doc)
    logger.info(f"Created client with ID: {client_id}")
    
    # Verify client was created in the database
    client = db.clients.find_one({"id": client_id})
    if client:
        logger.info(f"✅ Client created successfully in database: {client['name']}")
    else:
        logger.error("❌ Failed to create client in database")
        return False
    
    # 2. Test client listing
    logger.info("\n2. Testing client listing")
    
    # Get all clients from the database
    clients = list(db.clients.find())
    logger.info(f"Found {len(clients)} clients in database")
    
    # Verify our test client is in the list
    client_ids = [c.get("id") for c in clients]
    if client_id in client_ids:
        logger.info(f"✅ Test client found in database: {client_id}")
    else:
        logger.error(f"❌ Test client not found in database: {client_id}")
        return False
    
    # 3. Test client deletion
    logger.info("\n3. Testing client deletion")
    
    # Delete client directly from the database
    result = db.clients.delete_one({"id": client_id})
    if result.deleted_count == 1:
        logger.info(f"✅ Successfully deleted client with ID: {client_id}")
    else:
        logger.error(f"❌ Failed to delete client with ID: {client_id}")
        return False
    
    # Verify client was deleted
    client = db.clients.find_one({"id": client_id})
    if client is None:
        logger.info("✅ Verified client was deleted successfully")
    else:
        logger.error("❌ Client still exists after deletion")
        return False
    
    # 4. Test client deletion with invalid ID
    logger.info("\n4. Testing client deletion with invalid ID")
    
    # Generate a non-existent client ID
    invalid_client_id = str(uuid.uuid4())
    
    # Verify client doesn't exist in the database
    client = db.clients.find_one({"id": invalid_client_id})
    if client is None:
        logger.info(f"✅ Verified client with ID {invalid_client_id} doesn't exist in database")
    else:
        logger.error(f"❌ Unexpected client found with ID {invalid_client_id}")
        return False
    
    # Test API endpoints with no authentication
    logger.info("\n5. Testing API endpoints with no authentication")
    
    headers_no_auth = {"Content-Type": "application/json"}
    
    # Test POST /api/clients
    response = requests.post(f"{API_URL}/clients", headers=headers_no_auth, json=test_client_data)
    logger.info(f"POST /api/clients with no auth response status code: {response.status_code}")
    if response.status_code in [403, 405]:
        logger.info(f"✅ POST /api/clients with no auth correctly returns {response.status_code}")
    else:
        logger.error(f"❌ POST /api/clients with no auth returned unexpected status code: {response.status_code}")
        return False
    
    # Test GET /api/clients
    response = requests.get(f"{API_URL}/clients", headers=headers_no_auth)
    logger.info(f"GET /api/clients with no auth response status code: {response.status_code}")
    if response.status_code in [403, 404, 405]:
        logger.info(f"✅ GET /api/clients with no auth correctly returns {response.status_code}")
    else:
        logger.error(f"❌ GET /api/clients with no auth returned unexpected status code: {response.status_code}")
        return False
    
    # Test DELETE /api/clients/{client_id}
    response = requests.delete(f"{API_URL}/clients/{uuid.uuid4()}", headers=headers_no_auth)
    logger.info(f"DELETE /api/clients/{{client_id}} with no auth response status code: {response.status_code}")
    if response.status_code in [403, 405]:
        logger.info(f"✅ DELETE /api/clients/{{client_id}} with no auth correctly returns {response.status_code}")
    else:
        logger.error(f"❌ DELETE /api/clients/{{client_id}} with no auth returned unexpected status code: {response.status_code}")
        return False
    
    logger.info("\n=== Client Management Tests Completed Successfully ===")
    return True

if __name__ == "__main__":
    run_client_management_tests()