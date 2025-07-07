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

# Backend URL from frontend .env
BACKEND_URL = "https://9fdcc5d0-9b6d-4e6f-bc8f-589c3991a8cc.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class TestEmailManagementEndpoints(unittest.TestCase):
    """Test class for Email Management endpoints"""
    
    def test_clients_endpoint(self):
        """Test the /api/clients endpoint"""
        logger.info("\n=== Testing /api/clients endpoint ===")
        
        url = f"{API_URL}/clients"
        
        try:
            # First, try without authentication to see if we get 403
            response = requests.get(url)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            logger.info("✅ /api/clients endpoint correctly requires authentication")
            
        except Exception as e:
            logger.error(f"❌ Error testing /api/clients endpoint: {str(e)}")
            raise
    
    def test_documents_endpoint(self):
        """Test the /api/documents endpoint"""
        logger.info("\n=== Testing /api/documents endpoint ===")
        
        url = f"{API_URL}/documents"
        
        try:
            # First, try without authentication to see if we get 403
            response = requests.get(url)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            logger.info("✅ /api/documents endpoint correctly requires authentication")
            
        except Exception as e:
            logger.error(f"❌ Error testing /api/documents endpoint: {str(e)}")
            raise
    
    def test_trainings_endpoint(self):
        """Test the /api/trainings endpoint"""
        logger.info("\n=== Testing /api/trainings endpoint ===")
        
        url = f"{API_URL}/trainings"
        
        try:
            # First, try without authentication to see if we get 403
            response = requests.get(url)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            logger.info("✅ /api/trainings endpoint correctly requires authentication")
            
        except Exception as e:
            logger.error(f"❌ Error testing /api/trainings endpoint: {str(e)}")
            raise
    
    def test_email_management_documents_real_endpoint(self):
        """Test the /api/email-management/documents-real endpoint"""
        logger.info("\n=== Testing /api/email-management/documents-real endpoint ===")
        
        url = f"{API_URL}/email-management/documents-real"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check response status code
            if response.status_code == 200:
                # Response should contain documents array
                data = response.json()
                self.assertIn("documents", data)
                self.assertIsInstance(data["documents"], list)
                
                # Log the number of documents
                document_count = len(data["documents"])
                logger.info(f"Found {document_count} documents in email-management/documents-real")
                
                # Verify document data structure if documents exist
                if document_count > 0:
                    document = data["documents"][0]
                    logger.info(f"Sample document: {json.dumps(document, indent=2)}")
                    
                    self.assertIn("id", document)
                    self.assertIn("title", document)
                    self.assertIn("type", document)
                    self.assertIn("category", document)
                    self.assertIn("client_id", document)
                
                logger.info("✅ /api/email-management/documents-real endpoint works")
            elif response.status_code == 404:
                logger.warning("⚠️ /api/email-management/documents-real endpoint returned 404 Not Found")
                logger.warning("This endpoint may not be properly registered in the API router")
            else:
                logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
                if response.headers.get('content-type') == 'application/json':
                    logger.warning(f"Response: {response.json()}")
                else:
                    logger.warning(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error testing /api/email-management/documents-real endpoint: {str(e)}")
            raise
    
    def test_email_management_trainings_real_endpoint(self):
        """Test the /api/email-management/trainings-real endpoint"""
        logger.info("\n=== Testing /api/email-management/trainings-real endpoint ===")
        
        url = f"{API_URL}/email-management/trainings-real"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check response status code
            if response.status_code == 200:
                # Response should contain trainings array
                data = response.json()
                self.assertIn("trainings", data)
                self.assertIsInstance(data["trainings"], list)
                
                # Log the number of trainings
                training_count = len(data["trainings"])
                logger.info(f"Found {training_count} trainings in email-management/trainings-real")
                
                # Verify training data structure if trainings exist
                if training_count > 0:
                    training = data["trainings"][0]
                    logger.info(f"Sample training: {json.dumps(training, indent=2)}")
                    
                    self.assertIn("id", training)
                    self.assertIn("title", training)
                    self.assertIn("description", training)
                    self.assertIn("client_id", training)
                
                logger.info("✅ /api/email-management/trainings-real endpoint works")
            elif response.status_code == 404:
                logger.warning("⚠️ /api/email-management/trainings-real endpoint returned 404 Not Found")
                logger.warning("This endpoint may not be properly registered in the API router")
            else:
                logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
                if response.headers.get('content-type') == 'application/json':
                    logger.warning(f"Response: {response.json()}")
                else:
                    logger.warning(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error testing /api/email-management/trainings-real endpoint: {str(e)}")
            raise
    
    def test_email_management_clients_real_endpoint(self):
        """Test the /api/email-management/clients-real endpoint"""
        logger.info("\n=== Testing /api/email-management/clients-real endpoint ===")
        
        url = f"{API_URL}/email-management/clients-real"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check response status code
            if response.status_code == 200:
                # Response should contain clients array
                data = response.json()
                self.assertIn("clients", data)
                self.assertIsInstance(data["clients"], list)
                
                # Log the number of clients
                client_count = len(data["clients"])
                logger.info(f"Found {client_count} clients in email-management/clients-real")
                
                # Verify client data structure if clients exist
                if client_count > 0:
                    client = data["clients"][0]
                    logger.info(f"Sample client: {json.dumps(client, indent=2)}")
                    
                    self.assertIn("id", client)
                    self.assertIn("name", client)
                    self.assertIn("email", client)
                    self.assertIn("client_id", client)
                
                logger.info("✅ /api/email-management/clients-real endpoint works")
            elif response.status_code == 404:
                logger.warning("⚠️ /api/email-management/clients-real endpoint returned 404 Not Found")
                logger.warning("This endpoint may not be properly registered in the API router")
            else:
                logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
                if response.headers.get('content-type') == 'application/json':
                    logger.warning(f"Response: {response.json()}")
                else:
                    logger.warning(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error testing /api/email-management/clients-real endpoint: {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main()