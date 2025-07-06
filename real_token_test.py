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

class TestDocumentDownloadWithRealToken(unittest.TestCase):
    """Test class for document download endpoint with real JWT token"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
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
    
    def get_jwt_token(self):
        """Get a real JWT token from the user"""
        logger.info("Please enter a valid JWT token for testing:")
        token = input()
        return token
    
    def test_document_download_with_real_token(self):
        """Test document download endpoint with a real JWT token"""
        logger.info("\n=== Testing document download endpoint with real JWT token ===")
        
        # Get a real JWT token
        token = self.get_jwt_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get a real document ID from the database
        if self.db_connected:
            document = self.db.documents.find_one({})
            if document:
                document_id = document.get("id")
                logger.info(f"Found document ID: {document_id}")
                
                # Test download endpoint with real token
                url = f"{self.api_url}/documents/{document_id}/download"
                response = requests.get(url, headers=headers)
                
                logger.info(f"Real token response status code: {response.status_code}")
                
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
                
                # Save the file content to a temporary file for inspection
                with open(f"/tmp/document_{document_id}.bin", "wb") as f:
                    f.write(file_content)
                logger.info(f"File content saved to /tmp/document_{document_id}.bin")
                
                logger.info("✅ Document download with real token successfully returns file content")
            else:
                logger.warning("⚠️ No documents found in database, skipping test")
        else:
            logger.warning("⚠️ MongoDB connection failed, skipping test")

if __name__ == "__main__":
    unittest.main()