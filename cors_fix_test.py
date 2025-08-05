import unittest
import requests
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestCORSFix(unittest.TestCase):
    """Test class for CORS configuration fix"""
    
    def setUp(self):
        """Set up test environment"""
        # Use the URL from the error message
        self.api_url = "https://63cd9e66-c298-4a2c-92bc-f8af7936d9a9.preview.emergentagent.com/api"
        # Use the origin from the error message
        self.origin = "https://portal.rotakalitedanismanlik.com"
        
        # Headers for testing
        self.headers = {
            "Origin": self.origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type, Authorization"
        }
        
    def test_preflight_requests(self):
        """Test OPTIONS preflight requests to critical endpoints"""
        logger.info("\n=== Testing CORS Preflight Requests ===")
        
        # List of endpoints to test
        endpoints = [
            "/stats",
            "/clients",
            "/auth/register",
            "/health"
        ]
        
        for endpoint in endpoints:
            url = f"{self.api_url}{endpoint}"
            logger.info(f"Testing OPTIONS preflight request to {url}")
            
            try:
                # Send OPTIONS request
                response = requests.options(url, headers=self.headers)
                
                # Log response details
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
                
                # Check status code
                self.assertEqual(response.status_code, 200, f"OPTIONS request to {endpoint} should return 200 OK")
                
                # Check CORS headers
                self.assertIn("Access-Control-Allow-Origin", response.headers, 
                             f"Response for {endpoint} should include Access-Control-Allow-Origin header")
                
                # Check if our origin is allowed (either explicitly or via wildcard)
                allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
                self.assertTrue(allow_origin == "*" or allow_origin == self.origin,
                               f"Access-Control-Allow-Origin should be '*' or match our origin: {self.origin}")
                
                # Check other required CORS headers
                self.assertIn("Access-Control-Allow-Methods", response.headers,
                             f"Response for {endpoint} should include Access-Control-Allow-Methods header")
                self.assertIn("Access-Control-Allow-Headers", response.headers,
                             f"Response for {endpoint} should include Access-Control-Allow-Headers header")
                
                logger.info(f"✅ CORS preflight test PASSED for {endpoint}")
                
            except Exception as e:
                logger.error(f"❌ Error testing OPTIONS preflight for {endpoint}: {str(e)}")
                raise
    
    def test_actual_requests(self):
        """Test actual requests with CORS headers"""
        logger.info("\n=== Testing Actual Requests with CORS Headers ===")
        
        # Test GET /api/stats
        logger.info("Testing GET /api/stats with CORS headers")
        url = f"{self.api_url}/stats"
        
        try:
            # Send GET request with Origin header
            response = requests.get(url, headers={"Origin": self.origin})
            
            # Log response details
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
            
            # Check CORS headers in response
            self.assertIn("Access-Control-Allow-Origin", response.headers,
                         "Response should include Access-Control-Allow-Origin header")
            
            # Check if our origin is allowed (either explicitly or via wildcard)
            allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
            self.assertTrue(allow_origin == "*" or allow_origin == self.origin,
                           f"Access-Control-Allow-Origin should be '*' or match our origin: {self.origin}")
            
            logger.info("✅ CORS actual request test PASSED for /api/stats")
            
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/stats with CORS headers: {str(e)}")
            raise
        
        # Test GET /api/clients
        logger.info("Testing GET /api/clients with CORS headers")
        url = f"{self.api_url}/clients"
        
        try:
            # Send GET request with Origin header
            response = requests.get(url, headers={"Origin": self.origin})
            
            # Log response details
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
            
            # Check CORS headers in response
            self.assertIn("Access-Control-Allow-Origin", response.headers,
                         "Response should include Access-Control-Allow-Origin header")
            
            # Check if our origin is allowed (either explicitly or via wildcard)
            allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
            self.assertTrue(allow_origin == "*" or allow_origin == self.origin,
                           f"Access-Control-Allow-Origin should be '*' or match our origin: {self.origin}")
            
            logger.info("✅ CORS actual request test PASSED for /api/clients")
            
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/clients with CORS headers: {str(e)}")
            raise
        
        # Test POST /api/auth/register
        logger.info("Testing POST /api/auth/register with CORS headers")
        url = f"{self.api_url}/auth/register"
        
        try:
            # Sample registration data
            data = {
                "clerk_user_id": "test_user_id",
                "email": "test@example.com",
                "name": "Test User",
                "role": "client"
            }
            
            # Send POST request with Origin header
            response = requests.post(url, headers={"Origin": self.origin, "Content-Type": "application/json"}, json=data)
            
            # Log response details
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
            
            # Check CORS headers in response
            self.assertIn("Access-Control-Allow-Origin", response.headers,
                         "Response should include Access-Control-Allow-Origin header")
            
            # Check if our origin is allowed (either explicitly or via wildcard)
            allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
            self.assertTrue(allow_origin == "*" or allow_origin == self.origin,
                           f"Access-Control-Allow-Origin should be '*' or match our origin: {self.origin}")
            
            logger.info("✅ CORS actual request test PASSED for /api/auth/register")
            
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/auth/register with CORS headers: {str(e)}")
            raise
        
        # Test GET /api/health
        logger.info("Testing GET /api/health with CORS headers")
        url = f"{self.api_url}/health"
        
        try:
            # Send GET request with Origin header
            response = requests.get(url, headers={"Origin": self.origin})
            
            # Log response details
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
            
            # Check CORS headers in response
            self.assertIn("Access-Control-Allow-Origin", response.headers,
                         "Response should include Access-Control-Allow-Origin header")
            
            # Check if our origin is allowed (either explicitly or via wildcard)
            allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
            self.assertTrue(allow_origin == "*" or allow_origin == self.origin,
                           f"Access-Control-Allow-Origin should be '*' or match our origin: {self.origin}")
            
            logger.info("✅ CORS actual request test PASSED for /api/health")
            
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/health with CORS headers: {str(e)}")
            raise

def run_tests():
    """Run all CORS tests"""
    logger.info("Starting CORS configuration tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(TestCORSFix("test_preflight_requests"))
    suite.addTest(TestCORSFix("test_actual_requests"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All CORS configuration tests PASSED")
        return True
    else:
        logger.error("Some CORS configuration tests FAILED")
        return False

if __name__ == "__main__":
    run_tests()