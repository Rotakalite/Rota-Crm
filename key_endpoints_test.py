import unittest
import json
import logging
import requests
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestKeyEndpoints(unittest.TestCase):
    """Test class for key endpoints with the Railway backend URL"""
    
    def setUp(self):
        """Set up test environment"""
        # Use the Railway backend URL from frontend .env
        self.api_url = "https://rota-crm-production.up.railway.app/api"
        
    def test_key_endpoints_availability(self):
        """Test that key endpoints are available"""
        logger.info("\n=== Testing key endpoints availability ===")
        
        # Test endpoints
        endpoints = [
            "/health",
            "/auth/register",  # POST endpoint
            "/stats",
            "/clients"
        ]
        
        for endpoint in endpoints:
            url = f"{self.api_url}{endpoint}"
            
            logger.info(f"Testing endpoint: {url}")
            
            try:
                # Use OPTIONS request to check availability without authentication
                response = requests.options(url)
                
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response headers: {response.headers}")
                
                # OPTIONS request should return 200 OK
                self.assertEqual(response.status_code, 200)
                
                # Check CORS headers
                self.assertIn("Access-Control-Allow-Origin", response.headers)
                self.assertIn("Access-Control-Allow-Methods", response.headers)
                self.assertIn("Access-Control-Allow-Headers", response.headers)
                
                logger.info(f"✅ Endpoint {endpoint} is available")
                
            except Exception as e:
                logger.error(f"❌ Error testing endpoint {endpoint}: {str(e)}")
                raise
    
    def test_health_endpoint_content(self):
        """Test the content of the health endpoint response"""
        logger.info("\n=== Testing health endpoint content ===")
        
        url = f"{self.api_url}/health"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            # Health endpoint should be accessible without authentication
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            
            # Check required fields
            required_fields = ["status", "service", "timestamp", "version"]
            for field in required_fields:
                self.assertIn(field, data, f"Response should include {field} field")
            
            # Check specific values
            self.assertEqual(data["status"], "healthy")
            self.assertEqual(data["service"], "Rota CRM Backend")
            
            logger.info("✅ Health endpoint content test passed")
            
        except Exception as e:
            logger.error(f"❌ Error testing health endpoint content: {str(e)}")
            raise
    
    def test_auth_register_endpoint(self):
        """Test the auth/register endpoint"""
        logger.info("\n=== Testing auth/register endpoint ===")
        
        url = f"{self.api_url}/auth/register"
        
        try:
            # Create test user data
            test_user = {
                "clerk_user_id": f"test_clerk_id_{datetime.now().timestamp()}",
                "email": f"test_{datetime.now().timestamp()}@example.com",
                "name": "Test User",
                "role": "client"
            }
            
            # Send POST request
            response = requests.post(url, json=test_user)
            
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Should get 200 OK or 422 Validation Error
            self.assertIn(response.status_code, [200, 201, 422])
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.assertIn("id", data)
                self.assertIn("clerk_user_id", data)
                self.assertIn("email", data)
                self.assertIn("name", data)
                self.assertIn("role", data)
                
                logger.info(f"✅ User created with ID: {data['id']}")
            elif response.status_code == 422:
                logger.info("✅ Validation error - this is acceptable if the request format is incorrect")
            
            logger.info("✅ Auth/register endpoint test passed")
            
        except Exception as e:
            logger.error(f"❌ Error testing auth/register endpoint: {str(e)}")
            raise

def run_key_endpoints_tests():
    """Run key endpoints tests"""
    logger.info("Starting key endpoints tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add key endpoints tests
    suite.addTest(TestKeyEndpoints("test_key_endpoints_availability"))
    suite.addTest(TestKeyEndpoints("test_health_endpoint_content"))
    suite.addTest(TestKeyEndpoints("test_auth_register_endpoint"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Key Endpoints Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All key endpoints tests PASSED")
        return True
    else:
        logger.error("Some key endpoints tests FAILED")
        return False

if __name__ == "__main__":
    run_key_endpoints_tests()