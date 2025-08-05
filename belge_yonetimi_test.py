import unittest
import json
import logging
import requests
import os
import sys
import io
import uuid
from pymongo import MongoClient
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://63cd9e66-c298-4a2c-92bc-f8af7936d9a9.preview.emergentagent.com/api"

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "rotacrm"

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestBelgeYonetimiSystem(unittest.TestCase):
    """Test class for New Belge Yönetimi System Backend APIs"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        self.headers_no_auth = {}
        
        # MongoDB connection for direct database verification
        self.mongo_client = MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        
        # Test file for upload
        self.test_file_path = "/tmp/test_document.txt"
        with open(self.test_file_path, "w") as f:
            f.write("This is a test document for Belge Yönetimi System testing.")
        
        # Test data for document upload
        self.test_client_id = "test_client_" + str(uuid.uuid4())
        self.test_folder_id = "test_folder_" + str(uuid.uuid4())
        self.test_document_name = "Test Document " + str(uuid.uuid4())
        self.test_document_type = "TR1_CRITERIA"
        self.test_stage = "STAGE_1"
        self.test_description = "Test description for Belge Yönetimi System testing."
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove test file
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)
    
    def test_belge_upload_endpoint(self):
        """Test POST /api/belge/upload endpoint"""
        logger.info("\n=== Testing POST /api/belge/upload endpoint ===")
        
        url = f"{self.api_url}/belge/upload"
        
        # Test with admin authentication
        try:
            with open(self.test_file_path, "rb") as f:
                files = {"file": f}
                data = {
                    "client_id": self.test_client_id,
                    "folder_id": self.test_folder_id,
                    "document_name": self.test_document_name,
                    "document_type": self.test_document_type,
                    "stage": self.test_stage,
                    "description": self.test_description
                }
                
                response = requests.post(url, headers=self.headers_admin, files=files, data=data)
                logger.info(f"Admin response status code: {response.status_code}")
                
                # Should get 200 OK or 201 Created
                self.assertIn(response.status_code, [200, 201])
                
                # Response should contain success message and document_id
                data = response.json()
                self.assertIn("success", data)
                self.assertTrue(data["success"])
                self.assertIn("document_id", data)
                self.assertIn("message", data)
                self.assertIn("file_size", data)
                
                # Save document_id for later tests
                self.document_id = data["document_id"]
                logger.info(f"Uploaded document with ID: {self.document_id}")
                
                logger.info("✅ POST /api/belge/upload with admin auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing belge upload endpoint: {str(e)}")
            raise
    
    def test_belge_list_endpoint(self):
        """Test GET /api/belge/list endpoint"""
        logger.info("\n=== Testing GET /api/belge/list endpoint ===")
        
        url = f"{self.api_url}/belge/list"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain success message and documents
            data = response.json()
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("documents", data)
            self.assertIn("count", data)
            
            # Log the number of documents found
            documents = data["documents"]
            logger.info(f"Found {len(documents)} documents")
            
            # If there are documents, check their structure
            if len(documents) > 0:
                document = documents[0]
                self.assertIn("id", document)
                self.assertIn("client_id", document)
                self.assertIn("document_name", document)
                self.assertIn("document_type", document)
                self.assertIn("stage", document)
                self.assertIn("file_path", document)
                self.assertIn("file_size", document)
                self.assertIn("created_at", document)
                
                logger.info(f"Sample document: {document['document_name']} (ID: {document['id']})")
            
            logger.info("✅ GET /api/belge/list with admin auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing belge list endpoint: {str(e)}")
            raise
        
        # Test with client_id parameter
        try:
            params = {"client_id": self.test_client_id}
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"Admin response with client_id parameter status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain success message and documents
            data = response.json()
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("documents", data)
            self.assertIn("count", data)
            
            # Log the number of documents found for this client
            documents = data["documents"]
            logger.info(f"Found {len(documents)} documents for client {self.test_client_id}")
            
            # If there are documents for this client, they should all have the correct client_id
            for document in documents:
                self.assertEqual(document["client_id"], self.test_client_id)
            
            logger.info("✅ GET /api/belge/list with client_id parameter test passed")
        except Exception as e:
            logger.error(f"❌ Error testing belge list endpoint with client_id parameter: {str(e)}")
            raise
    
    def test_belge_download_endpoint(self):
        """Test GET /api/belge/download/{document_id} endpoint"""
        logger.info("\n=== Testing GET /api/belge/download/{document_id} endpoint ===")
        
        # First, upload a document to get a valid document_id
        try:
            # Upload a document
            upload_url = f"{self.api_url}/belge/upload"
            with open(self.test_file_path, "rb") as f:
                files = {"file": f}
                data = {
                    "client_id": self.test_client_id,
                    "folder_id": self.test_folder_id,
                    "document_name": self.test_document_name,
                    "document_type": self.test_document_type,
                    "stage": self.test_stage,
                    "description": self.test_description
                }
                
                upload_response = requests.post(upload_url, headers=self.headers_admin, files=files, data=data)
                upload_data = upload_response.json()
                document_id = upload_data["document_id"]
                logger.info(f"Uploaded document with ID: {document_id}")
            
            # Now test the download endpoint
            download_url = f"{self.api_url}/belge/download/{document_id}"
            
            # Test with admin authentication
            response = requests.get(download_url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain the file content
            content = response.content
            self.assertGreater(len(content), 0)
            
            # Check Content-Type and Content-Disposition headers
            self.assertIn("Content-Type", response.headers)
            self.assertIn("Content-Disposition", response.headers)
            
            logger.info(f"Downloaded file size: {len(content)} bytes")
            logger.info(f"Content-Type: {response.headers.get('Content-Type')}")
            logger.info(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
            
            logger.info("✅ GET /api/belge/download/{document_id} with admin auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing belge download endpoint: {str(e)}")
            raise
    
    def test_belge_delete_endpoint(self):
        """Test DELETE /api/belge/delete/{document_id} endpoint"""
        logger.info("\n=== Testing DELETE /api/belge/delete/{document_id} endpoint ===")
        
        # First, upload a document to get a valid document_id
        try:
            # Upload a document
            upload_url = f"{self.api_url}/belge/upload"
            with open(self.test_file_path, "rb") as f:
                files = {"file": f}
                data = {
                    "client_id": self.test_client_id,
                    "folder_id": self.test_folder_id,
                    "document_name": self.test_document_name,
                    "document_type": self.test_document_type,
                    "stage": self.test_stage,
                    "description": self.test_description
                }
                
                upload_response = requests.post(upload_url, headers=self.headers_admin, files=files, data=data)
                upload_data = upload_response.json()
                document_id = upload_data["document_id"]
                logger.info(f"Uploaded document with ID: {document_id}")
            
            # Now test the delete endpoint
            delete_url = f"{self.api_url}/belge/delete/{document_id}"
            
            # Test with admin authentication
            response = requests.delete(delete_url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain success message
            data = response.json()
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("message", data)
            
            logger.info(f"Delete response message: {data['message']}")
            
            # Verify the document is no longer in the database
            list_url = f"{self.api_url}/belge/list"
            list_response = requests.get(list_url, headers=self.headers_admin)
            list_data = list_response.json()
            documents = list_data["documents"]
            
            # Check that the deleted document is not in the list
            deleted_document = next((doc for doc in documents if doc["id"] == document_id), None)
            self.assertIsNone(deleted_document, f"Document with ID {document_id} should not be in the list after deletion")
            
            logger.info("✅ DELETE /api/belge/delete/{document_id} with admin auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing belge delete endpoint: {str(e)}")
            raise
    
    def test_authentication_requirements(self):
        """Test authentication requirements for all Belge Yönetimi endpoints"""
        logger.info("\n=== Testing authentication requirements for Belge Yönetimi endpoints ===")
        
        # Test endpoints with no authentication
        endpoints = [
            {"method": "GET", "url": f"{self.api_url}/belge/list"},
            {"method": "GET", "url": f"{self.api_url}/belge/download/invalid-id"},
            {"method": "DELETE", "url": f"{self.api_url}/belge/delete/invalid-id"}
        ]
        
        for endpoint in endpoints:
            method = endpoint["method"]
            url = endpoint["url"]
            
            try:
                if method == "GET":
                    response = requests.get(url, headers=self.headers_no_auth)
                elif method == "DELETE":
                    response = requests.delete(url, headers=self.headers_no_auth)
                
                logger.info(f"No auth response for {method} {url}: {response.status_code}")
                
                # Should get 401 Unauthorized or 403 Forbidden
                self.assertIn(response.status_code, [401, 403, 404])
                
                logger.info(f"✅ {method} {url} with no auth correctly returns {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Error testing {method} {url} with no auth: {str(e)}")
                raise
        
        # Test upload endpoint with no authentication
        try:
            upload_url = f"{self.api_url}/belge/upload"
            with open(self.test_file_path, "rb") as f:
                files = {"file": f}
                data = {
                    "client_id": self.test_client_id,
                    "folder_id": self.test_folder_id,
                    "document_name": self.test_document_name,
                    "document_type": self.test_document_type,
                    "stage": self.test_stage,
                    "description": self.test_description
                }
                
                response = requests.post(upload_url, headers=self.headers_no_auth, files=files, data=data)
                logger.info(f"No auth response for POST {upload_url}: {response.status_code}")
                
                # Should get 401 Unauthorized or 403 Forbidden
                self.assertIn(response.status_code, [401, 403])
                
                logger.info(f"✅ POST {upload_url} with no auth correctly returns {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing POST {upload_url} with no auth: {str(e)}")
            raise
        
        logger.info("✅ Authentication requirements test passed")

def run_belge_yonetimi_tests():
    """Run all Belge Yönetimi System tests"""
    suite = unittest.TestSuite()
    
    # Add Belge Yönetimi System tests
    suite.addTest(TestBelgeYonetimiSystem("test_belge_upload_endpoint"))
    suite.addTest(TestBelgeYonetimiSystem("test_belge_list_endpoint"))
    suite.addTest(TestBelgeYonetimiSystem("test_belge_download_endpoint"))
    suite.addTest(TestBelgeYonetimiSystem("test_belge_delete_endpoint"))
    suite.addTest(TestBelgeYonetimiSystem("test_authentication_requirements"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Print summary
    logger.info("\n=== Belge Yönetimi System Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All Belge Yönetimi System tests PASSED")
        return True
    else:
        logger.error("Some Belge Yönetimi System tests FAILED")
        return False

if __name__ == "__main__":
    run_belge_yonetimi_tests()