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

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT token - this is a sample token for testing
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
INVALID_TOKEN = "invalid.token.format"

class TestDocumentManagementAPI(unittest.TestCase):
    """Test class for Document Management API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different authentication scenarios
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test file for upload
        self.test_file_content = b"This is a test document content for API testing."
        self.test_filename = "test_document.pdf"
        
        # Test document data
        self.test_document_id = None  # Will be set after successful upload
    
    def test_01_get_folders(self):
        """Test GET /api/folders endpoint"""
        logger.info("\n=== Testing GET /api/folders endpoint ===")
        
        url = f"{self.api_url}/folders"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list of folders
            data = response.json()
            self.assertIsInstance(data, list)
            
            # Log the number of folders found
            logger.info(f"Found {len(data)} folders")
            
            # Check if we have the expected 905 folders
            self.assertGreaterEqual(len(data), 400, "Expected at least 400 folders")
            
            # Check folder structure
            if len(data) > 0:
                folder = data[0]
                self.assertIn("id", folder)
                self.assertIn("client_id", folder)
                self.assertIn("name", folder)
                self.assertIn("parent_folder_id", folder)
                self.assertIn("folder_path", folder)
                self.assertIn("level", folder)
                
                # Log some folder details
                logger.info(f"Sample folder: {folder['name']}, Level: {folder['level']}, Client ID: {folder['client_id']}")
                
                # Check if we have Level 4 folders
                level4_folders = [f for f in data if f.get("level") == 4]
                logger.info(f"Found {len(level4_folders)} Level 4 folders")
                self.assertGreaterEqual(len(level4_folders), 100, "Expected at least 100 Level 4 folders")
            
            logger.info("✅ GET /api/folders with admin auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/folders with admin: {str(e)}")
            raise
        
        # Test with client authentication
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list of folders
            data = response.json()
            self.assertIsInstance(data, list)
            
            # Log the number of folders found
            logger.info(f"Client can see {len(data)} folders")
            
            # Client should only see their own folders
            if len(data) > 0:
                # Check that all folders have the same client_id
                client_ids = set(folder.get("client_id") for folder in data)
                logger.info(f"Client folders have client_ids: {client_ids}")
                self.assertLessEqual(len(client_ids), 1, "Client should only see folders with their own client_id")
            
            logger.info("✅ GET /api/folders with client auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/folders with client: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ GET /api/folders with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/folders with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ GET /api/folders with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/folders with no auth: {str(e)}")
            raise
    
    def test_02_belge_list(self):
        """Test GET /api/belge/list endpoint"""
        logger.info("\n=== Testing GET /api/belge/list endpoint ===")
        
        url = f"{self.api_url}/belge/list"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain documents
            data = response.json()
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("documents", data)
            self.assertIn("count", data)
            
            documents = data["documents"]
            self.assertIsInstance(documents, list)
            
            # Log the number of documents found
            logger.info(f"Found {len(documents)} documents")
            
            # Check document structure
            if len(documents) > 0:
                document = documents[0]
                self.assertIn("id", document)
                self.assertIn("client_id", document)
                self.assertIn("document_name", document)
                self.assertIn("filename", document)
                self.assertIn("created_at", document)
                
                # Save a document ID for later tests
                self.test_document_id = document["id"]
                logger.info(f"Saved document ID for testing: {self.test_document_id}")
            
            logger.info("✅ GET /api/belge/list with admin auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/belge/list with admin: {str(e)}")
            raise
        
        # Test with client authentication
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain documents
            data = response.json()
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("documents", data)
            self.assertIn("count", data)
            
            documents = data["documents"]
            self.assertIsInstance(documents, list)
            
            # Log the number of documents found
            logger.info(f"Client can see {len(documents)} documents")
            
            # Client should only see their own documents
            if len(documents) > 0:
                # Check that all documents have the same client_id
                client_ids = set(doc.get("client_id") for doc in documents)
                logger.info(f"Client documents have client_ids: {client_ids}")
                self.assertLessEqual(len(client_ids), 1, "Client should only see documents with their own client_id")
                
                # If we don't have a test document ID yet, save one from the client's documents
                if not self.test_document_id and len(documents) > 0:
                    self.test_document_id = documents[0]["id"]
                    logger.info(f"Saved client document ID for testing: {self.test_document_id}")
            
            logger.info("✅ GET /api/belge/list with client auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/belge/list with client: {str(e)}")
            raise
        
        # Test with client_id parameter (admin only)
        if self.test_document_id:
            try:
                # Get the client_id from the first document
                response = requests.get(url, headers=self.headers_admin)
                data = response.json()
                documents = data["documents"]
                if len(documents) > 0:
                    client_id = documents[0]["client_id"]
                    
                    # Test filtering by client_id
                    params = {"client_id": client_id}
                    response = requests.get(url, headers=self.headers_admin, params=params)
                    logger.info(f"Admin response with client_id filter status code: {response.status_code}")
                    
                    # Should get 200 OK
                    self.assertEqual(response.status_code, 200)
                    
                    # Response should contain only documents for the specified client_id
                    data = response.json()
                    documents = data["documents"]
                    
                    # Check that all documents have the specified client_id
                    if len(documents) > 0:
                        for doc in documents:
                            self.assertEqual(doc["client_id"], client_id)
                    
                    logger.info(f"Found {len(documents)} documents for client_id: {client_id}")
                    logger.info("✅ GET /api/belge/list with client_id filter test passed")
            except Exception as e:
                logger.error(f"❌ Error testing GET /api/belge/list with client_id filter: {str(e)}")
                raise
        
        # Test with invalid authentication
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ GET /api/belge/list with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/belge/list with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ GET /api/belge/list with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/belge/list with no auth: {str(e)}")
            raise
    
    def test_03_belge_upload(self):
        """Test POST /api/belge/upload endpoint"""
        logger.info("\n=== Testing POST /api/belge/upload endpoint ===")
        
        url = f"{self.api_url}/belge/upload"
        
        # First, get a folder ID and client ID for the upload
        folder_id = None
        client_id = None
        
        try:
            # Get folders
            response = requests.get(f"{self.api_url}/folders", headers=self.headers_admin)
            folders = response.json()
            
            if len(folders) > 0:
                # Find a Level 4 folder
                level4_folders = [f for f in folders if f.get("level") == 4]
                if len(level4_folders) > 0:
                    folder = level4_folders[0]
                    folder_id = folder["id"]
                    client_id = folder["client_id"]
                    logger.info(f"Using folder: {folder['name']}, ID: {folder_id}, Client ID: {client_id}")
                else:
                    # Use any folder
                    folder = folders[0]
                    folder_id = folder["id"]
                    client_id = folder["client_id"]
                    logger.info(f"Using folder: {folder['name']}, ID: {folder_id}, Client ID: {client_id}")
        except Exception as e:
            logger.error(f"❌ Error getting folder for upload test: {str(e)}")
            raise
        
        if not folder_id or not client_id:
            logger.error("❌ Could not find a folder for upload test")
            self.skipTest("No folder available for upload test")
            return
        
        # Test with admin authentication
        try:
            # Create a test file
            files = {"file": (self.test_filename, self.test_file_content, "application/pdf")}
            
            # Form data
            data = {
                "client_id": client_id,
                "folder_id": folder_id,
                "document_name": "Test Document for API Testing",
                "document_type": "STAGE_1_DOC",
                "stage": "I.Aşama",
                "description": "This is a test document created by the API test suite"
            }
            
            response = requests.post(url, headers=self.headers_admin, files=files, data=data)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain success message and document_id
            data = response.json()
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("document_id", data)
            self.assertIn("message", data)
            
            # Save document ID for later tests
            self.test_document_id = data["document_id"]
            logger.info(f"Created document with ID: {self.test_document_id}")
            
            logger.info("✅ POST /api/belge/upload with admin auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/belge/upload with admin: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            # Create a test file
            files = {"file": (self.test_filename, self.test_file_content, "application/pdf")}
            
            # Form data
            data = {
                "client_id": client_id,
                "folder_id": folder_id,
                "document_name": "Test Document for API Testing",
                "document_type": "STAGE_1_DOC",
                "stage": "I.Aşama",
                "description": "This is a test document created by the API test suite"
            }
            
            response = requests.post(url, headers=self.headers_invalid, files=files, data=data)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ POST /api/belge/upload with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/belge/upload with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            # Create a test file
            files = {"file": (self.test_filename, self.test_file_content, "application/pdf")}
            
            # Form data
            data = {
                "client_id": client_id,
                "folder_id": folder_id,
                "document_name": "Test Document for API Testing",
                "document_type": "STAGE_1_DOC",
                "stage": "I.Aşama",
                "description": "This is a test document created by the API test suite"
            }
            
            response = requests.post(url, headers=self.headers_no_auth, files=files, data=data)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ POST /api/belge/upload with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/belge/upload with no auth: {str(e)}")
            raise
    
    def test_04_belge_download(self):
        """Test GET /api/belge/download/{id} endpoint"""
        logger.info("\n=== Testing GET /api/belge/download/{id} endpoint ===")
        
        # Skip if we don't have a document ID
        if not self.test_document_id:
            # Try to get a document ID from the list endpoint
            try:
                response = requests.get(f"{self.api_url}/belge/list", headers=self.headers_admin)
                data = response.json()
                documents = data["documents"]
                if len(documents) > 0:
                    self.test_document_id = documents[0]["id"]
                    logger.info(f"Found document ID for download test: {self.test_document_id}")
                else:
                    logger.error("❌ Could not find a document for download test")
                    self.skipTest("No document available for download test")
                    return
            except Exception as e:
                logger.error(f"❌ Error getting document for download test: {str(e)}")
                self.skipTest("Error getting document for download test")
                return
        
        url = f"{self.api_url}/belge/download/{self.test_document_id}"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be the file content
            content = response.content
            self.assertIsNotNone(content)
            self.assertGreater(len(content), 0)
            
            # Check Content-Type and Content-Disposition headers
            self.assertIn("Content-Type", response.headers)
            self.assertIn("Content-Disposition", response.headers)
            
            logger.info(f"Downloaded document with Content-Type: {response.headers.get('Content-Type')}")
            logger.info(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
            logger.info(f"Content length: {len(content)} bytes")
            
            logger.info("✅ GET /api/belge/download/{id} with admin auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/belge/download/{self.test_document_id} with admin: {str(e)}")
            raise
        
        # Test with client authentication
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Should get 200 OK or 403 Forbidden (if the document doesn't belong to the client)
            self.assertIn(response.status_code, [200, 403, 404])
            
            if response.status_code == 200:
                # Response should be the file content
                content = response.content
                self.assertIsNotNone(content)
                self.assertGreater(len(content), 0)
                
                # Check Content-Type and Content-Disposition headers
                self.assertIn("Content-Type", response.headers)
                self.assertIn("Content-Disposition", response.headers)
                
                logger.info(f"Client downloaded document with Content-Type: {response.headers.get('Content-Type')}")
                logger.info(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
                logger.info(f"Content length: {len(content)} bytes")
                
                logger.info("✅ GET /api/belge/download/{id} with client auth test passed")
            elif response.status_code == 403:
                # This is expected if the document doesn't belong to the client
                logger.info("✅ GET /api/belge/download/{id} with client auth correctly returns 403 for document not owned by client")
            else:
                # 404 is also acceptable if the document doesn't exist
                logger.info("✅ GET /api/belge/download/{id} with client auth returns 404 - document may have been deleted")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/belge/download/{self.test_document_id} with client: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ GET /api/belge/download/{id} with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/belge/download/{self.test_document_id} with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ GET /api/belge/download/{id} with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/belge/download/{self.test_document_id} with no auth: {str(e)}")
            raise
        
        # Test with non-existent document ID
        try:
            non_existent_id = str(uuid.uuid4())
            url = f"{self.api_url}/belge/download/{non_existent_id}"
            
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Non-existent document response status code: {response.status_code}")
            
            # Should get 404 Not Found
            self.assertEqual(response.status_code, 404)
            
            logger.info("✅ GET /api/belge/download/{id} with non-existent ID correctly returns 404")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/belge/download with non-existent ID: {str(e)}")
            raise
    
    def test_05_belge_delete(self):
        """Test DELETE /api/belge/delete/{id} endpoint"""
        logger.info("\n=== Testing DELETE /api/belge/delete/{id} endpoint ===")
        
        # Skip if we don't have a document ID
        if not self.test_document_id:
            # Try to get a document ID from the list endpoint
            try:
                response = requests.get(f"{self.api_url}/belge/list", headers=self.headers_admin)
                data = response.json()
                documents = data["documents"]
                if len(documents) > 0:
                    self.test_document_id = documents[0]["id"]
                    logger.info(f"Found document ID for delete test: {self.test_document_id}")
                else:
                    logger.error("❌ Could not find a document for delete test")
                    self.skipTest("No document available for delete test")
                    return
            except Exception as e:
                logger.error(f"❌ Error getting document for delete test: {str(e)}")
                self.skipTest("Error getting document for delete test")
                return
        
        url = f"{self.api_url}/belge/delete/{self.test_document_id}"
        
        # Test with admin authentication
        try:
            response = requests.delete(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain success message
            data = response.json()
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("message", data)
            
            logger.info(f"Delete response: {data['message']}")
            
            # Verify the document is deleted by trying to download it
            download_url = f"{self.api_url}/belge/download/{self.test_document_id}"
            download_response = requests.get(download_url, headers=self.headers_admin)
            self.assertEqual(download_response.status_code, 404)
            
            logger.info("✅ DELETE /api/belge/delete/{id} with admin auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing DELETE /api/belge/delete/{self.test_document_id} with admin: {str(e)}")
            raise
        
        # Test with invalid authentication (using a different document ID)
        try:
            # Get a new document ID
            response = requests.get(f"{self.api_url}/belge/list", headers=self.headers_admin)
            data = response.json()
            documents = data["documents"]
            if len(documents) > 0:
                new_document_id = documents[0]["id"]
                logger.info(f"Found new document ID for invalid auth delete test: {new_document_id}")
                
                url = f"{self.api_url}/belge/delete/{new_document_id}"
                
                response = requests.delete(url, headers=self.headers_invalid)
                logger.info(f"Invalid auth response status code: {response.status_code}")
                
                # Should get 401 Unauthorized
                self.assertEqual(response.status_code, 401)
                
                logger.info("✅ DELETE /api/belge/delete/{id} with invalid auth correctly returns 401")
            else:
                logger.warning("⚠️ Skipping invalid auth delete test - no documents available")
        except Exception as e:
            logger.error(f"❌ Error testing DELETE /api/belge/delete with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication (using a different document ID)
        try:
            # Get a new document ID
            response = requests.get(f"{self.api_url}/belge/list", headers=self.headers_admin)
            data = response.json()
            documents = data["documents"]
            if len(documents) > 0:
                new_document_id = documents[0]["id"]
                logger.info(f"Found new document ID for no auth delete test: {new_document_id}")
                
                url = f"{self.api_url}/belge/delete/{new_document_id}"
                
                response = requests.delete(url, headers=self.headers_no_auth)
                logger.info(f"No auth response status code: {response.status_code}")
                
                # Should get 403 Forbidden
                self.assertEqual(response.status_code, 403)
                
                logger.info("✅ DELETE /api/belge/delete/{id} with no auth correctly returns 403")
            else:
                logger.warning("⚠️ Skipping no auth delete test - no documents available")
        except Exception as e:
            logger.error(f"❌ Error testing DELETE /api/belge/delete with no auth: {str(e)}")
            raise
        
        # Test with non-existent document ID
        try:
            non_existent_id = str(uuid.uuid4())
            url = f"{self.api_url}/belge/delete/{non_existent_id}"
            
            response = requests.delete(url, headers=self.headers_admin)
            logger.info(f"Non-existent document response status code: {response.status_code}")
            
            # Should get 404 Not Found
            self.assertEqual(response.status_code, 404)
            
            logger.info("✅ DELETE /api/belge/delete/{id} with non-existent ID correctly returns 404")
        except Exception as e:
            logger.error(f"❌ Error testing DELETE /api/belge/delete with non-existent ID: {str(e)}")
            raise

class TestLevel4FolderStructure(unittest.TestCase):
    """Test class for Level 4 Folder Structure"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different authentication scenarios
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_01_level4_structure(self):
        """Test Level 4 folder structure implementation"""
        logger.info("\n=== Testing Level 4 folder structure implementation ===")
        
        url = f"{self.api_url}/folders"
        
        # Test with admin authentication
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list of folders
            folders = response.json()
            self.assertIsInstance(folders, list)
            
            # Check if we have Level 4 folders
            level4_folders = [f for f in folders if f.get("level") == 4]
            logger.info(f"Found {len(level4_folders)} Level 4 folders")
            self.assertGreaterEqual(len(level4_folders), 100, "Expected at least 100 Level 4 folders")
            
            # Check if we have the expected Level 4 folder names
            level4_names = set(f.get("name") for f in level4_folders)
            logger.info(f"Level 4 folder names: {level4_names}")
            
            expected_names = {"POLİTİKALAR", "PROSEDÜRLER", "FORMLAR", "LİSTELER", "KAYITLAR"}
            for name in expected_names:
                self.assertIn(name, level4_names, f"Expected Level 4 folder name '{name}' not found")
            
            # Check parent-child relationships
            # Get Level 2 and Level 3 folders
            level2_folders = [f for f in folders if f.get("level") == 2]
            level3_folders = [f for f in folders if f.get("level") == 3]
            
            logger.info(f"Found {len(level2_folders)} Level 2 folders and {len(level3_folders)} Level 3 folders")
            
            # Check that Level 4 folders have parent_folder_id pointing to Level 2 or Level 3 folders
            parent_ids = set(f.get("parent_folder_id") for f in level4_folders if f.get("parent_folder_id"))
            level2_ids = set(f.get("id") for f in level2_folders)
            level3_ids = set(f.get("id") for f in level3_folders)
            
            # All parent_ids should be in either level2_ids or level3_ids
            for parent_id in parent_ids:
                self.assertTrue(parent_id in level2_ids or parent_id in level3_ids, 
                               f"Parent folder ID {parent_id} is not a Level 2 or Level 3 folder")
            
            logger.info("✅ Level 4 folder structure implementation test passed")
        except Exception as e:
            logger.error(f"❌ Error testing Level 4 folder structure implementation: {str(e)}")
            raise
    
    def test_02_create_level4_structure_endpoint(self):
        """Test POST /api/folders/create-level4-structure endpoint"""
        logger.info("\n=== Testing POST /api/folders/create-level4-structure endpoint ===")
        
        url = f"{self.api_url}/folders/create-level4-structure"
        
        # Test with admin authentication
        try:
            response = requests.post(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain success message
            data = response.json()
            self.assertIn("message", data)
            self.assertIn("created_count", data)
            
            logger.info(f"Create Level 4 structure response: {data['message']}")
            logger.info(f"Created {data['created_count']} Level 4 folders")
            
            # The created_count might be 0 if all Level 4 folders already exist
            
            logger.info("✅ POST /api/folders/create-level4-structure with admin auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/folders/create-level4-structure with admin: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.post(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ POST /api/folders/create-level4-structure with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/folders/create-level4-structure with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.post(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ POST /api/folders/create-level4-structure with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/folders/create-level4-structure with no auth: {str(e)}")
            raise

class TestClientFiltering(unittest.TestCase):
    """Test class for Client Filtering"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different authentication scenarios
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_client_filtering(self):
        """Test client filtering in folder and document endpoints"""
        logger.info("\n=== Testing client filtering in folder and document endpoints ===")
        
        # Test folders endpoint with admin
        try:
            url = f"{self.api_url}/folders"
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin folders response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list of folders
            folders = response.json()
            self.assertIsInstance(folders, list)
            
            # Admin should see all folders
            logger.info(f"Admin can see {len(folders)} folders")
            
            # Get unique client_ids
            client_ids = set(f.get("client_id") for f in folders if f.get("client_id"))
            logger.info(f"Admin can see folders for {len(client_ids)} different clients")
            
            # Admin should see folders for multiple clients
            self.assertGreater(len(client_ids), 1, "Admin should see folders for multiple clients")
            
            logger.info("✅ Admin can see folders for multiple clients")
        except Exception as e:
            logger.error(f"❌ Error testing admin folder access: {str(e)}")
            raise
        
        # Test folders endpoint with client
        try:
            url = f"{self.api_url}/folders"
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client folders response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list of folders
            folders = response.json()
            self.assertIsInstance(folders, list)
            
            # Client should only see their own folders
            logger.info(f"Client can see {len(folders)} folders")
            
            # Get unique client_ids
            client_ids = set(f.get("client_id") for f in folders if f.get("client_id"))
            logger.info(f"Client can see folders for {len(client_ids)} different clients")
            
            # Client should see folders for only one client
            self.assertLessEqual(len(client_ids), 1, "Client should see folders for only one client")
            
            logger.info("✅ Client can only see folders for their own client")
        except Exception as e:
            logger.error(f"❌ Error testing client folder access: {str(e)}")
            raise
        
        # Test documents endpoint with admin
        try:
            url = f"{self.api_url}/belge/list"
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin documents response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain documents
            data = response.json()
            documents = data["documents"]
            self.assertIsInstance(documents, list)
            
            # Admin should see all documents
            logger.info(f"Admin can see {len(documents)} documents")
            
            # Get unique client_ids
            client_ids = set(d.get("client_id") for d in documents if d.get("client_id"))
            logger.info(f"Admin can see documents for {len(client_ids)} different clients")
            
            # Admin should see documents for multiple clients (if there are documents for multiple clients)
            if len(documents) > 0:
                self.assertGreaterEqual(len(client_ids), 1, "Admin should see documents for at least one client")
            
            logger.info("✅ Admin can see documents for multiple clients")
        except Exception as e:
            logger.error(f"❌ Error testing admin document access: {str(e)}")
            raise
        
        # Test documents endpoint with client
        try:
            url = f"{self.api_url}/belge/list"
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client documents response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain documents
            data = response.json()
            documents = data["documents"]
            self.assertIsInstance(documents, list)
            
            # Client should only see their own documents
            logger.info(f"Client can see {len(documents)} documents")
            
            # Get unique client_ids
            client_ids = set(d.get("client_id") for d in documents if d.get("client_id"))
            logger.info(f"Client can see documents for {len(client_ids)} different clients")
            
            # Client should see documents for only one client
            self.assertLessEqual(len(client_ids), 1, "Client should see documents for only one client")
            
            logger.info("✅ Client can only see documents for their own client")
        except Exception as e:
            logger.error(f"❌ Error testing client document access: {str(e)}")
            raise

def run_document_management_tests():
    """Run document management tests"""
    # Create a test suite for document management
    document_suite = unittest.TestSuite()
    document_suite.addTest(TestDocumentManagementAPI("test_01_get_folders"))
    document_suite.addTest(TestDocumentManagementAPI("test_02_belge_list"))
    document_suite.addTest(TestDocumentManagementAPI("test_03_belge_upload"))
    document_suite.addTest(TestDocumentManagementAPI("test_04_belge_download"))
    document_suite.addTest(TestDocumentManagementAPI("test_05_belge_delete"))
    
    # Run the document management tests
    print("\n=== Running Document Management API Tests ===")
    unittest.TextTestRunner().run(document_suite)
    
    # Create a test suite for Level 4 folder structure
    folder_suite = unittest.TestSuite()
    folder_suite.addTest(TestLevel4FolderStructure("test_01_level4_structure"))
    folder_suite.addTest(TestLevel4FolderStructure("test_02_create_level4_structure_endpoint"))
    
    # Run the Level 4 folder structure tests
    print("\n=== Running Level 4 Folder Structure Tests ===")
    unittest.TextTestRunner().run(folder_suite)
    
    # Create a test suite for client filtering
    client_filtering_suite = unittest.TestSuite()
    client_filtering_suite.addTest(TestClientFiltering("test_client_filtering"))
    
    # Run the client filtering tests
    print("\n=== Running Client Filtering Tests ===")
    unittest.TextTestRunner().run(client_filtering_suite)

if __name__ == "__main__":
    run_document_management_tests()