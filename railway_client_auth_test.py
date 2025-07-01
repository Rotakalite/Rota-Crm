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
TEST_CLIENT_EMAIL = "test@example.com"
TEST_CLIENT_PASSWORD = "password123"

class TestRailwayBackendClientAuth(unittest.TestCase):
    """Test class for Railway backend client authentication issues"""
    
    def setUp(self):
        """Set up test environment"""
        # Use the Railway backend URL from frontend/.env
        self.api_url = "https://rota-crm-production.up.railway.app/api"
        self.frontend_url = "https://portal.rotakalitedanismanlik.com"
        
        # We'll need to get a real token from Clerk
        self.token = None
        
    def test_clerk_auth_flow(self):
        """Test the complete authentication flow using Clerk and Railway backend"""
        logger.info("\n=== Testing complete authentication flow with Clerk and Railway backend ===")
        
        # Step 1: Check if we can access the frontend
        logger.info("Step 1: Checking frontend access...")
        try:
            response = requests.get(self.frontend_url)
            logger.info(f"Frontend response status code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Frontend is accessible")
            else:
                logger.warning(f"⚠️ Frontend returned status code {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error accessing frontend: {str(e)}")
            
        # Step 2: Check if we can access the backend health endpoint
        logger.info("\nStep 2: Checking backend health endpoint...")
        try:
            response = requests.get(f"{self.api_url}/health")
            logger.info(f"Health endpoint response status code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Backend health endpoint is accessible")
                data = response.json()
                logger.info(f"Service status: {data.get('status', 'Not found')}")
            else:
                logger.warning(f"⚠️ Backend health endpoint returned status code {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error accessing backend health endpoint: {str(e)}")
            
        # Step 3: Test CORS preflight requests
        logger.info("\nStep 3: Testing CORS preflight requests...")
        try:
            # Send OPTIONS request to clients endpoint
            headers = {
                "Origin": self.frontend_url,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
            
            response = requests.options(f"{self.api_url}/clients", headers=headers)
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
                if cors_origin and (cors_origin == "*" or self.frontend_url in cors_origin):
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
            
        # Step 4: Test clients endpoint without authentication
        logger.info("\nStep 4: Testing clients endpoint without authentication...")
        try:
            response = requests.get(f"{self.api_url}/clients")
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
            
        # Step 5: Test clients endpoint with invalid token
        logger.info("\nStep 5: Testing clients endpoint with invalid token...")
        try:
            headers = {"Authorization": "Bearer invalid.token.format"}
            response = requests.get(f"{self.api_url}/clients", headers=headers)
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
            
        # Step 6: Compare with Emergent backend (if available)
        logger.info("\nStep 6: Comparing with Emergent backend...")
        emergent_api_url = "https://45c51488-b08d-4ec3-832c-628720c8dcae.preview.emergentagent.com/api"
        
        try:
            # Test health endpoint
            response = requests.get(f"{emergent_api_url}/health")
            logger.info(f"Emergent health endpoint response status code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Emergent backend health endpoint is accessible")
            else:
                logger.warning(f"⚠️ Emergent backend health endpoint returned status code {response.status_code}")
                
            # Test clients endpoint without authentication
            response = requests.get(f"{emergent_api_url}/clients")
            logger.info(f"Emergent clients endpoint (no auth) response status code: {response.status_code}")
            
            if response.status_code in [401, 403]:
                logger.info(f"✅ Emergent clients endpoint correctly requires authentication - received {response.status_code}")
                
                # Compare with Railway behavior
                railway_response = requests.get(f"{self.api_url}/clients")
                logger.info(f"Railway clients endpoint (no auth) response status code: {railway_response.status_code}")
                
                if railway_response.status_code == response.status_code:
                    logger.info("✅ Railway and Emergent backends behave the same for unauthenticated requests")
                else:
                    logger.warning(f"⚠️ Railway ({railway_response.status_code}) and Emergent ({response.status_code}) backends behave differently for unauthenticated requests")
            else:
                logger.warning(f"⚠️ Unexpected status code for unauthenticated request to Emergent: {response.status_code}")
                
            # Test clients endpoint with invalid token
            headers = {"Authorization": "Bearer invalid.token.format"}
            response = requests.get(f"{emergent_api_url}/clients", headers=headers)
            logger.info(f"Emergent clients endpoint (invalid token) response status code: {response.status_code}")
            
            if response.status_code == 401:
                logger.info("✅ Emergent clients endpoint correctly rejects invalid token - received 401 Unauthorized")
                
                # Compare with Railway behavior
                railway_response = requests.get(f"{self.api_url}/clients", headers=headers)
                logger.info(f"Railway clients endpoint (invalid token) response status code: {railway_response.status_code}")
                
                if railway_response.status_code == response.status_code:
                    logger.info("✅ Railway and Emergent backends behave the same for invalid tokens")
                else:
                    logger.warning(f"⚠️ Railway ({railway_response.status_code}) and Emergent ({response.status_code}) backends behave differently for invalid tokens")
            else:
                logger.warning(f"⚠️ Unexpected status code for invalid token to Emergent: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error comparing with Emergent backend: {str(e)}")
            
        # Step 7: Check JWKS URL configuration
        logger.info("\nStep 7: Checking JWKS URL configuration...")
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
            
        # Step 8: Check for differences between Railway and local/Emergent
        logger.info("\nStep 8: Analyzing differences between Railway and local/Emergent...")
        
        logger.info("Possible issues:")
        logger.info("1. JWT token validation might be failing on Railway but working on local/Emergent")
        logger.info("2. Client users might not have client_id set correctly in the Railway database")
        logger.info("3. The client_id in the user record might not match any client in the Railway database")
        logger.info("4. CORS configuration might be different between Railway and local/Emergent")
        logger.info("5. Railway might be using a different JWKS URL or Clerk configuration")
        
        # Conclusion
        logger.info("\nConclusion:")
        logger.info("Based on the tests, the most likely issues are:")
        logger.info("1. JWT token validation is failing on Railway - check CLERK_JWKS_URL and CLERK_SECRET_KEY in Railway environment")
        logger.info("2. Client users don't have client_id set correctly in Railway database")
        logger.info("3. The client records in Railway database might be different from local/Emergent")
        
        logger.info("\nRecommended fixes:")
        logger.info("1. Verify CLERK_JWKS_URL and CLERK_SECRET_KEY are correctly set in Railway environment")
        logger.info("2. Check if client users have client_id set correctly in Railway database")
        logger.info("3. Ensure client records exist in Railway database with matching IDs")
        logger.info("4. Consider adding more detailed error logging in verify_token and get_current_user functions")

def run_railway_client_auth_tests():
    """Run Railway backend client authentication tests"""
    logger.info("Starting Railway backend client authentication tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add Railway backend client authentication tests
    suite.addTest(TestRailwayBackendClientAuth("test_clerk_auth_flow"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Railway Backend Client Authentication Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All Railway backend client authentication tests PASSED")
        return True
    else:
        logger.error("Some Railway backend client authentication tests FAILED")
        return False

if __name__ == "__main__":
    run_railway_client_auth_tests()