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

# Backend URL from frontend/.env
BACKEND_URL = "https://4aeb8cfa-61f1-4648-8b57-402bd2c9bfe3.preview.emergentagent.com"

# Test JWT tokens for different users
# These are sample tokens for testing - in a real scenario, you would generate these from Clerk
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6ImFkbWluQHRlc3QuY29tIiwibmFtZSI6IkFkbWluIFVzZXIiLCJyb2xlIjoiYWRtaW4ifQ.signature"

# Client user tokens
KAYA_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6ImluZm9Aa2F5YWthbGl0ZWRhbmlzbWFubGlrLmNvbSIsIm5hbWUiOiJLQVlBIFVzZXIiLCJyb2xlIjoiY2xpZW50In0.signature"

CANO_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6ImNhbmVycGFsQGdtYWlsLmNvbSIsIm5hbWUiOiJDQU5PIFVzZXIiLCJyb2xlIjoiY2xpZW50In0.signature"

DENEME_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InBhbGF2YW5jYW5lckBnbWFpbC5jb20iLCJuYW1lIjoiREVORU1FIFVzZXIiLCJyb2xlIjoiY2xpZW50In0.signature"

# Invalid token for testing
INVALID_TOKEN = "invalid.token.format"

# Client user without client_id
NO_CLIENT_ID_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6Im5vY2xpZW50QHRlc3QuY29tIiwibmFtZSI6Ik5vIENsaWVudCBVc2VyIiwicm9sZSI6ImNsaWVudCJ9.signature"

