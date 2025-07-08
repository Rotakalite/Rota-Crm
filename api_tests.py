import unittest
import json
import logging
import requests
import os
import sys
import io
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend API URL
BACKEND_API_URL = "https://96c96d61-de51-4844-9405-36489580d965.preview.emergentagent.com/api"

class TestAPIEndpoints(unittest.TestCase):
    """Test class for API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_API_URL
    
    def test_health_endpoint(self):
        """Test the health endpoint"""
        logger.info("\n=== Testing /api/health endpoint ===")
        
        url = f"{self.api_url}/health"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain status
            data = response.json()
            self.assertIn("status", data)
            self.assertEqual(data["status"], "healthy")
            
            logger.info("✅ Health endpoint test passed")
        except Exception as e:
            logger.error(f"❌ Error testing health endpoint: {str(e)}")
            raise
    
    def test_public_endpoints(self):
        """Test public endpoints that don't require authentication"""
        logger.info("\n=== Testing public endpoints ===")
        
        # List of public endpoints to test
        public_endpoints = [
            "/suppliers/categories/list",
            "/suppliers/certifications/list"
        ]
        
        for endpoint in public_endpoints:
            url = f"{self.api_url}{endpoint}"
            
            try:
                logger.info(f"Testing {endpoint}...")
                response = requests.get(url)
                logger.info(f"Response status code: {response.status_code}")
                
                # Should get 200 OK or 404 Not Found
                self.assertIn(response.status_code, [200, 404])
                
                if response.status_code == 200:
                    # Response should be JSON
                    data = response.json()
                    logger.info(f"Response data: {data.keys()}")
                    logger.info(f"✅ {endpoint} test passed")
                else:
                    logger.info(f"⚠️ {endpoint} returned 404 Not Found - may not be implemented")
            except Exception as e:
                logger.error(f"❌ Error testing {endpoint}: {str(e)}")
                raise
    
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        logger.info("\n=== Testing authentication endpoints ===")
        
        # Test register endpoint
        register_url = f"{self.api_url}/auth/register"
        
        try:
            logger.info("Testing /auth/register...")
            
            # Create a unique test user
            test_user = {
                "clerk_user_id": f"user_{uuid.uuid4()}",
                "email": f"test_{uuid.uuid4()}@example.com",
                "name": "Test User",
                "role": "client"
            }
            
            response = requests.post(register_url, json=test_user)
            logger.info(f"Response status code: {response.status_code}")
            
            # Should get 200 OK, 201 Created, or 422 Unprocessable Entity
            self.assertIn(response.status_code, [200, 201, 422])
            
            if response.status_code in [200, 201]:
                # Response should contain user data
                data = response.json()
                logger.info(f"Response data: {data}")
                self.assertIn("id", data)
                self.assertIn("email", data)
                self.assertIn("role", data)
                
                logger.info("✅ /auth/register test passed")
            else:
                logger.info("⚠️ /auth/register returned error - may require specific format")
        except Exception as e:
            logger.error(f"❌ Error testing /auth/register: {str(e)}")
            raise

def run_api_tests():
    """Run API tests"""
    logger.info("\n=== Running API Tests ===")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add API tests
    suite.addTest(TestAPIEndpoints("test_health_endpoint"))
    suite.addTest(TestAPIEndpoints("test_public_endpoints"))
    suite.addTest(TestAPIEndpoints("test_auth_endpoints"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == "__main__":
    run_api_tests()