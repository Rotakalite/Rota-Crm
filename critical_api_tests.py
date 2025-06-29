import unittest
import json
import logging
import requests
import os
import io
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestCriticalAPIEndpoints(unittest.TestCase):
    """Test class for critical API endpoints that were failing"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = "https://ddbdf62a-0dc7-4cf4-b9a6-6dc3e3277ae1.preview.emergentagent.com/api"
        self.headers_valid = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        
        # Test user data for registration
        self.test_user = {
            "clerk_user_id": f"user_{uuid.uuid4()}",
            "email": f"test_{uuid.uuid4()}@example.com",
            "name": "Test User",
            "role": "client"
        }
    
    def test_auth_register_endpoint(self):
        """Test the /api/auth/register endpoint"""
        logger.info("\n=== Testing /api/auth/register endpoint ===")
        
        url = f"{self.api_url}/auth/register"
        
        try:
            # Test with valid data
            logger.info("Testing with valid data...")
            response = requests.post(url, json=self.test_user)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Should get 200 OK or 201 Created
            self.assertIn(response.status_code, [200, 201], "Register endpoint should return 200 OK or 201 Created")
            
            # Verify response format
            data = response.json()
            self.assertIn("id", data, "Response should include 'id' field")
            self.assertIn("clerk_user_id", data, "Response should include 'clerk_user_id' field")
            self.assertIn("email", data, "Response should include 'email' field")
            self.assertIn("name", data, "Response should include 'name' field")
            self.assertIn("role", data, "Response should include 'role' field")
            
            # Verify the returned user data matches what we sent
            self.assertEqual(data["clerk_user_id"], self.test_user["clerk_user_id"], "clerk_user_id should match")
            self.assertEqual(data["email"], self.test_user["email"], "email should match")
            self.assertEqual(data["name"], self.test_user["name"], "name should match")
            self.assertEqual(data["role"], self.test_user["role"], "role should match")
            
            logger.info("✅ Auth register endpoint test passed")
        except Exception as e:
            logger.error(f"❌ Error testing auth register endpoint: {str(e)}")
            raise
    
    def test_stats_endpoint(self):
        """Test the /api/stats endpoint"""
        logger.info("\n=== Testing /api/stats endpoint ===")
        
        url = f"{self.api_url}/stats"
        
        try:
            # Test with valid token
            logger.info("Testing with valid token...")
            response = requests.get(url, headers=self.headers_valid)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check if we get a 200 OK or 401 Unauthorized (not 403 Forbidden)
            self.assertIn(response.status_code, [200, 401], "Stats endpoint should return 200 OK or 401 Unauthorized")
            self.assertNotEqual(response.status_code, 403, "Should not receive 403 Forbidden")
            
            if response.status_code == 200:
                # Verify response format
                data = response.json()
                self.assertIn("total_clients", data, "Response should include 'total_clients' field")
                self.assertIn("stage_distribution", data, "Response should include 'stage_distribution' field")
                self.assertIn("total_documents", data, "Response should include 'total_documents' field")
                self.assertIn("total_trainings", data, "Response should include 'total_trainings' field")
                
                # Verify stage_distribution structure
                stage_distribution = data["stage_distribution"]
                self.assertIn("stage_1", stage_distribution, "stage_distribution should include 'stage_1' field")
                self.assertIn("stage_2", stage_distribution, "stage_distribution should include 'stage_2' field")
                self.assertIn("stage_3", stage_distribution, "stage_distribution should include 'stage_3' field")
                
                logger.info("✅ Stats endpoint test passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication check passed - received 401 Unauthorized")
            
            # Test with invalid token
            logger.info("Testing with invalid token...")
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Response status code with invalid token: {response.status_code}")
            
            # Should get 401 Unauthorized, not 403 Forbidden
            self.assertEqual(response.status_code, 401, "Should receive 401 Unauthorized with invalid token")
            error_data = response.json()
            self.assertIn("detail", error_data, "Error response should include 'detail' field")
            logger.info("✅ Invalid token test passed - received 401 Unauthorized")
        except Exception as e:
            logger.error(f"❌ Error testing stats endpoint: {str(e)}")
            raise
    
    def test_clients_endpoint(self):
        """Test the /api/clients endpoint"""
        logger.info("\n=== Testing /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            # Test with valid token
            logger.info("Testing with valid token...")
            response = requests.get(url, headers=self.headers_valid)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check if we get a 200 OK or 401 Unauthorized (not 403 Forbidden)
            self.assertIn(response.status_code, [200, 401], "Clients endpoint should return 200 OK or 401 Unauthorized")
            self.assertNotEqual(response.status_code, 403, "Should not receive 403 Forbidden")
            
            if response.status_code == 200:
                # Verify response format
                data = response.json()
                self.assertIsInstance(data, list, "Response should be a list of clients")
                
                # Check structure of clients if any exist
                if len(data) > 0:
                    client = data[0]
                    self.assertIn("id", client, "Client should have an id field")
                    self.assertIn("name", client, "Client should have a name field")
                    self.assertIn("hotel_name", client, "Client should have a hotel_name field")
                    self.assertIn("contact_person", client, "Client should have a contact_person field")
                    self.assertIn("email", client, "Client should have an email field")
                    self.assertIn("phone", client, "Client should have a phone field")
                    self.assertIn("address", client, "Client should have an address field")
                    self.assertIn("current_stage", client, "Client should have a current_stage field")
                    
                    logger.info(f"✅ Client data structure verified: {client.get('id')}")
                else:
                    logger.info("✅ No clients found (this may be expected)")
                
                logger.info("✅ Clients endpoint test passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication check passed - received 401 Unauthorized")
            
            # Test with invalid token
            logger.info("Testing with invalid token...")
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Response status code with invalid token: {response.status_code}")
            
            # Should get 401 Unauthorized, not 403 Forbidden
            self.assertEqual(response.status_code, 401, "Should receive 401 Unauthorized with invalid token")
            error_data = response.json()
            self.assertIn("detail", error_data, "Error response should include 'detail' field")
            logger.info("✅ Invalid token test passed - received 401 Unauthorized")
        except Exception as e:
            logger.error(f"❌ Error testing clients endpoint: {str(e)}")
            raise

def run_critical_api_endpoints_tests():
    """Run tests for critical API endpoints that were failing"""
    logger.info("Starting critical API endpoints tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add critical API endpoints tests
    suite.addTest(TestCriticalAPIEndpoints("test_auth_register_endpoint"))
    suite.addTest(TestCriticalAPIEndpoints("test_stats_endpoint"))
    suite.addTest(TestCriticalAPIEndpoints("test_clients_endpoint"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Critical API Endpoints Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All critical API endpoints tests PASSED")
        return True
    else:
        logger.error("Some critical API endpoints tests FAILED")
        return False

if __name__ == "__main__":
    run_critical_api_endpoints_tests()