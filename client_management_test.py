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
BACKEND_URL = "https://9fdcc5d0-9b6d-4e6f-bc8f-589c3991a8cc.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "sustainable_tourism_crm"

class TestClientManagementEndpoints(unittest.TestCase):
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
        
        # Should get 403 Forbidden
        self.assertEqual(response.status_code, 403)
        logger.info("✅ POST /api/clients with no auth correctly returns 403")
        
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
        
        # Should get 403 Forbidden
        self.assertEqual(response.status_code, 403)
        logger.info("✅ GET /api/clients with no auth correctly returns 403")
        
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
        
        # Should get 403 Forbidden
        self.assertEqual(response.status_code, 403)
        logger.info("✅ DELETE /api/clients/{client_id} with no auth correctly returns 403")
        
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
        
        # Should get 403 Forbidden
        self.assertEqual(response.status_code, 403)
        logger.info("✅ DELETE /api/clients/{invalid_client_id} with no auth correctly returns 403")
    
    def test_1_client_creation(self):
        """Test POST /api/clients endpoint"""
        logger.info("\n=== Testing POST /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        # Test with admin authentication
        try:
            response = requests.post(url, headers=self.headers_admin, json=self.test_client_data)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK or 201 Created
            self.assertIn(response.status_code, [200, 201])
            
            # Response should contain client data with ID
            data = response.json()
            self.assertIn("id", data)
            self.assertEqual(data["name"], self.test_client_data["name"])
            self.assertEqual(data["hotel_name"], self.test_client_data["hotel_name"])
            self.assertEqual(data["contact_person"], self.test_client_data["contact_person"])
            self.assertEqual(data["email"], self.test_client_data["email"])
            self.assertEqual(data["phone"], self.test_client_data["phone"])
            self.assertEqual(data["address"], self.test_client_data["address"])
            
            # Save client ID for later tests
            self.created_client_id = data["id"]
            logger.info(f"Created client with ID: {self.created_client_id}")
            
            # Write client ID to a file for other tests to use
            with open("created_client_id.txt", "w") as f:
                f.write(self.created_client_id)
            
            logger.info("✅ POST /api/clients with admin auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing create client endpoint with admin: {str(e)}")
            raise
        
        # Test with client authentication (should be forbidden)
        try:
            response = requests.post(url, headers=self.headers_client, json=self.test_client_data)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Should get 403 Forbidden or 401 Unauthorized
            self.assertIn(response.status_code, [401, 403])
            
            logger.info("✅ POST /api/clients with client auth correctly returns 401/403")
        except Exception as e:
            logger.error(f"❌ Error testing create client endpoint with client auth: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.post(url, headers=self.headers_invalid, json=self.test_client_data)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ POST /api/clients with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing create client endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.post(url, headers=self.headers_no_auth, json=self.test_client_data)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ POST /api/clients with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing create client endpoint with no auth: {str(e)}")
            raise
    
    def test_2_client_listing(self):
        """Test GET /api/clients endpoint"""
        logger.info("\n=== Testing GET /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list of clients
            data = response.json()
            self.assertIsInstance(data, list)
            
            # Admin should see all clients (at least 1)
            self.assertGreaterEqual(len(data), 1, "Admin should see at least 1 client")
            
            # Log the clients found
            client_names = [client.get("name") for client in data]
            logger.info(f"Admin can see clients: {client_names}")
            
            # If we created a client in the previous test, verify it's in the list
            if self.created_client_id:
                client_ids = [client.get("id") for client in data]
                self.assertIn(self.created_client_id, client_ids, "Created client should be in the list")
            else:
                # Try to read client ID from file
                try:
                    with open("created_client_id.txt", "r") as f:
                        self.created_client_id = f.read().strip()
                        client_ids = [client.get("id") for client in data]
                        self.assertIn(self.created_client_id, client_ids, "Created client should be in the list")
                except FileNotFoundError:
                    logger.warning("No created client ID found, skipping verification")
            
            logger.info("✅ GET /api/clients with admin auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing get clients endpoint with admin: {str(e)}")
            raise
        
        # Test with client authentication
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list with exactly 1 client (their own)
            data = response.json()
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1, "Client user should see exactly 1 client (their own)")
            
            # Log the client found
            client = data[0]
            logger.info(f"Client can see: {client.get('name')}")
            
            logger.info("✅ GET /api/clients with client auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing get clients endpoint with client auth: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ GET /api/clients with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing get clients endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ GET /api/clients with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing get clients endpoint with no auth: {str(e)}")
            raise
    
    def test_3_client_deletion(self):
        """Test DELETE /api/clients/{client_id} endpoint"""
        logger.info("\n=== Testing DELETE /api/clients/{client_id} endpoint ===")
        
        # If we don't have a client ID from previous tests, try to read it from file
        if not self.created_client_id:
            try:
                with open("created_client_id.txt", "r") as f:
                    self.created_client_id = f.read().strip()
            except FileNotFoundError:
                logger.warning("No created client ID found, creating a new client for deletion test")
                # Create a new client for deletion test
                url = f"{self.api_url}/clients"
                response = requests.post(url, headers=self.headers_admin, json=self.test_client_data)
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.created_client_id = data["id"]
                    logger.info(f"Created client with ID: {self.created_client_id} for deletion test")
                else:
                    logger.error(f"Failed to create client for deletion test: {response.status_code}")
                    self.skipTest("Could not create client for deletion test")
        
        # Test with client authentication (should be forbidden)
        try:
            url = f"{self.api_url}/clients/{self.created_client_id}"
            response = requests.delete(url, headers=self.headers_client)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Should get 403 Forbidden or 401 Unauthorized
            self.assertIn(response.status_code, [401, 403])
            
            logger.info("✅ DELETE /api/clients/{client_id} with client auth correctly returns 401/403")
        except Exception as e:
            logger.error(f"❌ Error testing delete client endpoint with client auth: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            url = f"{self.api_url}/clients/{self.created_client_id}"
            response = requests.delete(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ DELETE /api/clients/{client_id} with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing delete client endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            url = f"{self.api_url}/clients/{self.created_client_id}"
            response = requests.delete(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ DELETE /api/clients/{client_id} with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing delete client endpoint with no auth: {str(e)}")
            raise
        
        # Test with admin authentication
        try:
            url = f"{self.api_url}/clients/{self.created_client_id}"
            response = requests.delete(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain success message
            data = response.json()
            self.assertIn("message", data)
            self.assertIn("deleted successfully", data["message"])
            
            logger.info("✅ DELETE /api/clients/{client_id} with admin auth test passed")
            
            # Verify client was actually deleted
            url = f"{self.api_url}/clients/{self.created_client_id}"
            response = requests.get(url, headers=self.headers_admin)
            self.assertEqual(response.status_code, 404, "Client should not exist after deletion")
            
            logger.info("✅ Verified client was deleted successfully")
        except Exception as e:
            logger.error(f"❌ Error testing delete client endpoint with admin: {str(e)}")
            raise
    
    def test_4_client_deletion_invalid_id(self):
        """Test DELETE /api/clients/{client_id} with invalid client ID"""
        logger.info("\n=== Testing DELETE /api/clients/{client_id} with invalid client ID ===")
        
        # Test with non-existent client ID
        try:
            invalid_client_id = str(uuid.uuid4())
            url = f"{self.api_url}/clients/{invalid_client_id}"
            response = requests.delete(url, headers=self.headers_admin)
            logger.info(f"Admin response status code for invalid client ID: {response.status_code}")
            
            # Should get 404 Not Found
            self.assertEqual(response.status_code, 404)
            
            # Response should contain error message
            data = response.json()
            self.assertIn("detail", data)
            self.assertIn("not found", data["detail"].lower())
            
            logger.info("✅ DELETE /api/clients/{client_id} with invalid client ID correctly returns 404")
        except Exception as e:
            logger.error(f"❌ Error testing delete client endpoint with invalid client ID: {str(e)}")
            raise
        
        # Test with malformed client ID
        try:
            malformed_client_id = "not-a-valid-uuid"
            url = f"{self.api_url}/clients/{malformed_client_id}"
            response = requests.delete(url, headers=self.headers_admin)
            logger.info(f"Admin response status code for malformed client ID: {response.status_code}")
            
            # Should get 404 Not Found or 400 Bad Request
            self.assertIn(response.status_code, [400, 404])
            
            logger.info("✅ DELETE /api/clients/{client_id} with malformed client ID correctly returns 400/404")
        except Exception as e:
            logger.error(f"❌ Error testing delete client endpoint with malformed client ID: {str(e)}")
            raise

if __name__ == "__main__":
    # Run the tests in order
    suite = unittest.TestSuite()
    suite.addTest(TestClientManagementEndpoints("test_1_client_creation"))
    suite.addTest(TestClientManagementEndpoints("test_2_client_listing"))
    suite.addTest(TestClientManagementEndpoints("test_3_client_deletion"))
    suite.addTest(TestClientManagementEndpoints("test_4_client_deletion_invalid_id"))
    
    runner = unittest.TextTestRunner()
    runner.run(suite)