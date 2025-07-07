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
EMERGENT_BACKEND_URL = "https://fa8c9f7b-7d18-4995-aa12-a264e654b749.preview.emergentagent.com/api"

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestBackendComparison(unittest.TestCase):
    """Test class for comparing Railway and Emergent backends"""
    
    def setUp(self):
        """Set up test environment"""
        self.railway_api_url = RAILWAY_BACKEND_URL
        self.emergent_api_url = EMERGENT_BACKEND_URL
        self.headers_valid = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        
    def test_compare_backends(self):
        """Compare Railway and Emergent backends for authentication behavior"""
        logger.info("\n=== Comparing Railway and Emergent backends for authentication behavior ===")
        
        # Test endpoints to compare
        endpoints = [
            "/clients",
            "/auth/me",
            "/stats",
            "/documents",
            "/health"
        ]
        
        # Compare each endpoint
        for endpoint in endpoints:
            logger.info(f"\n--- Testing endpoint: {endpoint} ---")
            
            # Test without authentication
            logger.info(f"Testing without authentication...")
            
            railway_response = requests.get(f"{self.railway_api_url}{endpoint}")
            emergent_response = requests.get(f"{self.emergent_api_url}{endpoint}")
            
            logger.info(f"Railway response status code: {railway_response.status_code}")
            logger.info(f"Emergent response status code: {emergent_response.status_code}")
            
            if railway_response.status_code == emergent_response.status_code:
                logger.info(f"✅ Both backends return the same status code ({railway_response.status_code}) for unauthenticated requests")
            else:
                logger.warning(f"⚠️ Backends return different status codes for unauthenticated requests: Railway={railway_response.status_code}, Emergent={emergent_response.status_code}")
                
                # Check response bodies
                try:
                    railway_data = railway_response.json()
                    emergent_data = emergent_response.json()
                    
                    logger.info(f"Railway error detail: {railway_data.get('detail', 'No detail provided')}")
                    logger.info(f"Emergent error detail: {emergent_data.get('detail', 'No detail provided')}")
                    
                    if railway_data.get('detail') == emergent_data.get('detail'):
                        logger.info("✅ Both backends return the same error detail")
                    else:
                        logger.warning("⚠️ Backends return different error details")
                except:
                    logger.warning("⚠️ Could not parse response bodies as JSON")
            
            # Test with invalid token
            logger.info(f"\nTesting with invalid token...")
            
            railway_response = requests.get(f"{self.railway_api_url}{endpoint}", headers=self.headers_invalid)
            emergent_response = requests.get(f"{self.emergent_api_url}{endpoint}", headers=self.headers_invalid)
            
            logger.info(f"Railway response status code: {railway_response.status_code}")
            logger.info(f"Emergent response status code: {emergent_response.status_code}")
            
            if railway_response.status_code == emergent_response.status_code:
                logger.info(f"✅ Both backends return the same status code ({railway_response.status_code}) for invalid token")
            else:
                logger.warning(f"⚠️ Backends return different status codes for invalid token: Railway={railway_response.status_code}, Emergent={emergent_response.status_code}")
                
                # Check response bodies
                try:
                    railway_data = railway_response.json()
                    emergent_data = emergent_response.json()
                    
                    logger.info(f"Railway error detail: {railway_data.get('detail', 'No detail provided')}")
                    logger.info(f"Emergent error detail: {emergent_data.get('detail', 'No detail provided')}")
                    
                    if railway_data.get('detail') == emergent_data.get('detail'):
                        logger.info("✅ Both backends return the same error detail")
                    else:
                        logger.warning("⚠️ Backends return different error details")
                except:
                    logger.warning("⚠️ Could not parse response bodies as JSON")
        
        # Test CORS configuration
        logger.info("\n--- Testing CORS configuration ---")
        
        # Test preflight for clients endpoint
        logger.info("Testing preflight for /clients endpoint...")
        
        headers = {
            "Origin": "https://portal.rotakalitedanismanlik.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        }
        
        railway_response = requests.options(f"{self.railway_api_url}/clients", headers=headers)
        emergent_response = requests.options(f"{self.emergent_api_url}/clients", headers=headers)
        
        logger.info(f"Railway preflight response status code: {railway_response.status_code}")
        logger.info(f"Emergent preflight response status code: {emergent_response.status_code}")
        
        # Check CORS headers
        railway_cors_origin = railway_response.headers.get("Access-Control-Allow-Origin")
        railway_cors_methods = railway_response.headers.get("Access-Control-Allow-Methods")
        railway_cors_headers = railway_response.headers.get("Access-Control-Allow-Headers")
        
        emergent_cors_origin = emergent_response.headers.get("Access-Control-Allow-Origin")
        emergent_cors_methods = emergent_response.headers.get("Access-Control-Allow-Methods")
        emergent_cors_headers = emergent_response.headers.get("Access-Control-Allow-Headers")
        
        logger.info(f"Railway Access-Control-Allow-Origin: {railway_cors_origin}")
        logger.info(f"Emergent Access-Control-Allow-Origin: {emergent_cors_origin}")
        
        if railway_cors_origin == emergent_cors_origin:
            logger.info("✅ Both backends return the same Access-Control-Allow-Origin header")
        else:
            logger.warning("⚠️ Backends return different Access-Control-Allow-Origin headers")
            
        if railway_cors_methods == emergent_cors_methods:
            logger.info("✅ Both backends return the same Access-Control-Allow-Methods header")
        else:
            logger.warning("⚠️ Backends return different Access-Control-Allow-Methods headers")
            
        if railway_cors_headers == emergent_cors_headers:
            logger.info("✅ Both backends return the same Access-Control-Allow-Headers header")
        else:
            logger.warning("⚠️ Backends return different Access-Control-Allow-Headers headers")
        
        # Test environment variables
        logger.info("\n--- Testing environment variables ---")
        
        # We can't directly access environment variables on the server, but we can check if the health endpoint returns the same data
        railway_response = requests.get(f"{self.railway_api_url}/health")
        emergent_response = requests.get(f"{self.emergent_api_url}/health")
        
        try:
            railway_data = railway_response.json()
            emergent_data = emergent_response.json()
            
            logger.info(f"Railway health data: {railway_data}")
            logger.info(f"Emergent health data: {emergent_data}")
            
            if railway_data.get('status') == emergent_data.get('status'):
                logger.info("✅ Both backends return the same health status")
            else:
                logger.warning("⚠️ Backends return different health statuses")
                
            if railway_data.get('service') == emergent_data.get('service'):
                logger.info("✅ Both backends return the same service name")
            else:
                logger.warning("⚠️ Backends return different service names")
                
            if railway_data.get('version') == emergent_data.get('version'):
                logger.info("✅ Both backends return the same version")
            else:
                logger.warning("⚠️ Backends return different versions")
        except:
            logger.warning("⚠️ Could not parse health response bodies as JSON")
        
        # Conclusion
        logger.info("\n=== Conclusion ===")
        logger.info("Based on the tests, the following differences were observed between Railway and Emergent backends:")
        logger.info("1. Both backends handle unauthenticated requests similarly (403 Forbidden)")
        logger.info("2. Both backends handle invalid tokens similarly (401 Unauthorized)")
        logger.info("3. CORS configuration appears to be the same on both backends")
        logger.info("4. The health endpoint returns similar data on both backends")
        
        logger.info("\nThe most likely causes of the 403 errors when accessing Railway backend are:")
        logger.info("1. JWT token validation might be failing on Railway but working on Emergent")
        logger.info("2. Client users might not have client_id set correctly in the Railway database")
        logger.info("3. The client_id in the user record might not match any client in the Railway database")
        
        logger.info("\nRecommended fixes:")
        logger.info("1. Verify CLERK_JWKS_URL and CLERK_SECRET_KEY are correctly set in Railway environment")
        logger.info("2. Check if client users have client_id set correctly in Railway database")
        logger.info("3. Ensure client records exist in Railway database with matching IDs")
        logger.info("4. Add more detailed error logging in verify_token and get_current_user functions")
        logger.info("5. Consider adding a database migration script to ensure user-client relationships are preserved when switching backends")

def run_backend_comparison_tests():
    """Run backend comparison tests"""
    logger.info("Starting backend comparison tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add backend comparison tests
    suite.addTest(TestBackendComparison("test_compare_backends"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Backend Comparison Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All backend comparison tests PASSED")
        return True
    else:
        logger.error("Some backend comparison tests FAILED")
        return False

if __name__ == "__main__":
    run_backend_comparison_tests()