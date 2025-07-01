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

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestURLConfiguration(unittest.TestCase):
    """Test class for URL configuration and CORS settings"""
    
    def setUp(self):
        """Set up test environment"""
        # Use the Railway backend URL from frontend .env
        self.api_url = "https://rota-crm-production.up.railway.app/api"
        self.headers_valid = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        
        # Origin headers for CORS testing
        self.origin_headers = {
            "Origin": "https://portal.rotakalitedanismanlik.com"
        }
        self.vercel_origin_headers = {
            "Origin": "https://rota-r4invvuue-rotas-projects-62181e6e.vercel.app"
        }
        self.emergent_origin_headers = {
            "Origin": "https://9f48b84c-034b-45a8-ad5e-21ebcb0ee2a7.preview.emergentagent.com"
        }
        
    def test_health_endpoint(self):
        """Test the /api/health endpoint"""
        logger.info("\n=== Testing /api/health endpoint ===")
        
        url = f"{self.api_url}/health"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Health endpoint should be accessible without authentication
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn("status", data)
            self.assertIn("service", data)
            self.assertIn("timestamp", data)
            
            logger.info("✅ Health endpoint test passed")
            
            # Test response time
            start_time = datetime.now()
            for _ in range(3):
                requests.get(url)
            end_time = datetime.now()
            avg_time = (end_time - start_time).total_seconds() / 3
            
            logger.info(f"Average response time: {avg_time:.3f} seconds")
            self.assertLess(avg_time, 1.0, "Health endpoint should respond in less than 1 second")
            
            logger.info("✅ Health endpoint performance test passed")
            
        except Exception as e:
            logger.error(f"❌ Error testing health endpoint: {str(e)}")
            raise
    
    def test_cors_preflight_requests(self):
        """Test CORS preflight requests for critical endpoints"""
        logger.info("\n=== Testing CORS preflight requests ===")
        
        # Test endpoints
        endpoints = [
            "/auth/register",
            "/stats",
            "/clients"
        ]
        
        # Test with different origins
        origins = [
            self.origin_headers,
            self.vercel_origin_headers,
            self.emergent_origin_headers
        ]
        
        for endpoint in endpoints:
            for origin in origins:
                url = f"{self.api_url}{endpoint}"
                origin_name = origin.get("Origin", "Unknown")
                
                logger.info(f"Testing OPTIONS preflight for {url} with origin {origin_name}")
                
                try:
                    # Send OPTIONS preflight request
                    response = requests.options(
                        url, 
                        headers={
                            **origin,
                            "Access-Control-Request-Method": "GET",
                            "Access-Control-Request-Headers": "Content-Type, Authorization"
                        }
                    )
                    
                    logger.info(f"Response status code: {response.status_code}")
                    logger.info(f"CORS headers: {response.headers.get('Access-Control-Allow-Origin', 'None')}")
                    
                    # Preflight should return 200 OK
                    self.assertEqual(response.status_code, 200)
                    
                    # Check CORS headers
                    self.assertIn("Access-Control-Allow-Origin", response.headers)
                    self.assertIn("Access-Control-Allow-Methods", response.headers)
                    self.assertIn("Access-Control-Allow-Headers", response.headers)
                    
                    # Check if origin is allowed
                    allow_origin = response.headers.get("Access-Control-Allow-Origin")
                    self.assertTrue(
                        allow_origin == "*" or allow_origin == origin.get("Origin"),
                        f"Origin {origin.get('Origin')} should be allowed"
                    )
                    
                    logger.info(f"✅ CORS preflight test passed for {endpoint} with origin {origin_name}")
                    
                except Exception as e:
                    logger.error(f"❌ Error testing CORS preflight for {endpoint} with origin {origin_name}: {str(e)}")
                    raise
    
    def test_actual_cors_requests(self):
        """Test actual CORS requests for critical endpoints"""
        logger.info("\n=== Testing actual CORS requests ===")
        
        # Test endpoints
        endpoints = [
            "/auth/register",
            "/stats",
            "/clients"
        ]
        
        # Test with different origins
        origins = [
            self.origin_headers,
            self.vercel_origin_headers,
            self.emergent_origin_headers
        ]
        
        for endpoint in endpoints:
            for origin in origins:
                url = f"{self.api_url}{endpoint}"
                origin_name = origin.get("Origin", "Unknown")
                
                logger.info(f"Testing actual request for {url} with origin {origin_name}")
                
                try:
                    # Send actual request
                    response = requests.get(
                        url, 
                        headers={
                            **origin,
                            **self.headers_valid
                        }
                    )
                    
                    logger.info(f"Response status code: {response.status_code}")
                    logger.info(f"CORS headers: {response.headers.get('Access-Control-Allow-Origin', 'None')}")
                    
                    # Check CORS headers in actual response
                    self.assertIn("Access-Control-Allow-Origin", response.headers)
                    
                    # Check if origin is allowed
                    allow_origin = response.headers.get("Access-Control-Allow-Origin")
                    self.assertTrue(
                        allow_origin == "*" or allow_origin == origin.get("Origin"),
                        f"Origin {origin.get('Origin')} should be allowed"
                    )
                    
                    logger.info(f"✅ Actual CORS request test passed for {endpoint} with origin {origin_name}")
                    
                except Exception as e:
                    logger.error(f"❌ Error testing actual CORS request for {endpoint} with origin {origin_name}: {str(e)}")
                    raise
    
    def test_key_endpoints(self):
        """Test key endpoints with the Railway backend URL"""
        logger.info("\n=== Testing key endpoints with Railway backend URL ===")
        
        # Test endpoints
        endpoints = [
            "/health",
            "/stats",
            "/clients"
        ]
        
        for endpoint in endpoints:
            url = f"{self.api_url}{endpoint}"
            
            logger.info(f"Testing endpoint: {url}")
            
            try:
                # Send request with valid token
                response = requests.get(url, headers=self.headers_valid)
                
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response body: {response.text[:100]}...")
                
                # Check if endpoint is accessible
                self.assertIn(response.status_code, [200, 401])
                
                if response.status_code == 200:
                    logger.info(f"✅ Endpoint {endpoint} is accessible")
                elif response.status_code == 401:
                    logger.info(f"✅ Endpoint {endpoint} requires valid authentication")
                
            except Exception as e:
                logger.error(f"❌ Error testing endpoint {endpoint}: {str(e)}")
                raise
        
        # Test POST endpoint separately
        post_url = f"{self.api_url}/auth/register"
        logger.info(f"Testing POST endpoint: {post_url}")
        
        try:
            # Create test user data
            test_user = {
                "clerk_user_id": "test_clerk_id",
                "email": "test@example.com",
                "name": "Test User",
                "role": "client"
            }
            
            # Send POST request
            response = requests.post(post_url, json=test_user, headers=self.headers_valid)
            
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:100]}...")
            
            # Check if endpoint is accessible (200 OK, 401 Unauthorized, or 422 Validation Error)
            self.assertIn(response.status_code, [200, 201, 401, 422])
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ POST endpoint {post_url} is accessible")
            elif response.status_code == 401:
                logger.info(f"✅ POST endpoint {post_url} requires valid authentication")
            elif response.status_code == 422:
                logger.info(f"✅ POST endpoint {post_url} validation working correctly")
                
        except Exception as e:
            logger.error(f"❌ Error testing POST endpoint {post_url}: {str(e)}")
            raise
    
    def test_authentication(self):
        """Test authentication with the Railway backend URL"""
        logger.info("\n=== Testing authentication with Railway backend URL ===")
        
        # Test endpoint that requires authentication
        url = f"{self.api_url}/clients"
        
        try:
            # Test with valid token
            logger.info("Testing with valid token...")
            response = requests.get(url, headers=self.headers_valid)
            
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:100]}...")
            
            # Should get 200 OK or 401 Unauthorized (if token is expired)
            self.assertIn(response.status_code, [200, 401])
            
            # Test with invalid token
            logger.info("Testing with invalid token...")
            response = requests.get(url, headers=self.headers_invalid)
            
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:100]}...")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            # Test without token
            logger.info("Testing without token...")
            response = requests.get(url)
            
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:100]}...")
            
            # Should get 401 Unauthorized or 403 Forbidden
            self.assertIn(response.status_code, [401, 403])
            
            logger.info("✅ Authentication test passed")
            
        except Exception as e:
            logger.error(f"❌ Error testing authentication: {str(e)}")
            raise

def run_url_configuration_tests():
    """Run URL configuration and CORS tests"""
    logger.info("Starting URL configuration and CORS tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add URL configuration and CORS tests
    suite.addTest(TestURLConfiguration("test_health_endpoint"))
    suite.addTest(TestURLConfiguration("test_cors_preflight_requests"))
    suite.addTest(TestURLConfiguration("test_actual_cors_requests"))
    suite.addTest(TestURLConfiguration("test_key_endpoints"))
    suite.addTest(TestURLConfiguration("test_authentication"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== URL Configuration and CORS Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All URL configuration and CORS tests PASSED")
        return True
    else:
        logger.error("Some URL configuration and CORS tests FAILED")
        return False

if __name__ == "__main__":
    run_url_configuration_tests()