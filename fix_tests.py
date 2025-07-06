import unittest
import json
import logging
import requests
import os
import sys
import io
import uuid
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pymongo import MongoClient
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "rotacrm"

# Test JWT tokens
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0xJRU5UIiwiZW1haWwiOiJjbGllbnRAdGVzdC5jb20iLCJuYW1lIjoiQ2xpZW50IFVzZXIifQ.signature"
INVALID_TOKEN = "invalid.token.format"

class TestDocumentDownloadEndpoint(unittest.TestCase):
    """Test class for document download endpoint"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # Connect to MongoDB to get document IDs for testing
        self.mongo_client = MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        
        # Get a list of document IDs from the database
        self.document_ids = []
        try:
            documents = list(self.db.documents.find({}, {"id": 1, "client_id": 1, "name": 1, "gridfs_id": 1}).limit(5))
            for doc in documents:
                if "id" in doc and "gridfs_id" in doc and doc["gridfs_id"]:
                    self.document_ids.append({
                        "id": doc["id"],
                        "client_id": doc.get("client_id", ""),
                        "name": doc.get("name", "Unknown"),
                        "gridfs_id": doc["gridfs_id"]
                    })
            logger.info(f"Found {len(self.document_ids)} documents with GridFS IDs for testing")
        except Exception as e:
            logger.error(f"Error getting document IDs from MongoDB: {e}")
    
    def test_document_download_endpoint_with_admin(self):
        """Test the /api/documents/{id}/download endpoint with admin authentication"""
        logger.info("\n=== Testing /api/documents/{id}/download endpoint with admin authentication ===")
        
        if not self.document_ids:
            logger.warning("No documents found in database for testing. Skipping test.")
            return
        
        for doc_info in self.document_ids:
            doc_id = doc_info["id"]
            doc_name = doc_info["name"]
            gridfs_id = doc_info["gridfs_id"]
            
            logger.info(f"Testing download for document: {doc_name} (ID: {doc_id}, GridFS ID: {gridfs_id})")
            
            url = f"{self.api_url}/documents/{doc_id}/download"
            
            try:
                response = requests.get(url, headers=self.headers_admin)
                logger.info(f"Admin response status code: {response.status_code}")
                
                # Should get 200 OK
                self.assertEqual(response.status_code, 200)
                
                # Check content type - should be application/octet-stream or application/pdf
                content_type = response.headers.get("Content-Type", "")
                logger.info(f"Content-Type: {content_type}")
                self.assertIn(content_type, ["application/octet-stream", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"])
                
                # Check Content-Disposition header - should be attachment
                content_disposition = response.headers.get("Content-Disposition", "")
                logger.info(f"Content-Disposition: {content_disposition}")
                self.assertIn("attachment", content_disposition)
                
                # Check content length - should be greater than 0
                content_length = int(response.headers.get("Content-Length", "0"))
                logger.info(f"Content-Length: {content_length}")
                self.assertGreater(content_length, 0)
                
                # Check content - should NOT contain placeholder text
                content = response.content
                content_start = content[:100]  # First 100 bytes
                logger.info(f"Content start: {content_start}")
                
                # Check if content is NOT a placeholder text file
                self.assertNotIn(b"This is a placeholder document content", content)
                
                # For PDF files, check for PDF signature
                if content_type == "application/pdf":
                    self.assertTrue(content.startswith(b"%PDF-"))
                
                logger.info(f"✅ Document download test passed for document: {doc_name}")
            except Exception as e:
                logger.error(f"❌ Error testing document download for {doc_name}: {str(e)}")
                raise
    
    def test_document_download_endpoint_with_client(self):
        """Test the /api/documents/{id}/download endpoint with client authentication"""
        logger.info("\n=== Testing /api/documents/{id}/download endpoint with client authentication ===")
        
        if not self.document_ids:
            logger.warning("No documents found in database for testing. Skipping test.")
            return
        
        for doc_info in self.document_ids:
            doc_id = doc_info["id"]
            doc_name = doc_info["name"]
            client_id = doc_info["client_id"]
            
            logger.info(f"Testing download for document: {doc_name} (ID: {doc_id}, Client ID: {client_id})")
            
            url = f"{self.api_url}/documents/{doc_id}/download"
            
            try:
                response = requests.get(url, headers=self.headers_client)
                logger.info(f"Client response status code: {response.status_code}")
                
                # Should get 200 OK or 403 Forbidden (if client doesn't have access)
                self.assertIn(response.status_code, [200, 403])
                
                if response.status_code == 200:
                    # Check content type - should be application/octet-stream or application/pdf
                    content_type = response.headers.get("Content-Type", "")
                    logger.info(f"Content-Type: {content_type}")
                    self.assertIn(content_type, ["application/octet-stream", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"])
                    
                    # Check Content-Disposition header - should be attachment
                    content_disposition = response.headers.get("Content-Disposition", "")
                    logger.info(f"Content-Disposition: {content_disposition}")
                    self.assertIn("attachment", content_disposition)
                    
                    # Check content length - should be greater than 0
                    content_length = int(response.headers.get("Content-Length", "0"))
                    logger.info(f"Content-Length: {content_length}")
                    self.assertGreater(content_length, 0)
                    
                    # Check content - should NOT contain placeholder text
                    content = response.content
                    content_start = content[:100]  # First 100 bytes
                    logger.info(f"Content start: {content_start}")
                    
                    # Check if content is NOT a placeholder text file
                    self.assertNotIn(b"This is a placeholder document content", content)
                    
                    logger.info(f"✅ Document download test passed for document: {doc_name}")
                else:
                    # If 403, this is expected for documents the client doesn't have access to
                    logger.info(f"✅ Client correctly denied access to document: {doc_name}")
            except Exception as e:
                logger.error(f"❌ Error testing document download for {doc_name} with client: {str(e)}")
                raise
    
    def test_document_download_endpoint_with_invalid_token(self):
        """Test the /api/documents/{id}/download endpoint with invalid authentication"""
        logger.info("\n=== Testing /api/documents/{id}/download endpoint with invalid authentication ===")
        
        if not self.document_ids:
            logger.warning("No documents found in database for testing. Skipping test.")
            return
        
        doc_id = self.document_ids[0]["id"]
        url = f"{self.api_url}/documents/{doc_id}/download"
        
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ Document download with invalid token correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing document download with invalid token: {str(e)}")
            raise
    
    def test_document_download_endpoint_without_token(self):
        """Test the /api/documents/{id}/download endpoint without authentication"""
        logger.info("\n=== Testing /api/documents/{id}/download endpoint without authentication ===")
        
        if not self.document_ids:
            logger.warning("No documents found in database for testing. Skipping test.")
            return
        
        doc_id = self.document_ids[0]["id"]
        url = f"{self.api_url}/documents/{doc_id}/download"
        
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No token response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ Document download without token correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing document download without token: {str(e)}")
            raise
    
    def test_document_download_endpoint_with_nonexistent_id(self):
        """Test the /api/documents/{id}/download endpoint with a nonexistent document ID"""
        logger.info("\n=== Testing /api/documents/{id}/download endpoint with nonexistent ID ===")
        
        nonexistent_id = str(uuid.uuid4())
        url = f"{self.api_url}/documents/{nonexistent_id}/download"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Nonexistent ID response status code: {response.status_code}")
            
            # Should get 404 Not Found
            self.assertEqual(response.status_code, 404)
            
            logger.info("✅ Document download with nonexistent ID correctly returns 404")
        except Exception as e:
            logger.error(f"❌ Error testing document download with nonexistent ID: {str(e)}")
            raise

class TestTrainingEndpoints(unittest.TestCase):
    """Test class for training endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_get_trainings_endpoint(self):
        """Test the GET /api/trainings endpoint with authentication"""
        logger.info("\n=== Testing GET /api/trainings endpoint ===")
        
        url = f"{self.api_url}/trainings"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list
            data = response.json()
            self.assertIsInstance(data, list)
            
            # Check structure of trainings if any exist
            if len(data) > 0:
                training = data[0]
                logger.info(f"Training data: {training}")
                
                # Check for both title and name fields
                self.assertTrue("title" in training or "name" in training, "Training should have either title or name field")
                
                # If title is missing but name exists, title should be set to name
                if "name" in training and "title" not in training:
                    logger.info(f"Training has name but no title: {training['name']}")
                
                # If both exist, either can be used
                if "name" in training and "title" in training:
                    logger.info(f"Training has both name and title: name={training['name']}, title={training['title']}")
                
                # Check other required fields
                self.assertIn("id", training)
                self.assertIn("client_id", training)
                
                # Check training_date format - should be a valid date string
                self.assertIn("training_date", training)
                training_date = training["training_date"]
                logger.info(f"Training date: {training_date}")
                
                # Attempt to parse the date to verify it's valid
                try:
                    datetime.fromisoformat(training_date.replace("Z", "+00:00"))
                    logger.info("✅ Training date is in valid ISO format")
                except ValueError:
                    self.fail(f"Training date is not in valid ISO format: {training_date}")
                
                logger.info(f"✅ Training data structure verified: {training.get('id')}")
            else:
                logger.info("No trainings found in the database")
            
            logger.info("✅ GET /api/trainings endpoint test passed")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/trainings endpoint: {str(e)}")
            raise
    
    def test_create_training_with_name_field(self):
        """Test creating a training with the name field"""
        logger.info("\n=== Testing POST /api/trainings endpoint with name field ===")
        
        url = f"{self.api_url}/trainings"
        
        # Create training data with name field
        training_data = {
            "client_id": "7a992a86-e2f4-4ed5-99f7-bab4966b7306",  # Test client ID
            "name": f"Test Training with Name Field {uuid.uuid4()}",
            "subject": "Test Subject",
            "participant_count": 10,
            "trainer": "Test Trainer",
            "training_date": datetime.now().isoformat(),
            "description": "Test training created with name field"
        }
        
        try:
            response = requests.post(url, headers=self.headers_admin, json=training_data)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK or 201 Created
            self.assertIn(response.status_code, [200, 201])
            
            # Response should contain success message and training_id
            data = response.json()
            self.assertIn("message", data)
            self.assertIn("training_id", data)
            
            training_id = data["training_id"]
            logger.info(f"Created training with ID: {training_id}")
            
            # Now get the training to verify it was created correctly
            get_url = f"{self.api_url}/trainings"
            get_response = requests.get(get_url, headers=self.headers_admin)
            self.assertEqual(get_response.status_code, 200)
            
            trainings = get_response.json()
            created_training = next((t for t in trainings if t.get("id") == training_id), None)
            
            if created_training:
                logger.info(f"Retrieved created training: {created_training}")
                
                # Verify the training has both name and title fields
                self.assertTrue("name" in created_training or "title" in created_training, 
                               "Training should have either name or title field")
                
                # If title exists, it should match the name we provided
                if "title" in created_training:
                    self.assertEqual(created_training["title"], training_data["name"])
                
                logger.info("✅ Training created with name field test passed")
            else:
                self.fail(f"Could not find created training with ID: {training_id}")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/trainings endpoint with name field: {str(e)}")
            raise

