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

# API URL from environment
API_URL = "https://4aeb8cfa-61f1-4648-8b57-402bd2c9bfe3.preview.emergentagent.com/api"

# Test JWT tokens for different users
# These are sample tokens for testing - in a real scenario, you would generate these from Clerk
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
KAYA_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyX0tBWUEiLCJlbWFpbCI6ImluZm9Aa2F5YWthbGl0ZWRhbmlzbWFubGlrLmNvbSIsIm5hbWUiOiJLQVlBIFVzZXIifQ.signature"
CANO_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyX0NBTk8iLCJlbWFpbCI6ImNhbmVycGFsQGdtYWlsLmNvbSIsIm5hbWUiOiJDQU5PIFVzZXIifQ.signature"
NO_CLIENT_ID_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyX05PQ0xJRU5UIiwiZW1haWwiOiJub2NsaWVudEBleGFtcGxlLmNvbSIsIm5hbWUiOiJObyBDbGllbnQgVXNlciJ9.signature"
INVALID_TOKEN = "invalid.token.format"

class TestClientDataSecurity(unittest.TestCase):
    """Test class for client data security"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = API_URL
        self.admin_headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.kaya_client_headers = {"Authorization": f"Bearer {KAYA_CLIENT_TOKEN}"}
        self.cano_client_headers = {"Authorization": f"Bearer {CANO_CLIENT_TOKEN}"}
        self.no_client_id_headers = {"Authorization": f"Bearer {NO_CLIENT_ID_TOKEN}"}
        self.invalid_headers = {"Authorization": f"Bearer {INVALID_TOKEN}"}
    
    def test_admin_access_to_clients(self):
        """Test that admin users can see all clients"""
        logger.info("\n=== Testing admin access to clients ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.admin_headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if we get a 200 OK
            self.assertEqual(response.status_code, 200, "Admin should get 200 OK")
            
            data = response.json()
            self.assertIsInstance(data, list, "Response should be a list of clients")
            
            # Admin should see multiple clients
            self.assertGreaterEqual(len(data), 2, "Admin should see at least 2 clients")
            
            # Log client names for verification
            client_names = [client.get("name") for client in data]
            logger.info(f"Admin can see clients: {client_names}")
            
            # Verify that both KAYA and CANO clients are visible
            kaya_found = any("KAYA" in client.get("name", "") for client in data)
            cano_found = any("CANO" in client.get("name", "") for client in data)
            
            self.assertTrue(kaya_found, "Admin should see KAYA client")
            self.assertTrue(cano_found, "Admin should see CANO client")
            
            logger.info("✅ Admin can see all clients as expected")
            
        except Exception as e:
            logger.error(f"❌ Error testing admin access to clients: {str(e)}")
            raise
    
    def test_kaya_client_access(self):
        """Test that KAYA client user can only see KAYA client data"""
        logger.info("\n=== Testing KAYA client access ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.kaya_client_headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if we get a 200 OK
            self.assertEqual(response.status_code, 200, "KAYA client should get 200 OK")
            
            data = response.json()
            self.assertIsInstance(data, list, "Response should be a list of clients")
            
            # KAYA client should see exactly 1 client (their own)
            self.assertEqual(len(data), 1, "KAYA client should see exactly 1 client")
            
            # Log client name for verification
            client_name = data[0].get("name")
            logger.info(f"KAYA client can see client: {client_name}")
            
            # Verify that only KAYA client is visible
            self.assertIn("KAYA", client_name, "KAYA client should only see KAYA client")
            
            logger.info("✅ KAYA client can only see their own client data")
            
        except Exception as e:
            logger.error(f"❌ Error testing KAYA client access: {str(e)}")
            raise
    
    def test_cano_client_access(self):
        """Test that CANO client user can only see CANO client data"""
        logger.info("\n=== Testing CANO client access ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.cano_client_headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if we get a 200 OK
            self.assertEqual(response.status_code, 200, "CANO client should get 200 OK")
            
            data = response.json()
            self.assertIsInstance(data, list, "Response should be a list of clients")
            
            # CANO client should see exactly 1 client (their own)
            self.assertEqual(len(data), 1, "CANO client should see exactly 1 client")
            
            # Log client name for verification
            client_name = data[0].get("name")
            logger.info(f"CANO client can see client: {client_name}")
            
            # Verify that only CANO client is visible
            self.assertIn("CANO", client_name, "CANO client should only see CANO client")
            
            logger.info("✅ CANO client can only see their own client data")
            
        except Exception as e:
            logger.error(f"❌ Error testing CANO client access: {str(e)}")
            raise
    
    def test_client_without_client_id(self):
        """Test that client users without client_id get proper error response"""
        logger.info("\n=== Testing client without client_id ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.no_client_id_headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if we get a 403 Forbidden
            self.assertEqual(response.status_code, 403, "Client without client_id should get 403 Forbidden")
            
            error_data = response.json()
            self.assertIn("detail", error_data, "Response should include error detail")
            
            # Verify error message
            self.assertIn("not properly linked", error_data.get("detail", ""), 
                         "Error should indicate client user is not properly linked to a client")
            
            logger.info(f"✅ Client without client_id gets proper error: {error_data.get('detail')}")
            
        except Exception as e:
            logger.error(f"❌ Error testing client without client_id: {str(e)}")
            raise
    
    def test_invalid_token(self):
        """Test that invalid tokens get proper error response"""
        logger.info("\n=== Testing invalid token ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.invalid_headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if we get a 401 Unauthorized
            self.assertEqual(response.status_code, 401, "Invalid token should get 401 Unauthorized")
            
            error_data = response.json()
            self.assertIn("detail", error_data, "Response should include error detail")
            
            logger.info(f"✅ Invalid token gets proper error: {error_data.get('detail')}")
            
        except Exception as e:
            logger.error(f"❌ Error testing invalid token: {str(e)}")
            raise
    
    def test_no_token(self):
        """Test that no token gets proper error response"""
        logger.info("\n=== Testing no token ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if we get a 401 Unauthorized or 403 Forbidden
            self.assertIn(response.status_code, [401, 403], "No token should get 401 Unauthorized or 403 Forbidden")
            
            error_data = response.json()
            self.assertIn("detail", error_data, "Response should include error detail")
            
            logger.info(f"✅ No token gets proper error: {error_data.get('detail')}")
            
        except Exception as e:
            logger.error(f"❌ Error testing no token: {str(e)}")
            raise

def run_client_security_tests():
    """Run client data security tests"""
    logger.info("Starting client data security tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add client data security tests
    suite.addTest(TestClientDataSecurity("test_admin_access_to_clients"))
    suite.addTest(TestClientDataSecurity("test_kaya_client_access"))
    suite.addTest(TestClientDataSecurity("test_cano_client_access"))
    suite.addTest(TestClientDataSecurity("test_client_without_client_id"))
    suite.addTest(TestClientDataSecurity("test_invalid_token"))
    suite.addTest(TestClientDataSecurity("test_no_token"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Client Data Security Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All client data security tests PASSED")
        return True
    else:
        logger.error("Some client data security tests FAILED")
        return False

if __name__ == "__main__":
    run_client_security_tests()