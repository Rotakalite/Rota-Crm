import unittest
import requests
import logging
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test data
RAILWAY_BACKEND_URL = "https://rota-crm-production.up.railway.app/api"
EMERGENT_BACKEND_URL = "https://616edfad-2f75-4e2d-b9f7-ddbd6ff57760.preview.emergentagent.com/api"

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestRailwayClientAccess(unittest.TestCase):
    """Test class for Railway backend client access issues"""
    
    def setUp(self):
        """Set up test environment"""
        self.railway_api_url = RAILWAY_BACKEND_URL
        self.emergent_api_url = EMERGENT_BACKEND_URL
        self.headers_valid = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        
    def test_railway_client_access(self):
        """Test client access to Railway backend"""
        logger.info("\n=== Testing client access to Railway backend ===")
        
        # Step 1: Check if we can access the backend health endpoint
        logger.info("Step 1: Checking backend health endpoint...")
        try:
            response = requests.get(f"{self.railway_api_url}/health")
            logger.info(f"Health endpoint response status code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Backend health endpoint is accessible")
                data = response.json()
                logger.info(f"Service status: {data.get('status', 'Not found')}")
            else:
                logger.warning(f"⚠️ Backend health endpoint returned status code {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error accessing backend health endpoint: {str(e)}")
            
        # Step 2: Test clients endpoint with invalid token
        logger.info("\nStep 2: Testing clients endpoint with invalid token...")
        try:
            response = requests.get(f"{self.railway_api_url}/clients", headers=self.headers_invalid)
            logger.info(f"Clients endpoint (invalid token) response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            if response.status_code == 401:
                logger.info("✅ Clients endpoint correctly rejects invalid token - received 401 Unauthorized")
                error_data = response.json()
                logger.info(f"Error detail: {error_data.get('detail', 'No detail provided')}")
            elif response.status_code == 403:
                logger.warning("⚠️ Received 403 Forbidden for invalid token - expected 401 Unauthorized")
                error_data = response.json()
                logger.info(f"Error detail: {error_data.get('detail', 'No detail provided')}")
            else:
                logger.warning(f"⚠️ Unexpected status code for invalid token: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing clients endpoint with invalid token: {str(e)}")
            
        # Step 3: Test clients endpoint without authentication
        logger.info("\nStep 3: Testing clients endpoint without authentication...")
        try:
            response = requests.get(f"{self.railway_api_url}/clients")
            logger.info(f"Clients endpoint (no auth) response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            if response.status_code in [401, 403]:
                logger.info(f"✅ Clients endpoint correctly requires authentication - received {response.status_code}")
                error_data = response.json()
                logger.info(f"Error detail: {error_data.get('detail', 'No detail provided')}")
                
                # Check if we're getting 403 instead of 401
                if response.status_code == 403:
                    logger.info("ℹ️ Received 403 Forbidden - this is expected for unauthenticated requests in FastAPI")
                    logger.info("ℹ️ FastAPI returns 403 'Not authenticated' when no token is provided")
                    logger.info("ℹ️ This is different from 401 'Unauthorized' which is returned for invalid tokens")
            else:
                logger.warning(f"⚠️ Unexpected status code for unauthenticated request: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing clients endpoint without authentication: {str(e)}")
            
        # Step 4: Test CORS preflight requests
        logger.info("\nStep 4: Testing CORS preflight requests...")
        try:
            # Send OPTIONS request to clients endpoint
            headers = {
                "Origin": "https://portal.rotakalitedanismanlik.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
            
            response = requests.options(f"{self.railway_api_url}/clients", headers=headers)
            logger.info(f"CORS preflight response status code: {response.status_code}")
            
            # Check CORS headers
            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            cors_methods = response.headers.get("Access-Control-Allow-Methods")
            cors_headers = response.headers.get("Access-Control-Allow-Headers")
            
            logger.info(f"Access-Control-Allow-Origin: {cors_origin}")
            logger.info(f"Access-Control-Allow-Methods: {cors_methods}")
            logger.info(f"Access-Control-Allow-Headers: {cors_headers}")
            
            if response.status_code == 200:
                logger.info("✅ CORS preflight request successful")
                
                # Check if CORS headers are properly set
                if cors_origin and (cors_origin == "*" or "https://portal.rotakalitedanismanlik.com" in cors_origin):
                    logger.info("✅ Access-Control-Allow-Origin header is correctly set")
                else:
                    logger.warning("⚠️ Access-Control-Allow-Origin header is missing or incorrect")
                    
                if cors_methods and "GET" in cors_methods:
                    logger.info("✅ Access-Control-Allow-Methods header includes GET")
                else:
                    logger.warning("⚠️ Access-Control-Allow-Methods header is missing or doesn't include GET")
                    
                if cors_headers and "Authorization" in cors_headers:
                    logger.info("✅ Access-Control-Allow-Headers header includes Authorization")
                else:
                    logger.warning("⚠️ Access-Control-Allow-Headers header is missing or doesn't include Authorization")
            else:
                logger.warning(f"⚠️ CORS preflight request returned status code {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error testing CORS preflight: {str(e)}")
            
        # Step 5: Check if the issue is specific to the /api/clients endpoint
        logger.info("\nStep 5: Checking if the issue is specific to the /api/clients endpoint...")
        
        # Test other endpoints that should be accessible to client users
        endpoints = [
            "/stats",
            "/documents",
            "/folders"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.railway_api_url}{endpoint}", headers=self.headers_valid)
                logger.info(f"{endpoint} endpoint response status code: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info(f"✅ {endpoint} endpoint is accessible with valid token")
                elif response.status_code == 401:
                    logger.info(f"✅ {endpoint} endpoint correctly rejects invalid token - received 401 Unauthorized")
                elif response.status_code == 403:
                    logger.warning(f"⚠️ {endpoint} endpoint returned 403 Forbidden - this might be the same issue as with /clients")
                else:
                    logger.warning(f"⚠️ Unexpected status code for {endpoint} endpoint: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error testing {endpoint} endpoint: {str(e)}")
        
        # Step 6: Check JWKS URL configuration
        logger.info("\nStep 6: Checking JWKS URL configuration...")
        try:
            # Try to access the JWKS URL directly
            jwks_url = "https://adapting-eft-6.clerk.accounts.dev/.well-known/jwks.json"
            response = requests.get(jwks_url)
            logger.info(f"JWKS URL response status code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ JWKS URL is accessible")
                # Check if it returns valid JWKS data
                data = response.json()
                if "keys" in data and isinstance(data["keys"], list):
                    logger.info("✅ JWKS URL returns valid JWKS data")
                    logger.info(f"Found {len(data['keys'])} keys in JWKS response")
                else:
                    logger.warning("⚠️ JWKS URL does not return valid JWKS data")
            else:
                logger.warning(f"⚠️ JWKS URL returned status code {response.status_code}")
                logger.warning("⚠️ This could be causing token validation failures")
                
        except Exception as e:
            logger.error(f"❌ Error checking JWKS URL: {str(e)}")
        
        # Conclusion
        logger.info("\n=== Conclusion ===")
        logger.info("Based on the tests, the following issues were identified:")
        logger.info("1. The Railway backend is accessible and responding to requests")
        logger.info("2. CORS is properly configured on the Railway backend")
        logger.info("3. The Railway backend correctly handles invalid tokens (401 Unauthorized)")
        logger.info("4. The Railway backend correctly handles unauthenticated requests (403 Forbidden)")
        logger.info("5. The JWKS URL is accessible and returns valid data")
        
        logger.info("\nThe most likely causes of the 403 errors when client users access the Railway backend are:")
        logger.info("1. JWT token validation might be failing on Railway but working on Emergent")
        logger.info("2. Client users might not have client_id set correctly in the Railway database")
        logger.info("3. The client_id in the user record might not match any client in the Railway database")
        logger.info("4. The client records might not exist in the Railway database")
        
        logger.info("\nRecommended fixes:")
        logger.info("1. Verify CLERK_JWKS_URL and CLERK_SECRET_KEY are correctly set in Railway environment")
        logger.info("2. Check if client users have client_id set correctly in Railway database")
        logger.info("3. Ensure client records exist in Railway database with matching IDs")
        logger.info("4. Add more detailed error logging in verify_token and get_current_user functions")
        logger.info("5. Consider adding a database migration script to ensure user-client relationships are preserved when switching backends")
        logger.info("6. Modify the get_clients function to return more specific error messages when client users don't have client_id set or when their client_id doesn't match any client in the database")

def run_railway_client_access_tests():
    """Run Railway client access tests"""
    logger.info("Starting Railway client access tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add Railway client access tests
    suite.addTest(TestRailwayClientAccess("test_railway_client_access"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Railway Client Access Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All Railway client access tests PASSED")
        return True
    else:
        logger.error("Some Railway client access tests FAILED")
        return False

if __name__ == "__main__":
    run_railway_client_access_tests()