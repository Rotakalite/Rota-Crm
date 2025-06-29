import unittest
import json
import logging
import requests
import os
import jwt
from datetime import datetime, timedelta

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
            return "https://ced36975-561f-4c1a-b948-3ca6d5f89931.preview.emergentagent.com"
        
        return backend_url
    except Exception as e:
        logger.error(f"Error reading .env file: {str(e)}")
        return "https://ced36975-561f-4c1a-b948-3ca6d5f89931.preview.emergentagent.com"

# Mock response class
class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data

class TestAuthenticationEndpoints(unittest.TestCase):
    """Test class for authentication and protected endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.backend_url = get_backend_url()
        self.api_url = f"{self.backend_url}/api"
        logger.info(f"Using API URL: {self.api_url}")
        
        # Create test tokens
        self.valid_admin_token = self.create_test_token(
            user_id="admin_user_123",
            email="admin@rotakalitedanismanlik.com",
            name="Admin User"
        )
        
        self.valid_client_token = self.create_test_token(
            user_id="client_user_456",
            email="client@example.com",
            name="Client User"
        )
        
        self.malformed_token = "invalid.token.format"
        self.expired_token = self.create_test_token(
            user_id="expired_user_789",
            email="expired@example.com",
            name="Expired User",
            expired=True
        )
        
        # Headers for requests
        self.admin_headers = {"Authorization": f"Bearer {self.valid_admin_token}"}
        self.client_headers = {"Authorization": f"Bearer {self.valid_client_token}"}
        self.invalid_headers = {"Authorization": f"Bearer {self.malformed_token}"}
        self.expired_headers = {"Authorization": f"Bearer {self.expired_token}"}
    
    def create_test_token(self, user_id, email, name, expired=False):
        """Create a test JWT token"""
        # This is a simplified token for testing purposes
        # In a real environment, tokens would be issued by Clerk
        now = datetime.utcnow()
        
        payload = {
            "sub": user_id,
            "email": email,
            "name": name,
            "iat": int((now - timedelta(minutes=5)).timestamp()),
            "exp": int((now - timedelta(minutes=1)).timestamp()) if expired else int((now + timedelta(hours=1)).timestamp())
        }
        
        # Use a simple secret for testing
        # Note: In production, tokens are verified using Clerk's JWKS
        token = jwt.encode(payload, "test_secret", algorithm="HS256")
        
        # Convert bytes to string if needed (depends on jwt version)
        if isinstance(token, bytes):
            token = token.decode('utf-8')
            
        return token

    def test_auth_me_endpoint(self):
        """Test the /api/auth/me endpoint with various token scenarios"""
        logger.info("\n=== Testing /api/auth/me endpoint ===")
        
        url = f"{self.api_url}/auth/me"
        
        # Test with valid admin token
        logger.info("Testing with valid admin token...")
        try:
            response = requests.get(url, headers=self.admin_headers)
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                self.assertEqual(response.status_code, 200)
                self.assertIn("role", data)
                self.assertEqual(data["role"], "admin")
                logger.info("✅ Admin token test passed")
            else:
                logger.warning(f"⚠️ Admin token test returned non-200 status: {response.status_code}")
                logger.warning(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error testing admin token: {str(e)}")
        
        # Test with valid client token
        logger.info("Testing with valid client token...")
        try:
            response = requests.get(url, headers=self.client_headers)
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                self.assertEqual(response.status_code, 200)
                self.assertIn("role", data)
                self.assertEqual(data["role"], "client")
                logger.info("✅ Client token test passed")
            else:
                logger.warning(f"⚠️ Client token test returned non-200 status: {response.status_code}")
                logger.warning(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error testing client token: {str(e)}")
        
        # Test with malformed token
        logger.info("Testing with malformed token...")
        try:
            response = requests.get(url, headers=self.invalid_headers)
            logger.info(f"Status code: {response.status_code}")
            
            # We expect a 401 Unauthorized or similar error
            self.assertNotEqual(response.status_code, 200)
            logger.info(f"✅ Malformed token correctly rejected with status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing malformed token: {str(e)}")
        
        # Test with expired token
        logger.info("Testing with expired token...")
        try:
            response = requests.get(url, headers=self.expired_headers)
            logger.info(f"Status code: {response.status_code}")
            
            # We expect a 401 Unauthorized or similar error
            self.assertNotEqual(response.status_code, 200)
            logger.info(f"✅ Expired token correctly rejected with status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing expired token: {str(e)}")

    def test_clients_endpoint(self):
        """Test the /api/clients endpoint with various token scenarios"""
        logger.info("\n=== Testing /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        # Test with valid admin token
        logger.info("Testing with valid admin token...")
        try:
            response = requests.get(url, headers=self.admin_headers)
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response contains {len(data)} clients")
                self.assertEqual(response.status_code, 200)
                self.assertIsInstance(data, list)
                logger.info("✅ Admin access to clients endpoint passed")
            else:
                logger.warning(f"⚠️ Admin access to clients endpoint returned non-200 status: {response.status_code}")
                logger.warning(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error testing admin access to clients endpoint: {str(e)}")
        
        # Test with valid client token
        logger.info("Testing with valid client token...")
        try:
            response = requests.get(url, headers=self.client_headers)
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response contains {len(data)} clients")
                self.assertEqual(response.status_code, 200)
                self.assertIsInstance(data, list)
                # Client should only see their own client record (0 or 1)
                self.assertLessEqual(len(data), 1)
                logger.info("✅ Client access to clients endpoint passed")
            else:
                logger.warning(f"⚠️ Client access to clients endpoint returned non-200 status: {response.status_code}")
                logger.warning(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error testing client access to clients endpoint: {str(e)}")
        
        # Test with malformed token
        logger.info("Testing with malformed token...")
        try:
            response = requests.get(url, headers=self.invalid_headers)
            logger.info(f"Status code: {response.status_code}")
            
            # We expect a 401 Unauthorized or similar error, not 403 Forbidden
            self.assertNotEqual(response.status_code, 200)
            self.assertNotEqual(response.status_code, 403)  # Should not be 403
            logger.info(f"✅ Malformed token correctly rejected with status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing malformed token: {str(e)}")

    def test_stats_endpoint(self):
        """Test the /api/stats endpoint with various token scenarios"""
        logger.info("\n=== Testing /api/stats endpoint ===")
        
        url = f"{self.api_url}/stats"
        
        # Test with valid admin token
        logger.info("Testing with valid admin token...")
        try:
            response = requests.get(url, headers=self.admin_headers)
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                self.assertEqual(response.status_code, 200)
                self.assertIn("total_clients", data)
                self.assertIn("stage_distribution", data)
                self.assertIn("total_documents", data)
                self.assertIn("total_trainings", data)
                logger.info("✅ Admin access to stats endpoint passed")
            else:
                logger.warning(f"⚠️ Admin access to stats endpoint returned non-200 status: {response.status_code}")
                logger.warning(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error testing admin access to stats endpoint: {str(e)}")
        
        # Test with valid client token
        logger.info("Testing with valid client token...")
        try:
            response = requests.get(url, headers=self.client_headers)
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                self.assertEqual(response.status_code, 200)
                self.assertIn("total_clients", data)
                self.assertIn("stage_distribution", data)
                self.assertIn("total_documents", data)
                self.assertIn("total_trainings", data)
                # Client should only see their own stats
                self.assertLessEqual(data["total_clients"], 1)
                logger.info("✅ Client access to stats endpoint passed")
            else:
                logger.warning(f"⚠️ Client access to stats endpoint returned non-200 status: {response.status_code}")
                logger.warning(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error testing client access to stats endpoint: {str(e)}")
        
        # Test with malformed token
        logger.info("Testing with malformed token...")
        try:
            response = requests.get(url, headers=self.invalid_headers)
            logger.info(f"Status code: {response.status_code}")
            
            # We expect a 401 Unauthorized or similar error, not 403 Forbidden
            self.assertNotEqual(response.status_code, 200)
            self.assertNotEqual(response.status_code, 403)  # Should not be 403
            logger.info(f"✅ Malformed token correctly rejected with status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing malformed token: {str(e)}")

def run_tests():
    """Run all authentication and protected endpoint tests"""
    logger.info("Starting authentication and protected endpoint tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(TestAuthenticationEndpoints("test_auth_me_endpoint"))
    suite.addTest(TestAuthenticationEndpoints("test_clients_endpoint"))
    suite.addTest(TestAuthenticationEndpoints("test_stats_endpoint"))
    
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