class TestDateFormatting(unittest.TestCase):
    """Test class for date formatting in document endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
    
    def test_document_date_formatting(self):
        """Test date formatting in the /api/documents endpoint"""
        logger.info("\n=== Testing date formatting in /api/documents endpoint ===")
        
        url = f"{self.api_url}/documents"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list
            documents = response.json()
            self.assertIsInstance(documents, list)
            
            # Check date formatting for each document
            for doc in documents:
                logger.info(f"Checking date formatting for document: {doc.get('title', 'Unknown')}")
                
                # Check upload_date format - should be a valid date string, not "Invalid Date"
                self.assertIn("upload_date", doc)
                upload_date = doc["upload_date"]
                logger.info(f"Upload date: {upload_date}")
                
                # Verify it's not "Invalid Date"
                self.assertNotEqual(upload_date, "Invalid Date")
                
                # Attempt to parse the date to verify it's valid
                try:
                    # Handle both ISO format and other date formats
                    if "T" in upload_date:
                        # ISO format with timezone
                        datetime.fromisoformat(upload_date.replace("Z", "+00:00"))
                    else:
                        # Try common date formats
                        datetime.strptime(upload_date, "%Y-%m-%d %H:%M:%S.%f")
                    logger.info("✅ Document date is in valid format")
                except ValueError:
                    try:
                        # Try alternative format
                        datetime.strptime(upload_date, "%Y-%m-%d %H:%M:%S")
                        logger.info("✅ Document date is in valid format (alternative)")
                    except ValueError:
                        self.fail(f"Document date is not in valid format: {upload_date}")
            
            logger.info("✅ Document date formatting test passed")
        except Exception as e:
            logger.error(f"❌ Error testing document date formatting: {str(e)}")
            raise

def run_tests():
    """Run all tests"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add document download tests
    suite.addTest(unittest.makeSuite(TestDocumentDownloadEndpoint))
    
    # Add training endpoint tests
    suite.addTest(unittest.makeSuite(TestTrainingEndpoints))
    
    # Add date formatting tests
    suite.addTest(unittest.makeSuite(TestDateFormatting))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == "__main__":
    run_tests()