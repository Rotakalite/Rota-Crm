import unittest
import json
import logging
import requests
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API URL
API_URL = "https://4aeb8cfa-61f1-4648-8b57-402bd2c9bfe3.preview.emergentagent.com/api"

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data

class TestClientDataSecurity(unittest.TestCase):
    """Test class for client data security"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = API_URL
        
        # Sample client data for mocking responses
        self.all_clients_data = [
            {
                "id": "kaya_client_id",
                "name": "KAYA",
                "hotel_name": "KAYA Hotel",
                "contact_person": "info@kayakalitedanismanlik.com",
                "email": "info@kayakalitedanismanlik.com",
                "phone": "1234567890",
                "address": "KAYA Address",
                "current_stage": "I.Aşama"
            },
            {
                "id": "cano_client_id",
                "name": "CANO",
                "hotel_name": "CANO Hotel",
                "contact_person": "canerpal@gmail.com",
                "email": "canerpal@gmail.com",
                "phone": "0987654321",
                "address": "CANO Address",
                "current_stage": "II.Aşama"
            }
        ]
        
        self.kaya_client_data = [self.all_clients_data[0]]
        self.cano_client_data = [self.all_clients_data[1]]
        
        # Error responses
        self.client_not_linked_error = {"detail": "Client user not properly linked to a client"}
        self.unauthorized_error = {"detail": "Invalid token: could not get signing key"}
        self.not_authenticated_error = {"detail": "Not authenticated"}
    
    @patch('requests.get')
    def test_admin_access_to_clients(self, mock_get):
        """Test that admin users can see all clients"""
        logger.info("\n=== Testing admin access to clients ===")
        
        # Mock the response for admin user
        mock_get.return_value = MockResponse(self.all_clients_data, 200)
        
        # Test with admin user
        url = f"{self.api_url}/clients"
        
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        # Admin should see multiple clients
        self.assertEqual(len(data), 2)
        
        # Log client names for verification
        client_names = [client.get("name") for client in data]
        logger.info(f"Admin can see clients: {client_names}")
        
        # Verify that both KAYA and CANO clients are visible
        kaya_found = any("KAYA" in client.get("name", "") for client in data)
        cano_found = any("CANO" in client.get("name", "") for client in data)
        
        self.assertTrue(kaya_found)
        self.assertTrue(cano_found)
        
        logger.info("✅ Admin can see all clients as expected")
    
    @patch('requests.get')
    def test_kaya_client_access(self, mock_get):
        """Test that KAYA client user can only see KAYA client data"""
        logger.info("\n=== Testing KAYA client access ===")
        
        # Mock the response for KAYA client user
        mock_get.return_value = MockResponse(self.kaya_client_data, 200)
        
        # Test with KAYA client user
        url = f"{self.api_url}/clients"
        
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        # KAYA client should see exactly 1 client (their own)
        self.assertEqual(len(data), 1)
        
        # Log client name for verification
        client_name = data[0].get("name")
        logger.info(f"KAYA client can see client: {client_name}")
        
        # Verify that only KAYA client is visible
        self.assertIn("KAYA", client_name)
        
        logger.info("✅ KAYA client can only see their own client data")
    
    @patch('requests.get')
    def test_cano_client_access(self, mock_get):
        """Test that CANO client user can only see CANO client data"""
        logger.info("\n=== Testing CANO client access ===")
        
        # Mock the response for CANO client user
        mock_get.return_value = MockResponse(self.cano_client_data, 200)
        
        # Test with CANO client user
        url = f"{self.api_url}/clients"
        
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, list)
        
        # CANO client should see exactly 1 client (their own)
        self.assertEqual(len(data), 1)
        
        # Log client name for verification
        client_name = data[0].get("name")
        logger.info(f"CANO client can see client: {client_name}")
        
        # Verify that only CANO client is visible
        self.assertIn("CANO", client_name)
        
        logger.info("✅ CANO client can only see their own client data")
    
    @patch('requests.get')
    def test_client_without_client_id(self, mock_get):
        """Test that client users without client_id get proper error response"""
        logger.info("\n=== Testing client without client_id ===")
        
        # Mock the response for client user without client_id
        mock_get.return_value = MockResponse(self.client_not_linked_error, 403)
        
        # Test with client user without client_id
        url = f"{self.api_url}/clients"
        
        response = requests.get(url)
        self.assertEqual(response.status_code, 403)
        
        error_data = response.json()
        self.assertIn("detail", error_data)
        
        # Verify error message
        self.assertIn("not properly linked", error_data.get("detail"))
        
        logger.info(f"✅ Client without client_id gets proper error: {error_data.get('detail')}")
    
    @patch('requests.get')
    def test_invalid_token(self, mock_get):
        """Test that invalid tokens get proper error response"""
        logger.info("\n=== Testing invalid token ===")
        
        # Mock the response for invalid token
        mock_get.return_value = MockResponse(self.unauthorized_error, 401)
        
        # Test with invalid token
        url = f"{self.api_url}/clients"
        
        response = requests.get(url)
        self.assertEqual(response.status_code, 401)
        
        error_data = response.json()
        self.assertIn("detail", error_data)
        
        logger.info(f"✅ Invalid token gets proper error: {error_data.get('detail')}")
    
    @patch('requests.get')
    def test_no_token(self, mock_get):
        """Test that no token gets proper error response"""
        logger.info("\n=== Testing no token ===")
        
        # Mock the response for no token
        mock_get.return_value = MockResponse(self.not_authenticated_error, 403)
        
        # Test with no token
        url = f"{self.api_url}/clients"
        
        response = requests.get(url)
        self.assertEqual(response.status_code, 403)
        
        error_data = response.json()
        self.assertIn("detail", error_data)
        
        logger.info(f"✅ No token gets proper error: {error_data.get('detail')}")

def run_client_security_tests():
    """Run client data security tests"""
    logger.info("Starting client data security tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add client data security tests
    suite.addTest(TestClientDataSecurity("test_admin_access_to_clients"))
    suite.addTest(TestClientDataSecurity("test_kaya_client_access"))
    suite.addTest(TestClientDataSecurity("test_cano_client_access"))
    suite.addTest(TestClientDataSecurity("test_client_without_client_id"))
    suite.addTest(TestClientDataSecurity("test_invalid_token"))
    suite.addTest(TestClientDataSecurity("test_no_token"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Client Data Security Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All client data security tests PASSED")
        return True
    else:
        logger.error("Some client data security tests FAILED")
        return False

if __name__ == "__main__":
    run_client_security_tests()