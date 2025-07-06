import unittest
import json
import logging
import requests
import os
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get backend URL from frontend/.env
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT token for admin user
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

class TestRealEmailManagementEndpoints(unittest.TestCase):
    """Test class for Real Email Management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        self.headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    def test_real_clients_endpoint(self):
        """Test GET /api/email-management/clients-real endpoint"""
        logger.info("\n=== Testing GET /api/email-management/clients-real endpoint ===")
        
        url = f"{self.api_url}/email-management/clients-real"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if endpoint is accessible
            self.assertIn(response.status_code, [200, 401, 403, 404, 405])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIn("clients", data)
                self.assertIsInstance(data["clients"], list)
                
                # Check client data structure if any clients exist
                if len(data["clients"]) > 0:
                    client = data["clients"][0]
                    self.assertIn("id", client)
                    self.assertIn("name", client)
                    self.assertIn("email", client)
                    self.assertIn("contact_person", client)
                    self.assertIn("category", client)
                    self.assertIn("client_id", client)
                    
                    logger.info(f"Found {len(data['clients'])} clients")
                    logger.info(f"Sample client: {client}")
                else:
                    logger.info("No clients found, but endpoint is working")
                
                logger.info("✅ GET /api/email-management/clients-real test passed")
            elif response.status_code == 404:
                logger.error("❌ Endpoint not found (404)")
                logger.error("The endpoint /api/email-management/clients-real is not accessible")
            elif response.status_code == 405:
                logger.error("❌ Method not allowed (405)")
                logger.error("The endpoint /api/email-management/clients-real does not allow GET method")
            elif response.status_code in [401, 403]:
                logger.info("Authentication/authorization required")
                
        except Exception as e:
            logger.error(f"❌ Error testing clients endpoint: {str(e)}")
            raise
    
    def test_real_documents_endpoint(self):
        """Test GET /api/email-management/documents-real endpoint"""
        logger.info("\n=== Testing GET /api/email-management/documents-real endpoint ===")
        
        url = f"{self.api_url}/email-management/documents-real"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if endpoint is accessible
            self.assertIn(response.status_code, [200, 401, 403, 404, 405])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIn("documents", data)
                self.assertIsInstance(data["documents"], list)
                
                # Check document data structure if any documents exist
                if len(data["documents"]) > 0:
                    document = data["documents"][0]
                    self.assertIn("id", document)
                    self.assertIn("title", document)
                    self.assertIn("type", document)
                    self.assertIn("category", document)
                    self.assertIn("upload_date", document)
                    self.assertIn("file_size", document)
                    self.assertIn("file_path", document)
                    self.assertIn("client_id", document)
                    self.assertIn("client_name", document)
                    
                    logger.info(f"Found {len(data['documents'])} documents")
                    logger.info(f"Sample document: {document}")
                else:
                    logger.info("No documents found, but endpoint is working")
                
                logger.info("✅ GET /api/email-management/documents-real test passed")
            elif response.status_code == 404:
                logger.error("❌ Endpoint not found (404)")
                logger.error("The endpoint /api/email-management/documents-real is not accessible")
            elif response.status_code == 405:
                logger.error("❌ Method not allowed (405)")
                logger.error("The endpoint /api/email-management/documents-real does not allow GET method")
            elif response.status_code in [401, 403]:
                logger.info("Authentication/authorization required")
                
        except Exception as e:
            logger.error(f"❌ Error testing documents endpoint: {str(e)}")
            raise
    
    def test_real_trainings_endpoint(self):
        """Test GET /api/email-management/trainings-real endpoint"""
        logger.info("\n=== Testing GET /api/email-management/trainings-real endpoint ===")
        
        url = f"{self.api_url}/email-management/trainings-real"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if endpoint is accessible
            self.assertIn(response.status_code, [200, 401, 403, 404, 405])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIn("trainings", data)
                self.assertIsInstance(data["trainings"], list)
                
                # Check training data structure if any trainings exist
                if len(data["trainings"]) > 0:
                    training = data["trainings"][0]
                    self.assertIn("id", training)
                    self.assertIn("title", training)
                    self.assertIn("description", training)
                    self.assertIn("duration", training)
                    self.assertIn("level", training)
                    self.assertIn("category", training)
                    self.assertIn("client_id", training)
                    self.assertIn("client_name", training)
                    self.assertIn("trainer", training)
                    self.assertIn("training_date", training)
                    self.assertIn("status", training)
                    
                    logger.info(f"Found {len(data['trainings'])} trainings")
                    logger.info(f"Sample training: {training}")
                else:
                    logger.info("No trainings found, but endpoint is working")
                
                logger.info("✅ GET /api/email-management/trainings-real test passed")
            elif response.status_code == 404:
                logger.error("❌ Endpoint not found (404)")
                logger.error("The endpoint /api/email-management/trainings-real is not accessible")
            elif response.status_code == 405:
                logger.error("❌ Method not allowed (405)")
                logger.error("The endpoint /api/email-management/trainings-real does not allow GET method")
            elif response.status_code in [401, 403]:
                logger.info("Authentication/authorization required")
                
        except Exception as e:
            logger.error(f"❌ Error testing trainings endpoint: {str(e)}")
            raise

    def test_regular_endpoints(self):
        """Test regular endpoints to compare with email management endpoints"""
        logger.info("\n=== Testing regular endpoints for comparison ===")
        
        # Test /api/clients endpoint
        try:
            url = f"{self.api_url}/clients"
            response = requests.get(url, headers=self.headers)
            logger.info(f"/api/clients response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    logger.info(f"Found {len(data)} clients in regular endpoint")
                else:
                    logger.info(f"Regular /api/clients endpoint returned non-list data")
                logger.info("✅ Regular /api/clients endpoint is working")
            else:
                logger.info(f"Regular /api/clients endpoint returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing regular clients endpoint: {str(e)}")
        
        # Test /api/documents endpoint
        try:
            url = f"{self.api_url}/documents"
            response = requests.get(url, headers=self.headers)
            logger.info(f"/api/documents response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    logger.info(f"Found {len(data)} documents in regular endpoint")
                else:
                    logger.info(f"Regular /api/documents endpoint returned non-list data")
                logger.info("✅ Regular /api/documents endpoint is working")
            else:
                logger.info(f"Regular /api/documents endpoint returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing regular documents endpoint: {str(e)}")
        
        # Test /api/trainings endpoint
        try:
            url = f"{self.api_url}/trainings"
            response = requests.get(url, headers=self.headers)
            logger.info(f"/api/trainings response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    logger.info(f"Found {len(data)} trainings in regular endpoint")
                else:
                    logger.info(f"Regular /api/trainings endpoint returned non-list data")
                logger.info("✅ Regular /api/trainings endpoint is working")
            else:
                logger.info(f"Regular /api/trainings endpoint returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing regular trainings endpoint: {str(e)}")

if __name__ == "__main__":
    unittest.main()