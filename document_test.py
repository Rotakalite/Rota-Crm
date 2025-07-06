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
from motor.motor_asyncio import AsyncIOMotorClient
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
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
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
        
        # Connect to MongoDB to get real document IDs
        try:
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            logger.info(f"✅ Connected to MongoDB: {DB_NAME}")
            self.db_connected = True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            self.mongo_client = None
            self.db = None
            self.db_connected = False
    
    def test_document_download_no_auth(self):
        """Test document download endpoint without authentication"""
        logger.info("\n=== Testing document download endpoint without authentication ===")
        
        # Get a real document ID from the database
        if self.db_connected:
            document = self.db.documents.find_one({})
            if document:
                document_id = document.get("id")
                logger.info(f"Found document ID: {document_id}")
                
                # Test download endpoint without authentication
                url = f"{self.api_url}/documents/{document_id}/download"
                response = requests.get(url, headers=self.headers_no_auth)
                
                logger.info(f"No auth response status code: {response.status_code}")
                
                # Should get 403 Forbidden (not 404 Not Found)
                self.assertEqual(response.status_code, 403)
                
                logger.info("✅ Document download without auth correctly returns 403 Forbidden")
            else:
                logger.warning("⚠️ No documents found in database, skipping test")
                # Use a dummy document ID for testing
                document_id = "dummy-document-id"
                url = f"{self.api_url}/documents/{document_id}/download"
                response = requests.get(url, headers=self.headers_no_auth)
                logger.info(f"No auth response status code: {response.status_code}")
                self.assertEqual(response.status_code, 403)
        else:
            logger.warning("⚠️ MongoDB connection failed, using dummy document ID")
            document_id = "dummy-document-id"
            url = f"{self.api_url}/documents/{document_id}/download"
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            self.assertEqual(response.status_code, 403)
    
    def test_document_download_invalid_auth(self):
        """Test document download endpoint with invalid authentication"""
        logger.info("\n=== Testing document download endpoint with invalid authentication ===")
        
        # Get a real document ID from the database
        if self.db:
            document = self.db.documents.find_one({})
            if document:
                document_id = document.get("id")
                logger.info(f"Found document ID: {document_id}")
                
                # Test download endpoint with invalid authentication
                url = f"{self.api_url}/documents/{document_id}/download"
                response = requests.get(url, headers=self.headers_invalid)
                
                logger.info(f"Invalid auth response status code: {response.status_code}")
                
                # Should get 401 Unauthorized
                self.assertEqual(response.status_code, 401)
                
                logger.info("✅ Document download with invalid auth correctly returns 401 Unauthorized")
            else:
                logger.warning("⚠️ No documents found in database, skipping test")
        else:
            logger.warning("⚠️ MongoDB connection failed, skipping test")
    
    def test_document_download_admin_auth(self):
        """Test document download endpoint with admin authentication"""
        logger.info("\n=== Testing document download endpoint with admin authentication ===")
        
        # Get a real document ID from the database
        if self.db:
            document = self.db.documents.find_one({})
            if document:
                document_id = document.get("id")
                logger.info(f"Found document ID: {document_id}")
                
                # Test download endpoint with admin authentication
                url = f"{self.api_url}/documents/{document_id}/download"
                response = requests.get(url, headers=self.headers_admin)
                
                logger.info(f"Admin auth response status code: {response.status_code}")
                
                # Should get 200 OK
                self.assertEqual(response.status_code, 200)
                
                # Check content type
                content_type = response.headers.get("Content-Type")
                logger.info(f"Content-Type: {content_type}")
                self.assertIsNotNone(content_type)
                
                # Check content disposition
                content_disposition = response.headers.get("Content-Disposition")
                logger.info(f"Content-Disposition: {content_disposition}")
                self.assertIsNotNone(content_disposition)
                
                # Check content length
                content_length = response.headers.get("Content-Length")
                logger.info(f"Content-Length: {content_length}")
                self.assertIsNotNone(content_length)
                
                # Check file content
                file_content = response.content
                logger.info(f"File content length: {len(file_content)} bytes")
                self.assertGreater(len(file_content), 0)
                
                # Check if content is not a placeholder text
                is_placeholder = False
                try:
                    text_content = file_content.decode('utf-8', errors='ignore')
                    if "This is a placeholder document content" in text_content:
                        is_placeholder = True
                except:
                    pass
                
                self.assertFalse(is_placeholder, "File content should not be a placeholder text")
                
                logger.info("✅ Document download with admin auth successfully returns file content")
            else:
                logger.warning("⚠️ No documents found in database, skipping test")
        else:
            logger.warning("⚠️ MongoDB connection failed, skipping test")
    
    def test_document_download_client_auth(self):
        """Test document download endpoint with client authentication"""
        logger.info("\n=== Testing document download endpoint with client authentication ===")
        
        # Get a real document ID from the database that belongs to the client
        if self.db:
            # Find a user with the client role
            user = self.db.users.find_one({"role": "client"})
            if user and user.get("client_id"):
                client_id = user.get("client_id")
                logger.info(f"Found client ID: {client_id}")
                
                # Find a document that belongs to this client
                document = self.db.documents.find_one({"client_id": client_id})
                if document:
                    document_id = document.get("id")
                    logger.info(f"Found document ID: {document_id} for client: {client_id}")
                    
                    # Test download endpoint with client authentication
                    url = f"{self.api_url}/documents/{document_id}/download"
                    response = requests.get(url, headers=self.headers_client)
                    
                    logger.info(f"Client auth response status code: {response.status_code}")
                    
                    # Should get 200 OK or 403 Forbidden (if document doesn't belong to client)
                    self.assertIn(response.status_code, [200, 403])
                    
                    if response.status_code == 200:
                        # Check content type
                        content_type = response.headers.get("Content-Type")
                        logger.info(f"Content-Type: {content_type}")
                        self.assertIsNotNone(content_type)
                        
                        # Check content disposition
                        content_disposition = response.headers.get("Content-Disposition")
                        logger.info(f"Content-Disposition: {content_disposition}")
                        self.assertIsNotNone(content_disposition)
                        
                        # Check content length
                        content_length = response.headers.get("Content-Length")
                        logger.info(f"Content-Length: {content_length}")
                        self.assertIsNotNone(content_length)
                        
                        # Check file content
                        file_content = response.content
                        logger.info(f"File content length: {len(file_content)} bytes")
                        self.assertGreater(len(file_content), 0)
                        
                        # Check if content is not a placeholder text
                        is_placeholder = False
                        try:
                            text_content = file_content.decode('utf-8', errors='ignore')
                            if "This is a placeholder document content" in text_content:
                                is_placeholder = True
                        except:
                            pass
                        
                        self.assertFalse(is_placeholder, "File content should not be a placeholder text")
                        
                        logger.info("✅ Document download with client auth successfully returns file content")
                    else:
                        logger.info("✅ Document download with client auth correctly returns 403 Forbidden (document doesn't belong to client)")
                else:
                    logger.warning("⚠️ No documents found for client, skipping test")
            else:
                logger.warning("⚠️ No client user found, skipping test")
        else:
            logger.warning("⚠️ MongoDB connection failed, skipping test")
    
    def test_document_download_nonexistent_id(self):
        """Test document download endpoint with nonexistent document ID"""
        logger.info("\n=== Testing document download endpoint with nonexistent document ID ===")
        
        # Generate a random document ID
        nonexistent_id = str(uuid.uuid4())
        logger.info(f"Generated nonexistent document ID: {nonexistent_id}")
        
        # Test download endpoint with admin authentication
        url = f"{self.api_url}/documents/{nonexistent_id}/download"
        response = requests.get(url, headers=self.headers_admin)
        
        logger.info(f"Nonexistent ID response status code: {response.status_code}")
        
        # Should get 404 Not Found
        self.assertEqual(response.status_code, 404)
        
        logger.info("✅ Document download with nonexistent ID correctly returns 404 Not Found")

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
        
        # Connect to MongoDB to get real training data
        try:
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            logger.info(f"✅ Connected to MongoDB: {DB_NAME}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            self.mongo_client = None
            self.db = None
    
    def test_training_list_endpoint(self):
        """Test GET /api/trainings endpoint"""
        logger.info("\n=== Testing GET /api/trainings endpoint ===")
        
        # Test with admin authentication
        url = f"{self.api_url}/trainings"
        response = requests.get(url, headers=self.headers_admin)
        
        logger.info(f"Admin auth response status code: {response.status_code}")
        
        # Should get 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should be a list
        data = response.json()
        self.assertIsInstance(data, list)
        
        # Log the number of trainings found
        logger.info(f"Found {len(data)} trainings")
        
        # Check if trainings have the required fields
        if len(data) > 0:
            training = data[0]
            logger.info(f"Sample training: {training}")
            
            # Check for required fields
            self.assertIn("id", training)
            self.assertIn("client_id", training)
            
            # Check for name field (could be "name" or "title")
            has_name_field = "name" in training or "title" in training
            self.assertTrue(has_name_field, "Training should have either 'name' or 'title' field")
            
            # Log the name field
            if "name" in training:
                logger.info(f"Training name: {training['name']}")
            elif "title" in training:
                logger.info(f"Training title: {training['title']}")
            
            # Check other fields
            self.assertIn("subject", training)
            self.assertIn("participant_count", training)
            self.assertIn("trainer", training)
            self.assertIn("training_date", training)
            
            logger.info("✅ Training data has all required fields")
        
        logger.info("✅ GET /api/trainings with admin auth test passed")
        
        # Test with no authentication
        response = requests.get(url, headers=self.headers_no_auth)
        logger.info(f"No auth response status code: {response.status_code}")
        
        # Should get 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        logger.info("✅ GET /api/trainings with no auth correctly returns 403 Forbidden")

class TestDocumentListEndpoint(unittest.TestCase):
    """Test class for document list endpoint"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # Connect to MongoDB to get real document data
        try:
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            logger.info(f"✅ Connected to MongoDB: {DB_NAME}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            self.mongo_client = None
            self.db = None
    
    def test_document_list_endpoint(self):
        """Test GET /api/documents endpoint"""
        logger.info("\n=== Testing GET /api/documents endpoint ===")
        
        # Test with admin authentication
        url = f"{self.api_url}/documents"
        response = requests.get(url, headers=self.headers_admin)
        
        logger.info(f"Admin auth response status code: {response.status_code}")
        
        # Should get 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Response should be a list
        data = response.json()
        self.assertIsInstance(data, list)
        
        # Log the number of documents found
        logger.info(f"Found {len(data)} documents")
        
        # Check if documents have the required fields
        if len(data) > 0:
            document = data[0]
            logger.info(f"Sample document: {document}")
            
            # Check for required fields
            self.assertIn("id", document)
            self.assertIn("title", document)
            self.assertIn("type", document)
            self.assertIn("category", document)
            self.assertIn("upload_date", document)
            self.assertIn("client_id", document)
            
            # Check if upload_date is a valid date
            upload_date = document.get("upload_date")
            logger.info(f"Document upload_date: {upload_date}")
            
            # Try to parse the date
            try:
                datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                logger.info("✅ Document date is valid")
            except ValueError:
                self.fail(f"Invalid date format: {upload_date}")
            except Exception as e:
                self.fail(f"Error parsing date: {e}")
            
            logger.info("✅ Document data has all required fields with valid dates")
        
        logger.info("✅ GET /api/documents with admin auth test passed")
        
        # Test with no authentication
        response = requests.get(url, headers=self.headers_no_auth)
        logger.info(f"No auth response status code: {response.status_code}")
        
        # Should get 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        logger.info("✅ GET /api/documents with no auth correctly returns 403 Forbidden")

if __name__ == "__main__":
    unittest.main()