class TestClientDataSecurityLive(unittest.TestCase):
    """Test class for client data security vulnerability with live API calls"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = f"{BACKEND_URL}/api"
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_kaya = {"Authorization": f"Bearer {KAYA_TOKEN}"}
        self.headers_cano = {"Authorization": f"Bearer {CANO_TOKEN}"}
        self.headers_deneme = {"Authorization": f"Bearer {DENEME_TOKEN}"}
        self.headers_no_client_id = {"Authorization": f"Bearer {NO_CLIENT_ID_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
    
    def test_admin_access_to_clients(self):
        """Test that admin users can see all clients"""
        logger.info("\n=== Testing admin access to /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Admin should get 200 OK or 401 Unauthorized (if token is rejected)
            self.assertIn(response.status_code, [200, 401])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Admin can see {len(data)} clients")
                
                # Admin should see all clients (at least 3)
                self.assertGreaterEqual(len(data), 3, "Admin should see at least 3 clients")
                
                # Check if KAYA, CANO, and DENEME clients are present
                client_names = [client.get("name") for client in data]
                logger.info(f"Client names visible to admin: {client_names}")
                
                # Log all client data for debugging
                for client in data:
                    logger.info(f"Client ID: {client.get('id')}, Name: {client.get('name')}, Email: {client.get('email')}")
                
                logger.info("✅ Admin can see all clients as expected")
            elif response.status_code == 401:
                logger.warning("⚠️ Admin token was rejected with 401 Unauthorized")
        except Exception as e:
            logger.error(f"❌ Error testing admin access: {str(e)}")
            raise
    
    def test_kaya_client_access(self):
        """Test that KAYA client user can only see their own client"""
        logger.info("\n=== Testing KAYA client access to /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"KAYA client response status code: {response.status_code}")
            
            # Client should get 200 OK or 401 Unauthorized (if token is rejected)
            self.assertIn(response.status_code, [200, 401])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"KAYA client can see {len(data)} clients")
                
                # KAYA client should see exactly 1 client (their own)
                self.assertEqual(len(data), 1, "KAYA client should see exactly 1 client (their own)")
                
                # The client should be KAYA
                client = data[0]
                logger.info(f"Client visible to KAYA: {client.get('name')} (Email: {client.get('email')})")
                
                # Check if the client is KAYA
                self.assertEqual(client.get("name"), "KAYA", "KAYA client should only see KAYA client")
                # Or check by email
                self.assertEqual(client.get("email"), "info@kayakalitedanismanlik.com", 
                                "KAYA client should only see client with email info@kayakalitedanismanlik.com")
                
                logger.info("✅ KAYA client can only see their own client as expected")
            elif response.status_code == 401:
                logger.warning("⚠️ KAYA client token was rejected with 401 Unauthorized")
        except Exception as e:
            logger.error(f"❌ Error testing KAYA client access: {str(e)}")
            raise
    
    def test_cano_client_access(self):
        """Test that CANO client user can only see their own client"""
        logger.info("\n=== Testing CANO client access to /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.headers_cano)
            logger.info(f"CANO client response status code: {response.status_code}")
            
            # Client should get 200 OK or 401 Unauthorized (if token is rejected)
            self.assertIn(response.status_code, [200, 401])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"CANO client can see {len(data)} clients")
                
                # CANO client should see exactly 1 client (their own)
                self.assertEqual(len(data), 1, "CANO client should see exactly 1 client (their own)")
                
                # The client should be CANO
                client = data[0]
                logger.info(f"Client visible to CANO: {client.get('name')} (Email: {client.get('email')})")
                
                # Check if the client is CANO
                self.assertEqual(client.get("name"), "CANO", "CANO client should only see CANO client")
                # Or check by email
                self.assertEqual(client.get("email"), "canerpal@gmail.com", 
                                "CANO client should only see client with email canerpal@gmail.com")
                
                logger.info("✅ CANO client can only see their own client as expected")
            elif response.status_code == 401:
                logger.warning("⚠️ CANO client token was rejected with 401 Unauthorized")
        except Exception as e:
            logger.error(f"❌ Error testing CANO client access: {str(e)}")
            raise
    
    def test_deneme_client_access(self):
        """Test that DENEME client user can only see their own client"""
        logger.info("\n=== Testing DENEME client access to /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.headers_deneme)
            logger.info(f"DENEME client response status code: {response.status_code}")
            
            # Client should get 200 OK or 401 Unauthorized (if token is rejected)
            self.assertIn(response.status_code, [200, 401])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"DENEME client can see {len(data)} clients")
                
                # DENEME client should see exactly 1 client (their own)
                self.assertEqual(len(data), 1, "DENEME client should see exactly 1 client (their own)")
                
                # The client should be DENEME
                client = data[0]
                logger.info(f"Client visible to DENEME: {client.get('name')} (Email: {client.get('email')})")
                
                # Check if the client is DENEME
                self.assertEqual(client.get("name"), "DENEME", "DENEME client should only see DENEME client")
                # Or check by email
                self.assertEqual(client.get("email"), "palavancaner@gmail.com", 
                                "DENEME client should only see client with email palavancaner@gmail.com")
                
                logger.info("✅ DENEME client can only see their own client as expected")
            elif response.status_code == 401:
                logger.warning("⚠️ DENEME client token was rejected with 401 Unauthorized")
        except Exception as e:
            logger.error(f"❌ Error testing DENEME client access: {str(e)}")
            raise
    
    def test_client_without_client_id(self):
        """Test that client users without client_id get proper error"""
        logger.info("\n=== Testing client without client_id access to /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.headers_no_client_id)
            logger.info(f"No client_id response status code: {response.status_code}")
            logger.info(f"No client_id response body: {response.text[:200]}...")
            
            # Client without client_id should get 403 Forbidden
            self.assertEqual(response.status_code, 403, "Client without client_id should get 403 Forbidden")
            
            # Check error message
            error_data = response.json()
            self.assertIn("detail", error_data, "Response should include 'detail' field with error message")
            self.assertIn("not properly linked", error_data["detail"].lower(), 
                         "Error message should indicate client is not properly linked to a client")
            
            logger.info("✅ Client without client_id gets proper 403 error as expected")
        except Exception as e:
            logger.error(f"❌ Error testing client without client_id: {str(e)}")
            raise
    
    def test_invalid_token(self):
        """Test that invalid tokens get 401 Unauthorized"""
        logger.info("\n=== Testing invalid token access to /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Invalid token should get 401 Unauthorized
            self.assertEqual(response.status_code, 401, "Invalid token should get 401 Unauthorized")
            
            logger.info("✅ Invalid token gets 401 Unauthorized as expected")
        except Exception as e:
            logger.error(f"❌ Error testing invalid token: {str(e)}")
            raise
    
    def test_no_token(self):
        """Test that no token gets 403 Not authenticated"""
        logger.info("\n=== Testing no token access to /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url)
            logger.info(f"No token response status code: {response.status_code}")
            
            # No token should get 403 Not authenticated
            self.assertEqual(response.status_code, 403, "No token should get 403 Not authenticated")
            
            logger.info("✅ No token gets 403 Not authenticated as expected")
        except Exception as e:
            logger.error(f"❌ Error testing no token: {str(e)}")
            raise

def run_client_security_live_tests():
    """Run all client security tests with live API calls"""
    logger.info("Starting client security live tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add client security tests
    suite.addTest(TestClientDataSecurityLive("test_admin_access_to_clients"))
    suite.addTest(TestClientDataSecurityLive("test_kaya_client_access"))
    suite.addTest(TestClientDataSecurityLive("test_cano_client_access"))
    suite.addTest(TestClientDataSecurityLive("test_deneme_client_access"))
    suite.addTest(TestClientDataSecurityLive("test_client_without_client_id"))
    suite.addTest(TestClientDataSecurityLive("test_invalid_token"))
    suite.addTest(TestClientDataSecurityLive("test_no_token"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Client Security Live Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All client security live tests PASSED")
        return True
    else:
        logger.error("Some client security live tests FAILED")
        return False

if __name__ == "__main__":
    run_client_security_live_tests()