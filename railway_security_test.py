import unittest
import json
import logging
import requests
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT tokens for client users
# These are sample tokens for testing different client users
KAYA_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
CANO_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0FOT19DTElFTlRfMDAxIiwiZW1haWwiOiJjYW5lcnBhbEBnbWFpbC5jb20iLCJuYW1lIjoiQ0FOTyBDbGllbnQifQ.signature"
DENEME_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfREVORU1FX0NMSUVOVF8wMDEiLCJlbWFpbCI6InBhbGF2YW5jYW5lckBnbWFpbC5jb20iLCJuYW1lIjoiREVORU1FIENsaWVudCJ9.signature"
NO_CLIENT_ID_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfTk9fQ0xJRU5UX0lEIiwiZW1haWwiOiJub2NsaWVudGlkQGV4YW1wbGUuY29tIiwibmFtZSI6IlVzZXIgV2l0aG91dCBDbGllbnQgSUQifQ.signature"
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestRailwayBackendSecurity(unittest.TestCase):
    """Test class for Railway backend security fix"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_kaya = {"Authorization": f"Bearer {KAYA_CLIENT_TOKEN}"}
        self.headers_cano = {"Authorization": f"Bearer {CANO_CLIENT_TOKEN}"}
        self.headers_deneme = {"Authorization": f"Bearer {DENEME_CLIENT_TOKEN}"}
        self.headers_no_client_id = {"Authorization": f"Bearer {NO_CLIENT_ID_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_admin_can_see_all_clients(self):
        """Test that admin users can see all clients"""
        logger.info("\n=== Testing admin access to /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Admin should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list of clients
            data = response.json()
            self.assertIsInstance(data, list)
            
            # Admin should see all clients (at least 2)
            self.assertGreaterEqual(len(data), 2, "Admin should see at least 2 clients")
            
            # Log the clients found
            client_names = [client.get("name") for client in data]
            logger.info(f"Admin can see clients: {client_names}")
            
            logger.info("✅ Admin can see all clients test passed")
        except Exception as e:
            logger.error(f"❌ Error testing admin access: {str(e)}")
            raise
    
    def test_client_users_can_only_see_own_client(self):
        """Test that client users can only see their own client data"""
        logger.info("\n=== Testing client user access to /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        # Test KAYA client
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"KAYA client response status code: {response.status_code}")
            
            # Client should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list with exactly 1 client
            data = response.json()
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1, "Client user should see exactly 1 client (their own)")
            
            # The client should be KAYA
            client = data[0]
            self.assertIn("name", client)
            logger.info(f"KAYA client can see: {client.get('name')}")
            
            # Verify it's their own client (should contain "KAYA" in the name)
            self.assertIn("KAYA", client.get("name", ""), "KAYA client should only see KAYA client data")
            
            logger.info("✅ KAYA client can only see own client test passed")
        except Exception as e:
            logger.error(f"❌ Error testing KAYA client access: {str(e)}")
            raise
        
        # Test CANO client
        try:
            response = requests.get(url, headers=self.headers_cano)
            logger.info(f"CANO client response status code: {response.status_code}")
            
            # Client should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list with exactly 1 client
            data = response.json()
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1, "Client user should see exactly 1 client (their own)")
            
            # The client should be CANO
            client = data[0]
            self.assertIn("name", client)
            logger.info(f"CANO client can see: {client.get('name')}")
            
            # Verify it's their own client (should contain "CANO" in the name)
            self.assertIn("CANO", client.get("name", ""), "CANO client should only see CANO client data")
            
            logger.info("✅ CANO client can only see own client test passed")
        except Exception as e:
            logger.error(f"❌ Error testing CANO client access: {str(e)}")
            raise
    
    def test_client_user_without_client_id_gets_403(self):
        """Test that client users without client_id get 403 Forbidden"""
        logger.info("\n=== Testing client user without client_id access to /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.headers_no_client_id)
            logger.info(f"No client_id user response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            # Error message should indicate client user not properly linked to a client
            error_data = response.json()
            self.assertIn("detail", error_data)
            self.assertIn("Client user not properly linked to a client", error_data.get("detail", ""))
            
            logger.info("✅ Client user without client_id gets 403 test passed")
        except Exception as e:
            logger.error(f"❌ Error testing client user without client_id access: {str(e)}")
            raise
    
    def test_invalid_token_gets_401(self):
        """Test that invalid tokens get 401 Unauthorized"""
        logger.info("\n=== Testing invalid token access to /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ Invalid token gets 401 test passed")
        except Exception as e:
            logger.error(f"❌ Error testing invalid token access: {str(e)}")
            raise
    
    def test_no_token_gets_403(self):
        """Test that no token gets 403 Not authenticated"""
        logger.info("\n=== Testing no token access to /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No token response status code: {response.status_code}")
            
            # Should get 403 Not authenticated
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ No token gets 403 test passed")
        except Exception as e:
            logger.error(f"❌ Error testing no token access: {str(e)}")
            raise

def run_tests():
    """Run all Railway backend security tests"""
    logger.info("Starting Railway backend security tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add client security tests
    suite.addTest(TestRailwayBackendSecurity("test_admin_can_see_all_clients"))
    suite.addTest(TestRailwayBackendSecurity("test_client_users_can_only_see_own_client"))
    suite.addTest(TestRailwayBackendSecurity("test_client_user_without_client_id_gets_403"))
    suite.addTest(TestRailwayBackendSecurity("test_invalid_token_gets_401"))
    suite.addTest(TestRailwayBackendSecurity("test_no_token_gets_403"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Railway Backend Security Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All Railway backend security tests PASSED")
        return True
    else:
        logger.error("Some Railway backend security tests FAILED")
        return False

if __name__ == "__main__":
    run_tests()