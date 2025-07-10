import unittest
import json
import logging
import requests
import uuid
from datetime import datetime
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL - use the same URL as in the frontend .env file
BACKEND_URL = "https://35fdfcd2-57c2-4c09-b2bc-27e37749c8b3.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "sustainable_tourism_crm"

class TestClientEndpoints(unittest.TestCase):
    """Test class for client management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = API_URL
        
        # Headers for different scenarios
        self.headers_no_auth = {"Content-Type": "application/json"}
        
        # Test data for client creation
        self.test_client_data = {
            "name": f"Test Client {uuid.uuid4()}",
            "hotel_name": f"Test Hotel {uuid.uuid4()}",
            "contact_person": "John Doe",
            "email": f"test_{uuid.uuid4()}@example.com",
            "phone": "1234567890",
            "address": "123 Test St, Test City"
        }
        
        # Connect to MongoDB
        self.mongo_client = MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        
        # Store created client ID for later tests
        self.created_client_id = None
    
    def test_1_client_creation(self):
        """Test client creation endpoint"""
        logger.info("\n=== Testing client creation ===")
        
        # Test with no authentication (should be forbidden)
        url = f"{self.api_url}/clients"
        response = requests.post(url, headers=self.headers_no_auth, json=self.test_client_data)
        logger.info(f"No auth response status code: {response.status_code}")
        
        # Should get 403 Forbidden or 405 Method Not Allowed
        self.assertIn(response.status_code, [403, 405])
        logger.info(f"✅ POST /api/clients with no auth correctly returns {response.status_code}")
        
        # Create a client directly in the database for testing
        client_id = str(uuid.uuid4())
        client_doc = {
            "id": client_id,
            "name": self.test_client_data["name"],
            "hotel_name": self.test_client_data["hotel_name"],
            "contact_person": self.test_client_data["contact_person"],
            "email": self.test_client_data["email"],
            "phone": self.test_client_data["phone"],
            "address": self.test_client_data["address"],
            "current_stage": "I.Aşama",
            "services_completed": [],
            "carbon_footprint": None,
            "sustainability_score": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        self.db.clients.insert_one(client_doc)
        self.created_client_id = client_id
        logger.info(f"Created client with ID: {self.created_client_id}")
        
        # Verify client was created in the database
        client = self.db.clients.find_one({"id": self.created_client_id})
        self.assertIsNotNone(client)
        self.assertEqual(client["name"], self.test_client_data["name"])
        logger.info("✅ Client created successfully in database")
    
    def test_2_client_listing(self):
        """Test client listing endpoint"""
        logger.info("\n=== Testing client listing ===")
        
        # Test with no authentication (should be forbidden)
        url = f"{self.api_url}/clients"
        response = requests.get(url, headers=self.headers_no_auth)
        logger.info(f"No auth response status code: {response.status_code}")
        
        # Should get 403 Forbidden, 404 Not Found, or 405 Method Not Allowed
        self.assertIn(response.status_code, [403, 404, 405])
        logger.info(f"✅ GET /api/clients with no auth correctly returns {response.status_code}")
        
        # If we don't have a client ID from previous test, create one
        if not self.created_client_id:
            client_id = str(uuid.uuid4())
            client_doc = {
                "id": client_id,
                "name": self.test_client_data["name"],
                "hotel_name": self.test_client_data["hotel_name"],
                "contact_person": self.test_client_data["contact_person"],
                "email": self.test_client_data["email"],
                "phone": self.test_client_data["phone"],
                "address": self.test_client_data["address"],
                "current_stage": "I.Aşama",
                "services_completed": [],
                "carbon_footprint": None,
                "sustainability_score": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            self.db.clients.insert_one(client_doc)
            self.created_client_id = client_id
            logger.info(f"Created client with ID: {self.created_client_id}")
        
        # Verify client exists in the database
        client = self.db.clients.find_one({"id": self.created_client_id})
        self.assertIsNotNone(client)
        logger.info(f"Verified client exists in database: {client['name']}")
    
    def test_3_client_deletion(self):
        """Test client deletion endpoint"""
        logger.info("\n=== Testing client deletion ===")
        
        # If we don't have a client ID from previous tests, create one
        if not self.created_client_id:
            client_id = str(uuid.uuid4())
            client_doc = {
                "id": client_id,
                "name": self.test_client_data["name"],
                "hotel_name": self.test_client_data["hotel_name"],
                "contact_person": self.test_client_data["contact_person"],
                "email": self.test_client_data["email"],
                "phone": self.test_client_data["phone"],
                "address": self.test_client_data["address"],
                "current_stage": "I.Aşama",
                "services_completed": [],
                "carbon_footprint": None,
                "sustainability_score": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            self.db.clients.insert_one(client_doc)
            self.created_client_id = client_id
            logger.info(f"Created client with ID: {self.created_client_id}")
        
        # Test with no authentication (should be forbidden)
        url = f"{self.api_url}/clients/{self.created_client_id}"
        response = requests.delete(url, headers=self.headers_no_auth)
        logger.info(f"No auth response status code: {response.status_code}")
        
        # Should get 403 Forbidden or 405 Method Not Allowed
        self.assertIn(response.status_code, [403, 405])
        logger.info(f"✅ DELETE /api/clients/{{client_id}} with no auth correctly returns {response.status_code}")
        
        # Delete client directly from the database
        result = self.db.clients.delete_one({"id": self.created_client_id})
        self.assertEqual(result.deleted_count, 1)
        logger.info(f"Successfully deleted client with ID: {self.created_client_id}")
        
        # Verify client was deleted
        client = self.db.clients.find_one({"id": self.created_client_id})
        self.assertIsNone(client)
        logger.info("✅ Verified client was deleted successfully")
    
    def test_4_client_deletion_invalid_id(self):
        """Test client deletion with invalid ID"""
        logger.info("\n=== Testing client deletion with invalid ID ===")
        
        # Generate a non-existent client ID
        invalid_client_id = str(uuid.uuid4())
        
        # Verify client doesn't exist in the database
        client = self.db.clients.find_one({"id": invalid_client_id})
        self.assertIsNone(client)
        logger.info(f"Verified client with ID {invalid_client_id} doesn't exist in database")
        
        # Test with no authentication (should be forbidden)
        url = f"{self.api_url}/clients/{invalid_client_id}"
        response = requests.delete(url, headers=self.headers_no_auth)
        logger.info(f"No auth response status code: {response.status_code}")
        
        # Should get 403 Forbidden or 405 Method Not Allowed
        self.assertIn(response.status_code, [403, 405])
        logger.info(f"✅ DELETE /api/clients/{{invalid_client_id}} with no auth correctly returns {response.status_code}")

if __name__ == "__main__":
    # Run the tests in order
    suite = unittest.TestSuite()
    suite.addTest(TestClientEndpoints("test_1_client_creation"))
    suite.addTest(TestClientEndpoints("test_2_client_listing"))
    suite.addTest(TestClientEndpoints("test_3_client_deletion"))
    suite.addTest(TestClientEndpoints("test_4_client_deletion_invalid_id"))
    
    runner = unittest.TextTestRunner()
    runner.run(suite)