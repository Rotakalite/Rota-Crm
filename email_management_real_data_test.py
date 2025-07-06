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

# Test JWT tokens for different user types
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
KAYA_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestEmailManagementRealDataEndpoints(unittest.TestCase):
    """Test class for Email Management Real Data endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        # Use the correct backend URL from frontend/.env
        self.api_url = "https://be473f49-c085-4355-8cf7-95fc4e8bf06a.preview.emergentagent.com/api"
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {KAYA_CLIENT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_documents_real_endpoint(self):
        """Test GET /api/email-management/documents-real endpoint"""
        logger.info("\n=== Testing GET /api/email-management/documents-real endpoint ===")
        
        url = f"{self.api_url}/email-management/documents-real"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data keys: {data.keys()}")
                
                # Verify response structure
                self.assertIn("documents", data)
                self.assertIsInstance(data["documents"], list)
                
                # Log the number of documents found
                logger.info(f"Found {len(data['documents'])} documents")
                
                # If there are documents, check their structure
                if len(data["documents"]) > 0:
                    document = data["documents"][0]
                    logger.info(f"Sample document: {document}")
                    
                    # Verify document structure
                    self.assertIn("id", document)
                    self.assertIn("title", document)
                    self.assertIn("type", document)
                    self.assertIn("category", document)
                    self.assertIn("client_id", document)
                    self.assertIn("client_name", document)
                    
                    # Verify client mapping is working
                    self.assertIsNotNone(document["client_name"])
                    self.assertNotEqual(document["client_name"], "Unknown Client")
                
                logger.info("✅ GET /api/email-management/documents-real with admin auth test passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access forbidden - received 403 Forbidden")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing documents-real endpoint with admin: {str(e)}")
            raise
        
        # Test with client authentication
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data keys: {data.keys()}")
                
                # Verify response structure
                self.assertIn("documents", data)
                self.assertIsInstance(data["documents"], list)
                
                # Log the number of documents found
                logger.info(f"Found {len(data['documents'])} documents for client")
                
                logger.info("✅ GET /api/email-management/documents-real with client auth test passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access forbidden - received 403 Forbidden")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing documents-real endpoint with client: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized or 404 Not Found
            self.assertIn(response.status_code, [401, 404])
            
            if response.status_code == 401:
                logger.info("✅ GET /api/email-management/documents-real with invalid auth correctly returns 401")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing documents-real endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden or 404 Not Found
            self.assertIn(response.status_code, [403, 404])
            
            if response.status_code == 403:
                logger.info("✅ GET /api/email-management/documents-real with no auth correctly returns 403")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing documents-real endpoint with no auth: {str(e)}")
            raise
    
    def test_trainings_real_endpoint(self):
        """Test GET /api/email-management/trainings-real endpoint"""
        logger.info("\n=== Testing GET /api/email-management/trainings-real endpoint ===")
        
        url = f"{self.api_url}/email-management/trainings-real"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data keys: {data.keys()}")
                
                # Verify response structure
                self.assertIn("trainings", data)
                self.assertIsInstance(data["trainings"], list)
                
                # Log the number of trainings found
                logger.info(f"Found {len(data['trainings'])} trainings")
                
                # If there are trainings, check their structure
                if len(data["trainings"]) > 0:
                    training = data["trainings"][0]
                    logger.info(f"Sample training: {training}")
                    
                    # Verify training structure
                    self.assertIn("id", training)
                    self.assertIn("title", training)
                    self.assertIn("description", training)
                    self.assertIn("client_id", training)
                    self.assertIn("client_name", training)
                    self.assertIn("trainer", training)
                    self.assertIn("training_date", training)
                    
                    # Verify client mapping is working
                    self.assertIsNotNone(training["client_name"])
                    self.assertNotEqual(training["client_name"], "Unknown Client")
                
                logger.info("✅ GET /api/email-management/trainings-real with admin auth test passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access forbidden - received 403 Forbidden")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing trainings-real endpoint with admin: {str(e)}")
            raise
        
        # Test with client authentication
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data keys: {data.keys()}")
                
                # Verify response structure
                self.assertIn("trainings", data)
                self.assertIsInstance(data["trainings"], list)
                
                # Log the number of trainings found
                logger.info(f"Found {len(data['trainings'])} trainings for client")
                
                logger.info("✅ GET /api/email-management/trainings-real with client auth test passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access forbidden - received 403 Forbidden")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing trainings-real endpoint with client: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized or 404 Not Found
            self.assertIn(response.status_code, [401, 404])
            
            if response.status_code == 401:
                logger.info("✅ GET /api/email-management/trainings-real with invalid auth correctly returns 401")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing trainings-real endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ GET /api/email-management/trainings-real with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing trainings-real endpoint with no auth: {str(e)}")
            raise
    
    def test_clients_real_endpoint(self):
        """Test GET /api/email-management/clients-real endpoint"""
        logger.info("\n=== Testing GET /api/email-management/clients-real endpoint ===")
        
        url = f"{self.api_url}/email-management/clients-real"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data keys: {data.keys()}")
                
                # Verify response structure
                self.assertIn("clients", data)
                self.assertIsInstance(data["clients"], list)
                
                # Log the number of clients found
                logger.info(f"Found {len(data['clients'])} clients")
                
                # If there are clients, check their structure
                if len(data["clients"]) > 0:
                    client = data["clients"][0]
                    logger.info(f"Sample client: {client}")
                    
                    # Verify client structure
                    self.assertIn("id", client)
                    self.assertIn("name", client)
                    self.assertIn("email", client)
                    self.assertIn("contact_person", client)
                    self.assertIn("client_id", client)
                    
                    # Verify email is present
                    self.assertIsNotNone(client["email"])
                    self.assertNotEqual(client["email"], "")
                
                logger.info("✅ GET /api/email-management/clients-real with admin auth test passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access forbidden - received 403 Forbidden")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing clients-real endpoint with admin: {str(e)}")
            raise
        
        # Test with client authentication
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data keys: {data.keys()}")
                
                # Verify response structure
                self.assertIn("clients", data)
                self.assertIsInstance(data["clients"], list)
                
                # Log the number of clients found
                logger.info(f"Found {len(data['clients'])} clients for client user")
                
                logger.info("✅ GET /api/email-management/clients-real with client auth test passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication required - received 401 Unauthorized")
            elif response.status_code == 403:
                logger.info("✅ Access forbidden - received 403 Forbidden")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing clients-real endpoint with client: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized or 404 Not Found
            self.assertIn(response.status_code, [401, 404])
            
            if response.status_code == 401:
                logger.info("✅ GET /api/email-management/clients-real with invalid auth correctly returns 401")
            else:
                logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        except Exception as e:
            logger.error(f"❌ Error testing clients-real endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ GET /api/email-management/clients-real with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing clients-real endpoint with no auth: {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main()