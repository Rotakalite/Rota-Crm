import unittest
import requests
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test data
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestCORSConfiguration(unittest.TestCase):
    """Test class for CORS configuration"""
    
    def setUp(self):
        """Set up test environment"""
        # Use the updated backend URL from frontend/.env
        self.api_url = "https://ddbdf62a-0dc7-4cf4-b9a6-6dc3e3277ae1.preview.emergentagent.com/api"
        self.headers_valid = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        
        # Headers for CORS preflight requests
        self.preflight_headers = {
            "Origin": "https://rota-r4invvuue-rotas-projects-62181e6e.vercel.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type"
        }
        
        # Sample user data for registration
        self.user_data = {
            "clerk_user_id": "user_test123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "client"
        }
    
    def test_cors_preflight_auth_register(self):
        """Test CORS preflight request for /api/auth/register endpoint"""
        logger.info("\n=== Testing CORS preflight for /api/auth/register endpoint ===")
        
        url = f"{self.api_url}/auth/register"
        
        try:
            # Send OPTIONS request to simulate preflight
            response = requests.options(url, headers=self.preflight_headers)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Check status code (should be 200 for preflight)
            self.assertEqual(response.status_code, 200, "Preflight request should return 200 OK")
            
            # Check CORS headers
            self.assertIn("Access-Control-Allow-Origin", response.headers, "Missing Access-Control-Allow-Origin header")
            self.assertIn("Access-Control-Allow-Methods", response.headers, "Missing Access-Control-Allow-Methods header")
            self.assertIn("Access-Control-Allow-Headers", response.headers, "Missing Access-Control-Allow-Headers header")
            
            # Check if Origin is allowed
            origin_header = response.headers.get("Access-Control-Allow-Origin")
            self.assertTrue(origin_header == "*" or origin_header == self.preflight_headers["Origin"], 
                           f"Origin not allowed: {origin_header}")
            
            # Check if POST method is allowed (either explicitly or via wildcard)
            methods_header = response.headers.get("Access-Control-Allow-Methods")
            self.assertTrue(methods_header == "*" or "POST" in methods_header.split(",") if "," in methods_header else [methods_header], 
                         f"POST method not allowed: {methods_header}")
            
            logger.info("✅ CORS preflight test passed for /api/auth/register")
        except Exception as e:
            logger.error(f"❌ Error testing CORS preflight for /api/auth/register: {str(e)}")
            raise
    
    def test_cors_preflight_stats(self):
        """Test CORS preflight request for /api/stats endpoint"""
        logger.info("\n=== Testing CORS preflight for /api/stats endpoint ===")
        
        url = f"{self.api_url}/stats"
        
        try:
            # Send OPTIONS request to simulate preflight
            response = requests.options(url, headers=self.preflight_headers)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Check status code (should be 200 for preflight)
            self.assertEqual(response.status_code, 200, "Preflight request should return 200 OK")
            
            # Check CORS headers
            self.assertIn("Access-Control-Allow-Origin", response.headers, "Missing Access-Control-Allow-Origin header")
            self.assertIn("Access-Control-Allow-Methods", response.headers, "Missing Access-Control-Allow-Methods header")
            self.assertIn("Access-Control-Allow-Headers", response.headers, "Missing Access-Control-Allow-Headers header")
            
            # Check if Origin is allowed
            origin_header = response.headers.get("Access-Control-Allow-Origin")
            self.assertTrue(origin_header == "*" or origin_header == self.preflight_headers["Origin"], 
                           f"Origin not allowed: {origin_header}")
            
            # Check if GET method is allowed
            methods_header = response.headers.get("Access-Control-Allow-Methods")
            self.assertIn("GET", methods_header.split(",") if "," in methods_header else [methods_header], 
                         f"GET method not allowed: {methods_header}")
            
            logger.info("✅ CORS preflight test passed for /api/stats")
        except Exception as e:
            logger.error(f"❌ Error testing CORS preflight for /api/stats: {str(e)}")
            raise
    
    def test_cors_preflight_clients(self):
        """Test CORS preflight request for /api/clients endpoint"""
        logger.info("\n=== Testing CORS preflight for /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            # Send OPTIONS request to simulate preflight
            response = requests.options(url, headers=self.preflight_headers)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Check status code (should be 200 for preflight)
            self.assertEqual(response.status_code, 200, "Preflight request should return 200 OK")
            
            # Check CORS headers
            self.assertIn("Access-Control-Allow-Origin", response.headers, "Missing Access-Control-Allow-Origin header")
            self.assertIn("Access-Control-Allow-Methods", response.headers, "Missing Access-Control-Allow-Methods header")
            self.assertIn("Access-Control-Allow-Headers", response.headers, "Missing Access-Control-Allow-Headers header")
            
            # Check if Origin is allowed
            origin_header = response.headers.get("Access-Control-Allow-Origin")
            self.assertTrue(origin_header == "*" or origin_header == self.preflight_headers["Origin"], 
                           f"Origin not allowed: {origin_header}")
            
            # Check if GET method is allowed
            methods_header = response.headers.get("Access-Control-Allow-Methods")
            self.assertIn("GET", methods_header.split(",") if "," in methods_header else [methods_header], 
                         f"GET method not allowed: {methods_header}")
            
            logger.info("✅ CORS preflight test passed for /api/clients")
        except Exception as e:
            logger.error(f"❌ Error testing CORS preflight for /api/clients: {str(e)}")
            raise
    
    def test_auth_register_endpoint(self):
        """Test the /api/auth/register endpoint with CORS headers"""
        logger.info("\n=== Testing /api/auth/register endpoint with CORS headers ===")
        
        url = f"{self.api_url}/auth/register"
        
        try:
            # Add Origin header to simulate cross-origin request
            headers = {
                "Origin": "https://rota-r4invvuue-rotas-projects-62181e6e.vercel.app",
                "Content-Type": "application/json"
            }
            
            # Send POST request
            response = requests.post(url, headers=headers, json=self.user_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Check CORS headers in response
            self.assertIn("Access-Control-Allow-Origin", response.headers, "Missing Access-Control-Allow-Origin header")
            
            # Check if Origin is allowed
            origin_header = response.headers.get("Access-Control-Allow-Origin")
            self.assertTrue(origin_header == "*" or origin_header == headers["Origin"], 
                           f"Origin not allowed: {origin_header}")
            
            # Status code could be 200 (success) or 4xx/5xx (error), but CORS headers should still be present
            logger.info(f"Response status: {response.status_code}, CORS headers present")
            logger.info("✅ CORS headers test passed for /api/auth/register")
        except Exception as e:
            logger.error(f"❌ Error testing CORS headers for /api/auth/register: {str(e)}")
            raise
    
    def test_stats_endpoint(self):
        """Test the /api/stats endpoint with CORS headers"""
        logger.info("\n=== Testing /api/stats endpoint with CORS headers ===")
        
        url = f"{self.api_url}/stats"
        
        try:
            # Add Origin header to simulate cross-origin request
            headers = {
                "Origin": "https://rota-r4invvuue-rotas-projects-62181e6e.vercel.app",
                "Authorization": f"Bearer {VALID_JWT_TOKEN}"
            }
            
            # Send GET request
            response = requests.get(url, headers=headers)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Check CORS headers in response
            self.assertIn("Access-Control-Allow-Origin", response.headers, "Missing Access-Control-Allow-Origin header")
            
            # Check if Origin is allowed
            origin_header = response.headers.get("Access-Control-Allow-Origin")
            self.assertTrue(origin_header == "*" or origin_header == headers["Origin"], 
                           f"Origin not allowed: {origin_header}")
            
            # Status code could be 200 (success) or 401 (unauthorized), but CORS headers should still be present
            logger.info(f"Response status: {response.status_code}, CORS headers present")
            logger.info("✅ CORS headers test passed for /api/stats")
        except Exception as e:
            logger.error(f"❌ Error testing CORS headers for /api/stats: {str(e)}")
            raise
    
    def test_clients_endpoint(self):
        """Test the /api/clients endpoint with CORS headers"""
        logger.info("\n=== Testing /api/clients endpoint with CORS headers ===")
        
        url = f"{self.api_url}/clients"
        
        try:
            # Add Origin header to simulate cross-origin request
            headers = {
                "Origin": "https://rota-r4invvuue-rotas-projects-62181e6e.vercel.app",
                "Authorization": f"Bearer {VALID_JWT_TOKEN}"
            }
            
            # Send GET request
            response = requests.get(url, headers=headers)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Check CORS headers in response
            self.assertIn("Access-Control-Allow-Origin", response.headers, "Missing Access-Control-Allow-Origin header")
            
            # Check if Origin is allowed
            origin_header = response.headers.get("Access-Control-Allow-Origin")
            self.assertTrue(origin_header == "*" or origin_header == headers["Origin"], 
                           f"Origin not allowed: {origin_header}")
            
            # Status code could be 200 (success) or 401 (unauthorized), but CORS headers should still be present
            logger.info(f"Response status: {response.status_code}, CORS headers present")
            logger.info("✅ CORS headers test passed for /api/clients")
        except Exception as e:
            logger.error(f"❌ Error testing CORS headers for /api/clients: {str(e)}")
            raise
    
    def test_url_configuration(self):
        """Test that the backend is accessible via the correct URL"""
        logger.info("\n=== Testing backend URL configuration ===")
        
        # Test the root endpoint
        url = f"{self.api_url}"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            
            # Should get a successful response (200 OK) or 404 Not Found or 405 Method Not Allowed
            # All of these indicate the server is accessible
            self.assertIn(response.status_code, [200, 404, 405], 
                         f"Backend URL not accessible: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Backend URL is accessible")
            elif response.status_code in [404, 405]:
                # 404/405 is acceptable for the root endpoint if it's not defined or doesn't allow GET
                # Try a known endpoint with OPTIONS which should always work with CORS
                known_url = f"{self.api_url}/stats"
                known_response = requests.options(known_url)
                self.assertEqual(known_response.status_code, 200, 
                                "Known endpoint not accessible with OPTIONS request")
                logger.info(f"✅ Backend URL is accessible (root returns {response.status_code} but known endpoint works)")
        except Exception as e:
            logger.error(f"❌ Error testing backend URL configuration: {str(e)}")
            raise

def run_cors_tests():
    """Run all CORS configuration tests"""
    logger.info("Starting CORS configuration tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add CORS configuration tests
    suite.addTest(TestCORSConfiguration("test_cors_preflight_auth_register"))
    suite.addTest(TestCORSConfiguration("test_cors_preflight_stats"))
    suite.addTest(TestCORSConfiguration("test_cors_preflight_clients"))
    suite.addTest(TestCORSConfiguration("test_auth_register_endpoint"))
    suite.addTest(TestCORSConfiguration("test_stats_endpoint"))
    suite.addTest(TestCORSConfiguration("test_clients_endpoint"))
    suite.addTest(TestCORSConfiguration("test_url_configuration"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== CORS Configuration Test Summary ===")
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
    run_cors_tests()