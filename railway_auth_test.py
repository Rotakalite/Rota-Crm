import unittest
import requests
import logging
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data

class TestRailwayBackendAuth(unittest.TestCase):
    """Test class for Railway backend authentication issues"""
    
    def setUp(self):
        """Set up test environment"""
        # Use the Railway backend URL from frontend/.env
        self.api_url = "https://rota-crm-production.up.railway.app/api"
        self.headers_valid = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        
        # Create a client user with proper client_id
        self.client_user_token = VALID_JWT_TOKEN
        self.client_headers = {"Authorization": f"Bearer {self.client_user_token}"}
        
        # Create an admin user
        self.admin_user_token = VALID_JWT_TOKEN
        self.admin_headers = {"Authorization": f"Bearer {self.admin_user_token}"}
        
    def test_railway_clients_endpoint(self):
        """Test the /api/clients endpoint on Railway backend"""
        logger.info("\n=== Testing Railway backend /api/clients endpoint ===")
        
        # Test with client user token
        logger.info("Testing with client user token...")
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.client_headers)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:500]}...")
            
            # Check if we get a 200 OK, 401 Unauthorized, or 403 Forbidden
            # We want to understand why we're getting 403 instead of 401
            if response.status_code == 200:
                logger.info("✅ Authentication successful - received 200 OK")
                data = response.json()
                logger.info(f"Received {len(data)} clients")
                
                # Check if client user can see only their own client
                if len(data) > 1:
                    logger.warning("⚠️ Client user can see multiple clients - potential security issue")
                
            elif response.status_code == 401:
                logger.info("✅ Authentication failed correctly - received 401 Unauthorized")
                error_data = response.json()
                logger.info(f"Error detail: {error_data.get('detail', 'No detail provided')}")
                
            elif response.status_code == 403:
                logger.warning("⚠️ Received 403 Forbidden - investigating why")
                error_data = response.json()
                logger.info(f"Error detail: {error_data.get('detail', 'No detail provided')}")
                
                # This is the issue we're investigating - why 403 instead of 401?
                # Possible reasons:
                # 1. Token is valid but user doesn't have client_id
                # 2. Token is valid but user's client_id doesn't exist in database
                # 3. Token validation works differently on Railway vs local/Emergent
                
            else:
                logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing Railway clients endpoint: {str(e)}")
            raise
            
        # Test with invalid token
        logger.info("\nTesting with invalid token...")
        
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Should get 401 Unauthorized, not 403 Forbidden
            if response.status_code == 401:
                logger.info("✅ Invalid token test passed - received 401 Unauthorized")
                error_data = response.json()
                logger.info(f"Error detail: {error_data.get('detail', 'No detail provided')}")
            elif response.status_code == 403:
                logger.warning("⚠️ Received 403 Forbidden for invalid token - investigating why")
                error_data = response.json()
                logger.info(f"Error detail: {error_data.get('detail', 'No detail provided')}")
            else:
                logger.warning(f"⚠️ Unexpected status code for invalid token: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing Railway clients endpoint with invalid token: {str(e)}")
            raise
            
        # Test without token
        logger.info("\nTesting without token...")
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Should get 401 Unauthorized or 403 Forbidden
            if response.status_code in [401, 403]:
                logger.info(f"✅ No token test passed - received {response.status_code}")
                error_data = response.json()
                logger.info(f"Error detail: {error_data.get('detail', 'No detail provided')}")
            else:
                logger.warning(f"⚠️ Unexpected status code for no token: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing Railway clients endpoint without token: {str(e)}")
            raise
    
    def test_railway_auth_me_endpoint(self):
        """Test the /api/auth/me endpoint on Railway backend"""
        logger.info("\n=== Testing Railway backend /api/auth/me endpoint ===")
        
        # Test with client user token
        logger.info("Testing with client user token...")
        url = f"{self.api_url}/auth/me"
        
        try:
            response = requests.get(url, headers=self.client_headers)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:500]}...")
            
            # Check if we get a 200 OK, 401 Unauthorized, or 403 Forbidden
            if response.status_code == 200:
                logger.info("✅ Authentication successful - received 200 OK")
                data = response.json()
                
                # Check user data
                logger.info(f"User ID: {data.get('id', 'Not found')}")
                logger.info(f"User email: {data.get('email', 'Not found')}")
                logger.info(f"User role: {data.get('role', 'Not found')}")
                logger.info(f"User client_id: {data.get('client_id', 'Not found')}")
                
                # Check if client_id is empty - this could be the issue
                if not data.get('client_id'):
                    logger.warning("⚠️ User has no client_id - this is likely causing the 403 error on /api/clients")
                
            elif response.status_code == 401:
                logger.info("✅ Authentication failed correctly - received 401 Unauthorized")
                error_data = response.json()
                logger.info(f"Error detail: {error_data.get('detail', 'No detail provided')}")
                
            elif response.status_code == 403:
                logger.warning("⚠️ Received 403 Forbidden - investigating why")
                error_data = response.json()
                logger.info(f"Error detail: {error_data.get('detail', 'No detail provided')}")
                
            else:
                logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing Railway auth/me endpoint: {str(e)}")
            raise
    
    def test_railway_health_endpoint(self):
        """Test the /api/health endpoint on Railway backend"""
        logger.info("\n=== Testing Railway backend /api/health endpoint ===")
        
        url = f"{self.api_url}/health"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Health endpoint should be accessible without authentication
            if response.status_code == 200:
                logger.info("✅ Health endpoint accessible - received 200 OK")
                data = response.json()
                logger.info(f"Service status: {data.get('status', 'Not found')}")
                logger.info(f"Service name: {data.get('service', 'Not found')}")
            else:
                logger.warning(f"⚠️ Unexpected status code for health endpoint: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing Railway health endpoint: {str(e)}")
            raise
    
    def test_railway_cors_preflight(self):
        """Test CORS preflight requests on Railway backend"""
        logger.info("\n=== Testing Railway backend CORS preflight requests ===")
        
        # Test preflight for /api/clients endpoint
        logger.info("Testing preflight for /api/clients endpoint...")
        url = f"{self.api_url}/clients"
        
        try:
            # Send OPTIONS request
            headers = {
                "Origin": "https://portal.rotakalitedanismanlik.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
            
            response = requests.options(url, headers=headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            cors_methods = response.headers.get("Access-Control-Allow-Methods")
            cors_headers = response.headers.get("Access-Control-Allow-Headers")
            
            logger.info(f"Access-Control-Allow-Origin: {cors_origin}")
            logger.info(f"Access-Control-Allow-Methods: {cors_methods}")
            logger.info(f"Access-Control-Allow-Headers: {cors_headers}")
            
            # Preflight should return 200 OK
            if response.status_code == 200:
                logger.info("✅ Preflight request successful - received 200 OK")
                
                # Check if CORS headers are properly set
                if cors_origin:
                    logger.info("✅ Access-Control-Allow-Origin header is set")
                else:
                    logger.warning("⚠️ Access-Control-Allow-Origin header is missing")
                    
                if cors_methods and "GET" in cors_methods:
                    logger.info("✅ Access-Control-Allow-Methods header includes GET")
                else:
                    logger.warning("⚠️ Access-Control-Allow-Methods header is missing or doesn't include GET")
                    
                if cors_headers and "Authorization" in cors_headers:
                    logger.info("✅ Access-Control-Allow-Headers header includes Authorization")
                else:
                    logger.warning("⚠️ Access-Control-Allow-Headers header is missing or doesn't include Authorization")
            else:
                logger.warning(f"⚠️ Unexpected status code for preflight request: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing Railway CORS preflight: {str(e)}")
            raise

def run_railway_auth_tests():
    """Run Railway backend authentication tests"""
    logger.info("Starting Railway backend authentication tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add Railway backend authentication tests
    suite.addTest(TestRailwayBackendAuth("test_railway_health_endpoint"))
    suite.addTest(TestRailwayBackendAuth("test_railway_cors_preflight"))
    suite.addTest(TestRailwayBackendAuth("test_railway_auth_me_endpoint"))
    suite.addTest(TestRailwayBackendAuth("test_railway_clients_endpoint"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Railway Backend Authentication Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All Railway backend authentication tests PASSED")
        return True
    else:
        logger.error("Some Railway backend authentication tests FAILED")
        return False

if __name__ == "__main__":
    run_railway_auth_tests()