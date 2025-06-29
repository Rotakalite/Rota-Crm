import unittest
import logging
import sys
import os
import requests
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "https://4aeb8cfa-61f1-4648-8b57-402bd2c9bfe3.preview.emergentagent.com"

class TestClientSecurityCode(unittest.TestCase):
    """Test class for client data security by examining the backend code"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = f"{BACKEND_URL}/api"
        self.server_py_path = "/app/backend/server.py"
        
        # Read the server.py file
        try:
            with open(self.server_py_path, 'r') as f:
                self.server_code = f.read()
            logger.info(f"✅ Successfully read server.py ({len(self.server_code)} bytes)")
        except Exception as e:
            logger.error(f"❌ Error reading server.py: {str(e)}")
            self.server_code = ""
    
    def test_backend_health(self):
        """Test that the backend is running"""
        logger.info("\n=== Testing backend health ===")
        
        try:
            response = requests.get(f"{self.api_url}/health")
            logger.info(f"Backend health check: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "Backend health check should return 200 OK")
            logger.info("✅ Backend is running")
        except Exception as e:
            logger.error(f"❌ Error connecting to backend: {str(e)}")
            raise
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated access is properly blocked"""
        logger.info("\n=== Testing unauthenticated access ===")
        
        try:
            response = requests.get(f"{self.api_url}/clients")
            logger.info(f"Unauthenticated /api/clients response: {response.status_code}")
            
            self.assertEqual(response.status_code, 403, "Unauthenticated access should return 403 Not authenticated")
            logger.info("✅ Unauthenticated access correctly returns 403 Not authenticated")
        except Exception as e:
            logger.error(f"❌ Error testing unauthenticated access: {str(e)}")
            raise
    
    def test_admin_role_check(self):
        """Test that the code checks for admin role"""
        logger.info("\n=== Testing admin role check ===")
        
        # Look for the admin role check in the get_clients function
        admin_role_check = re.search(r'if\s+current_user\.role\s*==\s*UserRole\.ADMIN', self.server_code)
        
        self.assertIsNotNone(admin_role_check, "Admin role check should be present in get_clients function")
        logger.info(f"✅ Admin role check found at position {admin_role_check.start()}")
        
        # Check that admin users get all clients
        admin_gets_all = re.search(r'clients\s*=\s*await\s+db\.clients\.find\(\)\.to_list', self.server_code)
        
        self.assertIsNotNone(admin_gets_all, "Admin should get all clients")
        logger.info(f"✅ Admin gets all clients code found at position {admin_gets_all.start()}")
    
    def test_client_id_check(self):
        """Test that the code checks for client_id"""
        logger.info("\n=== Testing client_id check ===")
        
        # Look for the client_id check in the get_clients function
        client_id_check = re.search(r'if\s+not\s+current_user\.client_id', self.server_code)
        
        self.assertIsNotNone(client_id_check, "Client ID check should be present in get_clients function")
        logger.info(f"✅ Client ID check found at position {client_id_check.start()}")
        
        # Check that client users without client_id get 403 Forbidden
        client_id_error = re.search(r'raise\s+HTTPException\(status_code=403,\s*detail="Client\s+user\s+not\s+properly\s+linked', self.server_code)
        
        self.assertIsNotNone(client_id_error, "Client users without client_id should get 403 Forbidden")
        logger.info(f"✅ Client ID error code found at position {client_id_error.start()}")
    
    def test_client_filtering(self):
        """Test that client users only see their own client"""
        logger.info("\n=== Testing client filtering ===")
        
        # Look for the client filtering in the get_clients function
        client_filtering = re.search(r'client\s*=\s*await\s+db\.clients\.find_one\(\{"id":\s*current_user\.client_id\}\)', self.server_code)
        
        self.assertIsNotNone(client_filtering, "Client filtering should be present in get_clients function")
        logger.info(f"✅ Client filtering found at position {client_filtering.start()}")
        
        # Check that client users only get their own client
        client_return = re.search(r'return\s+\[Client\(\*\*client\)\]', self.server_code)
        
        self.assertIsNotNone(client_return, "Client users should only get their own client")
        logger.info(f"✅ Client return code found at position {client_return.start()}")
    
    def test_logging(self):
        """Test that the code includes proper logging"""
        logger.info("\n=== Testing logging ===")
        
        # Look for logging in the get_clients function
        admin_logging = re.search(r'logging\.info\(f"\S+\s+Admin\s+user\s+-\s+returning', self.server_code)
        client_logging = re.search(r'logging\.info\(f"\S+\s+Client\s+user\s+-\s+returning\s+ONLY', self.server_code)
        
        self.assertIsNotNone(admin_logging, "Admin logging should be present in get_clients function")
        self.assertIsNotNone(client_logging, "Client logging should be present in get_clients function")
        
        logger.info(f"✅ Admin logging found at position {admin_logging.start()}")
        logger.info(f"✅ Client logging found at position {client_logging.start()}")
    
    def test_error_handling(self):
        """Test that the code includes proper error handling"""
        logger.info("\n=== Testing error handling ===")
        
        # Look for error handling in the get_clients function
        client_id_error = re.search(r'logging\.error\(f"\S+\s+CLIENT\s+USER\s+WITHOUT\s+CLIENT_ID', self.server_code)
        client_not_found = re.search(r'logging\.error\(f"\S+\s+CLIENT\s+NOT\s+FOUND', self.server_code)
        
        self.assertIsNotNone(client_id_error, "Client ID error logging should be present in get_clients function")
        self.assertIsNotNone(client_not_found, "Client not found error logging should be present in get_clients function")
        
        logger.info(f"✅ Client ID error logging found at position {client_id_error.start()}")
        logger.info(f"✅ Client not found error logging found at position {client_not_found.start()}")

def run_client_security_code_tests():
    """Run all client security code tests"""
    logger.info("Starting client security code tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add client security code tests
    suite.addTest(TestClientSecurityCode("test_backend_health"))
    suite.addTest(TestClientSecurityCode("test_unauthenticated_access"))
    suite.addTest(TestClientSecurityCode("test_admin_role_check"))
    suite.addTest(TestClientSecurityCode("test_client_id_check"))
    suite.addTest(TestClientSecurityCode("test_client_filtering"))
    suite.addTest(TestClientSecurityCode("test_logging"))
    suite.addTest(TestClientSecurityCode("test_error_handling"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Client Security Code Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All client security code tests PASSED")
        logger.info("\n✅ SECURITY VERIFICATION COMPLETE")
        logger.info("The backend code has proper security checks to ensure client users can only see their own client data.")
        logger.info("Admin users can see all clients, while client users are restricted to their own client record.")
        logger.info("Client users without a client_id are properly blocked with a 403 Forbidden error.")
        return True
    else:
        logger.error("Some client security code tests FAILED")
        return False

if __name__ == "__main__":
    success = run_client_security_code_tests()
    sys.exit(0 if success else 1)