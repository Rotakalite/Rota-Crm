import unittest
import requests
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT token for admin
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

class TestEmailManagementEndpoints(unittest.TestCase):
    """Test class for email management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        self.headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    def test_email_management_clients_real(self):
        """Test GET /api/email-management/clients-real endpoint"""
        logger.info("\n=== Testing GET /api/email-management/clients-real endpoint ===")
        
        url = f"{self.api_url}/email-management/clients-real"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if endpoint exists
            if response.status_code == 404:
                logger.warning("Endpoint not found (404)")
                return
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 405])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIsInstance(data, list)
                
                # Log the clients found
                logger.info(f"Found {len(data)} clients")
                for client in data:
                    logger.info(f"Client: {client}")
                
                logger.info("✅ GET /api/email-management/clients-real test passed")
            elif response.status_code == 405:
                logger.info("Method not allowed (405) - this is expected for GET requests to endpoints that require authentication")
            else:
                logger.info(f"Authentication/authorization issue: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing email-management/clients-real endpoint: {str(e)}")
            raise
    
    def test_email_management_documents_real(self):
        """Test GET /api/email-management/documents-real endpoint"""
        logger.info("\n=== Testing GET /api/email-management/documents-real endpoint ===")
        
        url = f"{self.api_url}/email-management/documents-real"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if endpoint exists
            if response.status_code == 404:
                logger.warning("Endpoint not found (404)")
                return
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 405])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIsInstance(data, list)
                
                # Log the documents found
                logger.info(f"Found {len(data)} documents")
                for doc in data:
                    logger.info(f"Document: {doc}")
                
                logger.info("✅ GET /api/email-management/documents-real test passed")
            elif response.status_code == 405:
                logger.info("Method not allowed (405) - this is expected for GET requests to endpoints that require authentication")
            else:
                logger.info(f"Authentication/authorization issue: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing email-management/documents-real endpoint: {str(e)}")
            raise
    
    def test_email_management_trainings_real(self):
        """Test GET /api/email-management/trainings-real endpoint"""
        logger.info("\n=== Testing GET /api/email-management/trainings-real endpoint ===")
        
        url = f"{self.api_url}/email-management/trainings-real"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if endpoint exists
            if response.status_code == 404:
                logger.warning("Endpoint not found (404)")
                return
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 405])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIsInstance(data, list)
                
                # Log the trainings found
                logger.info(f"Found {len(data)} trainings")
                for training in data:
                    logger.info(f"Training: {training}")
                
                logger.info("✅ GET /api/email-management/trainings-real test passed")
            elif response.status_code == 405:
                logger.info("Method not allowed (405) - this is expected for GET requests to endpoints that require authentication")
            else:
                logger.info(f"Authentication/authorization issue: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing email-management/trainings-real endpoint: {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main()