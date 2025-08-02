import unittest
import json
import logging
import requests
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestHealthEndpoint(unittest.TestCase):
    """Test class for the health endpoint"""
    
    def setUp(self):
        """Set up test environment"""
        # Use the Railway backend URL from frontend .env
        self.api_url = "https://rota-crm-production.up.railway.app/api"
        
        # Origin headers for CORS testing
        self.origins = [
            "https://portal.rotakalitedanismanlik.com",
            "https://rota-r4invvuue-rotas-projects-62181e6e.vercel.app",
            "https://d787e851-4fbb-4d90-a594-90394e6ba15e.preview.emergentagent.com"
        ]
        
    def test_health_endpoint_basic(self):
        """Test basic functionality of the health endpoint"""
        logger.info("\n=== Testing basic functionality of health endpoint ===")
        
        url = f"{self.api_url}/health"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            # Health endpoint should be accessible without authentication
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn("status", data)
            self.assertIn("service", data)
            self.assertIn("timestamp", data)
            
            # Check specific values
            self.assertEqual(data["status"], "healthy")
            self.assertEqual(data["service"], "Rota CRM Backend")
            
            # Check timestamp format
            try:
                datetime.fromisoformat(data["timestamp"])
                logger.info("✅ Timestamp is in valid ISO format")
            except ValueError:
                self.fail("Timestamp is not in valid ISO format")
            
            logger.info("✅ Health endpoint basic test passed")
            
        except Exception as e:
            logger.error(f"❌ Error testing health endpoint: {str(e)}")
            raise
    
    def test_health_endpoint_performance(self):
        """Test performance of the health endpoint"""
        logger.info("\n=== Testing performance of health endpoint ===")
        
        url = f"{self.api_url}/health"
        
        try:
            # Test response time
            start_time = datetime.now()
            for _ in range(5):
                response = requests.get(url)
                self.assertEqual(response.status_code, 200)
            end_time = datetime.now()
            avg_time = (end_time - start_time).total_seconds() / 5
            
            logger.info(f"Average response time: {avg_time:.3f} seconds")
            self.assertLess(avg_time, 1.0, "Health endpoint should respond in less than 1 second")
            
            logger.info("✅ Health endpoint performance test passed")
            
        except Exception as e:
            logger.error(f"❌ Error testing health endpoint performance: {str(e)}")
            raise
    
    def test_health_endpoint_cors(self):
        """Test CORS configuration of the health endpoint"""
        logger.info("\n=== Testing CORS configuration of health endpoint ===")
        
        url = f"{self.api_url}/health"
        
        for origin in self.origins:
            logger.info(f"Testing with origin: {origin}")
            
            try:
                # Test OPTIONS preflight request
                response = requests.options(
                    url, 
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "GET",
                        "Access-Control-Request-Headers": "Content-Type"
                    }
                )
                
                logger.info(f"Preflight response status code: {response.status_code}")
                logger.info(f"Preflight CORS headers: {response.headers.get('Access-Control-Allow-Origin', 'None')}")
                
                # Preflight should return 200 OK
                self.assertEqual(response.status_code, 200)
                
                # Check CORS headers
                self.assertIn("Access-Control-Allow-Origin", response.headers)
                self.assertIn("Access-Control-Allow-Methods", response.headers)
                self.assertIn("Access-Control-Allow-Headers", response.headers)
                
                # Check if origin is allowed
                allow_origin = response.headers.get("Access-Control-Allow-Origin")
                self.assertTrue(
                    allow_origin == "*" or allow_origin == origin,
                    f"Origin {origin} should be allowed"
                )
                
                # Test actual request
                response = requests.get(
                    url, 
                    headers={
                        "Origin": origin
                    }
                )
                
                logger.info(f"Actual response status code: {response.status_code}")
                logger.info(f"Actual CORS headers: {response.headers.get('Access-Control-Allow-Origin', 'None')}")
                
                # Actual request should return 200 OK
                self.assertEqual(response.status_code, 200)
                
                # Check CORS headers
                self.assertIn("Access-Control-Allow-Origin", response.headers)
                
                # Check if origin is allowed
                allow_origin = response.headers.get("Access-Control-Allow-Origin")
                self.assertTrue(
                    allow_origin == "*" or allow_origin == origin,
                    f"Origin {origin} should be allowed"
                )
                
                logger.info(f"✅ CORS test passed for origin: {origin}")
                
            except Exception as e:
                logger.error(f"❌ Error testing CORS for origin {origin}: {str(e)}")
                raise
    
    def test_health_endpoint_content(self):
        """Test content of the health endpoint response"""
        logger.info("\n=== Testing content of health endpoint response ===")
        
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
            
            # Check content type header
            self.assertEqual(response.headers.get("Content-Type"), "application/json")
            
            logger.info("✅ Health endpoint content test passed")
            
        except Exception as e:
            logger.error(f"❌ Error testing health endpoint content: {str(e)}")
            raise

def run_health_endpoint_tests():
    """Run health endpoint tests"""
    logger.info("Starting health endpoint tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add health endpoint tests
    suite.addTest(TestHealthEndpoint("test_health_endpoint_basic"))
    suite.addTest(TestHealthEndpoint("test_health_endpoint_performance"))
    suite.addTest(TestHealthEndpoint("test_health_endpoint_cors"))
    suite.addTest(TestHealthEndpoint("test_health_endpoint_content"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Health Endpoint Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All health endpoint tests PASSED")
        return True
    else:
        logger.error("Some health endpoint tests FAILED")
        return False

if __name__ == "__main__":
    run_health_endpoint_tests()