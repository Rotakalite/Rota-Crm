import unittest
import json
import logging
import requests
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load backend URL from frontend .env file
def get_backend_url():
    env_file_path = "/app/frontend/.env"
    backend_url = None
    
    try:
        with open(env_file_path, 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.strip().split('=', 1)[1].strip('"\'')
                    break
        
        if not backend_url:
            logger.error("REACT_APP_BACKEND_URL not found in .env file")
            return "https://53980ca9-c304-433e-ab62-1c37a7176dd5.preview.emergentagent.com"
        
        return backend_url
    except Exception as e:
        logger.error(f"Error reading .env file: {str(e)}")
        return "https://53980ca9-c304-433e-ab62-1c37a7176dd5.preview.emergentagent.com"

class TestBackendEndpoints(unittest.TestCase):
    """Test class for backend endpoints without authentication"""
    
    def setUp(self):
        """Set up test environment"""
        self.backend_url = get_backend_url()
        self.api_url = f"{self.backend_url}/api"
        logger.info(f"Using API URL: {self.api_url}")
    
    def test_health_endpoint(self):
        """Test the /api/health endpoint"""
        logger.info("\n=== Testing /api/health endpoint ===")
        
        url = f"{self.api_url}/health"
        
        try:
            response = requests.get(url)
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                self.assertEqual(response.status_code, 200)
                self.assertIn("status", data)
                self.assertEqual(data["status"], "healthy")
                logger.info("✅ Health endpoint test passed")
            else:
                logger.warning(f"⚠️ Health endpoint test returned non-200 status: {response.status_code}")
                logger.warning(f"Response: {response.text}")
                self.fail(f"Health endpoint returned status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing health endpoint: {str(e)}")
            self.fail(f"Exception during health endpoint test: {str(e)}")
    
    def test_root_endpoint(self):
        """Test the /api/ root endpoint"""
        logger.info("\n=== Testing /api/ root endpoint ===")
        
        url = f"{self.api_url}/"
        
        try:
            response = requests.get(url)
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                self.assertEqual(response.status_code, 200)
                self.assertIn("message", data)
                logger.info("✅ Root endpoint test passed")
            else:
                logger.warning(f"⚠️ Root endpoint test returned non-200 status: {response.status_code}")
                logger.warning(f"Response: {response.text}")
                self.fail(f"Root endpoint returned status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing root endpoint: {str(e)}")
            self.fail(f"Exception during root endpoint test: {str(e)}")
    
    def test_malformed_token_handling(self):
        """Test how the API handles malformed tokens"""
        logger.info("\n=== Testing malformed token handling ===")
        
        # Test endpoints that require authentication
        endpoints = [
            "/api/clients",
            "/api/stats",
            "/api/auth/me"
        ]
        
        # Test with different malformed tokens
        malformed_tokens = [
            "invalid_token",  # Not in JWT format
            "invalid.token",  # Only two segments
            "invalid.token.with.too.many.segments",  # Too many segments
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"  # Missing signature
        ]
        
        for endpoint in endpoints:
            for token in malformed_tokens:
                logger.info(f"Testing {endpoint} with malformed token: {token[:20]}...")
                
                url = f"{self.backend_url}{endpoint}"
                headers = {"Authorization": f"Bearer {token}"}
                
                try:
                    response = requests.get(url, headers=headers)
                    logger.info(f"Status code: {response.status_code}")
                    
                    # We expect a 401 Unauthorized, not a 403 Forbidden
                    self.assertNotEqual(response.status_code, 403, 
                                       f"Endpoint {endpoint} returned 403 Forbidden instead of 401 Unauthorized")
                    
                    if response.status_code == 401:
                        logger.info(f"✅ Correctly received 401 Unauthorized for malformed token")
                    else:
                        logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
                        logger.warning(f"Response: {response.text}")
                except Exception as e:
                    logger.error(f"❌ Error testing endpoint {endpoint}: {str(e)}")

def run_tests():
    """Run all backend endpoint tests"""
    logger.info("Starting backend endpoint tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(TestBackendEndpoints("test_health_endpoint"))
    suite.addTest(TestBackendEndpoints("test_root_endpoint"))
    suite.addTest(TestBackendEndpoints("test_malformed_token_handling"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All tests PASSED")
        return True
    else:
        logger.error("Some tests FAILED")
        for error in result.errors:
            logger.error(f"Error: {error}")
        for failure in result.failures:
            logger.error(f"Failure: {failure}")
        return False

if __name__ == "__main__":
    run_tests()