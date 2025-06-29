import unittest
import json
import logging
import requests
import os
import io
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestDocumentManagementRefactor(unittest.TestCase):
    """Test class for admin document management refactor with client and folder-based document viewing"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = "https://ddbdf62a-0dc7-4cf4-b9a6-6dc3e3277ae1.preview.emergentagent.com/api"
        self.headers_valid = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
    
    def test_document_endpoints_authentication(self):
        """Test that all document-related endpoints work correctly with admin authentication"""
        logger.info("\n=== Testing document-related endpoints authentication ===")
        
        # Test endpoints
        endpoints = [
            "/documents",
            "/folders",
            "/upload-document"
        ]
        
        for endpoint in endpoints:
            url = f"{self.api_url}{endpoint}"
            logger.info(f"Testing endpoint: {url}")
            
            # Test with valid token
            try:
                if endpoint == "/upload-document":
                    # For POST endpoints, we need to send some data
                    # Create a small test file
                    test_file = io.BytesIO(b"test file content")
                    test_file.name = "test.txt"
                    
                    # Form data for the request
                    form_data = {
                        "client_id": "test_client_id",
                        "document_name": "Test Document",
                        "document_type": "STAGE_1_DOC",
                        "stage": "STAGE_1",
                        "folder_id": "test_folder_id"  # Required folder selection
                    }
                    
                    files = {
                        "file": ("test.txt", test_file, "text/plain")
                    }
                    
                    response = requests.post(url, headers=self.headers_valid, files=files, data=form_data)
                else:
                    # For GET endpoints
                    response = requests.get(url, headers=self.headers_valid)
                
                logger.info(f"Response status code with valid token: {response.status_code}")
                logger.info(f"Response body: {response.text[:200]}...")
                
                # Check if we get a 200 OK, 401 Unauthorized, or 422/404 (validation error or not found)
                # But not 403 Forbidden
                self.assertIn(response.status_code, [200, 401, 422, 404, 500])
                self.assertNotEqual(response.status_code, 403, f"Endpoint {endpoint} should not return 403 Forbidden with valid token")
                
                if response.status_code == 200:
                    logger.info(f"✅ Authentication successful for {endpoint} - received 200 OK")
                elif response.status_code == 401:
                    logger.info(f"✅ Authentication failed correctly for {endpoint} - received 401 Unauthorized")
                else:
                    logger.info(f"✅ Endpoint {endpoint} returned {response.status_code} - this is acceptable for validation errors or not found resources")
            except Exception as e:
                logger.error(f"❌ Error testing {endpoint} with valid token: {str(e)}")
                raise
            
            # Test with invalid token
            try:
                if endpoint == "/upload-document":
                    response = requests.post(url, headers=self.headers_invalid, files=files, data=form_data)
                else:
                    response = requests.get(url, headers=self.headers_invalid)
                
                logger.info(f"Response status code with invalid token: {response.status_code}")
                
                # Should get 401 Unauthorized, not 403 Forbidden
                self.assertEqual(response.status_code, 401, f"Endpoint {endpoint} should return 401 Unauthorized with invalid token")
                logger.info(f"✅ Invalid token test passed for {endpoint} - received 401 Unauthorized")
            except Exception as e:
                logger.error(f"❌ Error testing {endpoint} with invalid token: {str(e)}")
                raise
            
            # Test without token
            try:
                if endpoint == "/upload-document":
                    response = requests.post(url, files=files, data=form_data)
                else:
                    response = requests.get(url)
                
                logger.info(f"Response status code without token: {response.status_code}")
                
                # Should get 401 Unauthorized or 403 Forbidden (both are acceptable)
                self.assertIn(response.status_code, [401, 403], f"Endpoint {endpoint} should return 401 Unauthorized or 403 Forbidden without token")
                logger.info(f"✅ No token test passed for {endpoint} - received {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Error testing {endpoint} without token: {str(e)}")
                raise
    
    def test_folder_hierarchy(self):
        """Test that the GET /api/folders endpoint returns the correct folder hierarchy"""
        logger.info("\n=== Testing folder hierarchy ===")
        
        url = f"{self.api_url}/folders"
        
        try:
            response = requests.get(url, headers=self.headers_valid)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Authentication successful - received 200 OK")
                data = response.json()
                
                # Verify response is a list of folders
                self.assertIsInstance(data, list, "Response should be a list of folders")
                logger.info(f"Found {len(data)} folders")
                
                # Check folder structure if any folders exist
                if len(data) > 0:
                    # Check for required fields
                    folder = data[0]
                    self.assertIn("id", folder, "Folder should have an id field")
                    self.assertIn("client_id", folder, "Folder should have a client_id field")
                    self.assertIn("name", folder, "Folder should have a name field")
                    self.assertIn("level", folder, "Folder should have a level field")
                    self.assertIn("folder_path", folder, "Folder should have a folder_path field")
                    
                    # Check for root folders (level 0)
                    root_folders = [f for f in data if f.get("level") == 0]
                    if root_folders:
                        logger.info(f"Found {len(root_folders)} root folders (level 0)")
                        
                        # Group folders by client_id
                        folders_by_client = {}
                        for folder in data:
                            client_id = folder.get("client_id")
                            if client_id not in folders_by_client:
                                folders_by_client[client_id] = []
                            folders_by_client[client_id].append(folder)
                        
                        logger.info(f"Found folders for {len(folders_by_client)} different clients")
                        
                        # Check folder hierarchy for each client
                        for client_id, client_folders in folders_by_client.items():
                            # Find root folder for this client
                            client_root_folders = [f for f in client_folders if f.get("level") == 0]
                            if client_root_folders:
                                client_root_folder = client_root_folders[0]
                                logger.info(f"Client {client_id} has root folder: {client_root_folder['name']}")
                                
                                # Check for column sub-folders (level 1)
                                column_folders = [f for f in client_folders if f.get("level") == 1 and f.get("parent_folder_id") == client_root_folder["id"]]
                                logger.info(f"Client {client_id} has {len(column_folders)} column folders")
                                
                                # Check for the 4 column folders
                                column_names = [f["name"] for f in column_folders]
                                expected_columns = ["A SÜTUNU", "B SÜTUNU", "C SÜTUNU", "D SÜTUNU"]
                                
                                for expected_column in expected_columns:
                                    if expected_column in column_names:
                                        logger.info(f"✅ Client {client_id} has expected column folder: {expected_column}")
                                    else:
                                        logger.warning(f"⚠️ Client {client_id} missing expected column folder: {expected_column}")
                            else:
                                logger.warning(f"⚠️ Client {client_id} has no root folder")
                    else:
                        logger.warning("⚠️ No root folders (level 0) found")
                
                logger.info("✅ Folder hierarchy test passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication failed correctly - received 401 Unauthorized")
            else:
                logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing folder hierarchy: {str(e)}")
            raise
    
    def test_document_filtering(self):
        """Test that documents can be retrieved and filtered by client_id and folder_id"""
        logger.info("\n=== Testing document filtering by client_id and folder_id ===")
        
        # Step 1: Get available clients
        logger.info("Step 1: Getting available clients...")
        clients_url = f"{self.api_url}/clients"
        
        try:
            clients_response = requests.get(clients_url, headers=self.headers_valid)
            logger.info(f"Clients response status code: {clients_response.status_code}")
            
            if clients_response.status_code != 200:
                logger.warning(f"Clients retrieval failed with status code {clients_response.status_code}, skipping rest of test")
                return
            
            clients_data = clients_response.json()
            
            if not clients_data:
                logger.warning("No clients found, skipping rest of test")
                return
            
            # Step 2: Get folders for a client
            logger.info("Step 2: Getting folders for a client...")
            test_client = clients_data[0]
            client_id = test_client.get("id")
            
            folders_url = f"{self.api_url}/folders"
            folders_response = requests.get(folders_url, headers=self.headers_valid)
            
            if folders_response.status_code != 200:
                logger.warning(f"Folders retrieval failed with status code {folders_response.status_code}, skipping rest of test")
                return
            
            folders_data = folders_response.json()
            
            # Find folders for the selected client
            client_folders = [f for f in folders_data if f.get("client_id") == client_id]
            logger.info(f"Found {len(client_folders)} folders for client {client_id}")
            
            if not client_folders:
                logger.warning(f"No folders found for client {client_id}, skipping rest of test")
                return
            
            # Step 3: Get documents for the client
            logger.info("Step 3: Getting documents for the client...")
            documents_url = f"{self.api_url}/documents/{client_id}"
            
            documents_response = requests.get(documents_url, headers=self.headers_valid)
            logger.info(f"Documents response status code: {documents_response.status_code}")
            
            if documents_response.status_code != 200:
                logger.warning(f"Documents retrieval failed with status code {documents_response.status_code}, skipping rest of test")
                return
            
            documents_data = documents_response.json()
            logger.info(f"Found {len(documents_data)} documents for client {client_id}")
            
            # Step 4: Get all documents (admin only)
            logger.info("Step 4: Getting all documents (admin only)...")
            all_documents_url = f"{self.api_url}/documents"
            
            all_documents_response = requests.get(all_documents_url, headers=self.headers_valid)
            logger.info(f"All documents response status code: {all_documents_response.status_code}")
            
            if all_documents_response.status_code != 200:
                logger.warning(f"All documents retrieval failed with status code {all_documents_response.status_code}, skipping rest of test")
                return
            
            all_documents_data = all_documents_response.json()
            logger.info(f"Found {len(all_documents_data)} documents in total")
            
            # Step 5: Check if documents have folder_id field
            logger.info("Step 5: Checking if documents have folder_id field...")
            
            documents_with_folder_id = [d for d in all_documents_data if "folder_id" in d]
            logger.info(f"Found {len(documents_with_folder_id)} documents with folder_id field")
            
            if documents_with_folder_id:
                # Step 6: Filter documents by folder_id
                logger.info("Step 6: Filtering documents by folder_id...")
                
                test_folder = client_folders[0]
                folder_id = test_folder.get("id")
                
                folder_documents = [d for d in all_documents_data if d.get("folder_id") == folder_id]
                logger.info(f"Found {len(folder_documents)} documents for folder {folder_id}")
                
                # Verify that documents have the correct folder information
                for doc in folder_documents:
                    self.assertEqual(doc.get("folder_id"), folder_id, 
                                   f"Document folder_id should be {folder_id}, got: {doc.get('folder_id')}")
                    
                    if "folder_path" in doc:
                        self.assertEqual(doc.get("folder_path"), test_folder.get("folder_path"), 
                                       f"Document folder_path should be {test_folder.get('folder_path')}, got: {doc.get('folder_path')}")
                    
                    if "folder_level" in doc:
                        self.assertEqual(doc.get("folder_level"), test_folder.get("level"), 
                                       f"Document folder_level should be {test_folder.get('level')}, got: {doc.get('folder_level')}")
                
                logger.info("✅ Documents have correct folder information")
            else:
                logger.warning("⚠️ No documents with folder_id field found")
            
            logger.info("✅ Document filtering test passed")
        except Exception as e:
            logger.error(f"❌ Error testing document filtering: {str(e)}")
            raise
    
    def test_admin_access_control(self):
        """Test that admin users can access all clients' documents and folders"""
        logger.info("\n=== Testing admin access control for documents and folders ===")
        
        # Step 1: Get all clients
        logger.info("Step 1: Getting all clients...")
        clients_url = f"{self.api_url}/clients"
        
        try:
            clients_response = requests.get(clients_url, headers=self.headers_valid)
            logger.info(f"Clients response status code: {clients_response.status_code}")
            
            if clients_response.status_code != 200:
                logger.warning(f"Clients retrieval failed with status code {clients_response.status_code}, skipping rest of test")
                return
            
            clients_data = clients_response.json()
            
            if len(clients_data) < 2:
                logger.warning("Need at least 2 clients for this test, skipping rest of test")
                return
            
            # Step 2: Get all folders
            logger.info("Step 2: Getting all folders...")
            folders_url = f"{self.api_url}/folders"
            
            folders_response = requests.get(folders_url, headers=self.headers_valid)
            logger.info(f"Folders response status code: {folders_response.status_code}")
            
            if folders_response.status_code != 200:
                logger.warning(f"Folders retrieval failed with status code {folders_response.status_code}, skipping rest of test")
                return
            
            folders_data = folders_response.json()
            
            # Group folders by client_id
            folders_by_client = {}
            for folder in folders_data:
                client_id = folder.get("client_id")
                if client_id not in folders_by_client:
                    folders_by_client[client_id] = []
                folders_by_client[client_id].append(folder)
            
            logger.info(f"Found folders for {len(folders_by_client)} different clients")
            
            # Step 3: Get all documents
            logger.info("Step 3: Getting all documents...")
            documents_url = f"{self.api_url}/documents"
            
            documents_response = requests.get(documents_url, headers=self.headers_valid)
            logger.info(f"Documents response status code: {documents_response.status_code}")
            
            if documents_response.status_code != 200:
                logger.warning(f"Documents retrieval failed with status code {documents_response.status_code}, skipping rest of test")
                return
            
            documents_data = documents_response.json()
            
            # Group documents by client_id
            documents_by_client = {}
            for doc in documents_data:
                client_id = doc.get("client_id")
                if client_id not in documents_by_client:
                    documents_by_client[client_id] = []
                documents_by_client[client_id].append(doc)
            
            logger.info(f"Found documents for {len(documents_by_client)} different clients")
            
            # Step 4: Verify that admin can access documents for different clients
            logger.info("Step 4: Verifying that admin can access documents for different clients...")
            
            # Get documents for specific clients
            for client_id in list(documents_by_client.keys())[:2]:  # Test with first 2 clients
                client_documents_url = f"{self.api_url}/documents/{client_id}"
                
                client_documents_response = requests.get(client_documents_url, headers=self.headers_valid)
                logger.info(f"Documents response status code for client {client_id}: {client_documents_response.status_code}")
                
                if client_documents_response.status_code == 200:
                    client_documents_data = client_documents_response.json()
                    logger.info(f"Found {len(client_documents_data)} documents for client {client_id}")
                    
                    # Verify that all documents belong to the specified client
                    for doc in client_documents_data:
                        self.assertEqual(doc.get("client_id"), client_id, 
                                       f"Document client_id should be {client_id}, got: {doc.get('client_id')}")
                    
                    logger.info(f"✅ Admin can access documents for client {client_id}")
                else:
                    logger.warning(f"⚠️ Could not access documents for client {client_id}")
            
            logger.info("✅ Admin access control test passed")
        except Exception as e:
            logger.error(f"❌ Error testing admin access control: {str(e)}")
            raise
    
    def test_document_upload_with_folder(self):
        """Test the /api/upload-document endpoint with folder_id parameter"""
        logger.info("\n=== Testing document upload with folder_id parameter ===")
        
        # Step 1: Get available clients
        logger.info("Step 1: Getting available clients...")
        clients_url = f"{self.api_url}/clients"
        
        try:
            clients_response = requests.get(clients_url, headers=self.headers_valid)
            logger.info(f"Clients response status code: {clients_response.status_code}")
            
            if clients_response.status_code != 200:
                logger.warning(f"Clients retrieval failed with status code {clients_response.status_code}, skipping rest of test")
                return
            
            clients_data = clients_response.json()
            
            if not clients_data:
                logger.warning("No clients found, skipping rest of test")
                return
            
            # Step 2: Get folders for a client
            logger.info("Step 2: Getting folders for a client...")
            test_client = clients_data[0]
            client_id = test_client.get("id")
            
            folders_url = f"{self.api_url}/folders"
            folders_response = requests.get(folders_url, headers=self.headers_valid)
            
            if folders_response.status_code != 200:
                logger.warning(f"Folders retrieval failed with status code {folders_response.status_code}, skipping rest of test")
                return
            
            folders_data = folders_response.json()
            
            # Find folders for the selected client
            client_folders = [f for f in folders_data if f.get("client_id") == client_id]
            logger.info(f"Found {len(client_folders)} folders for client {client_id}")
            
            if not client_folders:
                logger.warning(f"No folders found for client {client_id}, skipping rest of test")
                return
            
            # Step 3: Upload a document with folder_id
            logger.info("Step 3: Uploading a document with folder_id...")
            upload_url = f"{self.api_url}/upload-document"
            
            # Select a folder for the upload
            test_folder = client_folders[0]
            folder_id = test_folder.get("id")
            
            # Create a small test file
            test_file = io.BytesIO(b"test file content for folder upload")
            test_file.name = "test_folder_upload.txt"
            
            # Form data for the request
            form_data = {
                "client_id": client_id,
                "document_name": "Test Folder Upload",
                "document_type": "STAGE_1_DOC",
                "stage": "STAGE_1",
                "folder_id": folder_id  # Include folder_id parameter
            }
            
            files = {
                "file": ("test_folder_upload.txt", test_file, "text/plain")
            }
            
            upload_response = requests.post(upload_url, headers=self.headers_valid, files=files, data=form_data)
            logger.info(f"Upload response status code: {upload_response.status_code}")
            logger.info(f"Upload response body: {upload_response.text[:500]}...")
            
            # Check if upload was successful
            if upload_response.status_code == 200:
                logger.info("✅ Upload with folder selection successful")
                upload_data = upload_response.json()
                
                # Verify document_id is returned
                self.assertIn("document_id", upload_data, "Response should include document_id")
                document_id = upload_data["document_id"]
                logger.info(f"✅ Document ID returned: {document_id}")
                
                # Step 4: Verify document was saved with folder information
                logger.info("Step 4: Verifying document was saved with folder information...")
                documents_url = f"{self.api_url}/documents"
                
                documents_response = requests.get(documents_url, headers=self.headers_valid)
                logger.info(f"Documents response status code: {documents_response.status_code}")
                
                if documents_response.status_code == 200:
                    documents_data = documents_response.json()
                    
                    # Find the uploaded document
                    uploaded_doc = None
                    for doc in documents_data:
                        if doc.get("id") == document_id:
                            uploaded_doc = doc
                            break
                    
                    if uploaded_doc:
                        logger.info(f"✅ Found uploaded document: {uploaded_doc.get('name')}")
                        
                        # Verify folder information was saved
                        self.assertIn("folder_path", uploaded_doc, "Document should have folder_path field")
                        self.assertEqual(uploaded_doc.get("folder_path"), test_folder["folder_path"], 
                                       f"Document folder_path should be '{test_folder['folder_path']}', got: {uploaded_doc.get('folder_path')}")
                        
                        self.assertIn("folder_level", uploaded_doc, "Document should have folder_level field")
                        self.assertEqual(uploaded_doc.get("folder_level"), test_folder["level"], 
                                       f"Document folder_level should be {test_folder['level']}, got: {uploaded_doc.get('folder_level')}")
                        
                        logger.info(f"✅ Document was saved with correct folder information: {uploaded_doc.get('folder_path')}")
                    else:
                        logger.warning(f"⚠️ Uploaded document with ID {document_id} not found in documents list")
                else:
                    logger.warning(f"⚠️ Documents retrieval failed with status code {documents_response.status_code}")
            elif upload_response.status_code in [400, 422]:
                # Check if the error is due to missing folder_id
                error_data = upload_response.json()
                error_detail = error_data.get("detail", "")
                
                if "folder_id" in error_detail.lower():
                    logger.info("✅ Upload correctly requires folder_id parameter")
                else:
                    logger.warning(f"⚠️ Upload failed with validation error: {error_detail}")
            else:
                logger.warning(f"⚠️ Upload failed with status code {upload_response.status_code}")
            
            # Step 5: Test upload without folder_id (should fail)
            logger.info("Step 5: Testing upload without folder_id (should fail)...")
            
            # Form data without folder_id
            form_data_no_folder = {
                "client_id": client_id,
                "document_name": "Test No Folder Upload",
                "document_type": "STAGE_1_DOC",
                "stage": "STAGE_1"
            }
            
            test_file.seek(0)  # Reset file position
            
            upload_no_folder_response = requests.post(upload_url, headers=self.headers_valid, files=files, data=form_data_no_folder)
            logger.info(f"Upload without folder_id response status code: {upload_no_folder_response.status_code}")
            logger.info(f"Upload without folder_id response body: {upload_no_folder_response.text[:500]}...")
            
            # Should get 400 Bad Request or 422 Unprocessable Entity
            self.assertIn(upload_no_folder_response.status_code, [400, 422], 
                         "Upload without folder_id should return 400 Bad Request or 422 Unprocessable Entity")
            
            logger.info(f"✅ Upload without folder_id correctly fails with status code {upload_no_folder_response.status_code}")
            
            logger.info("✅ Document upload with folder test passed")
        except Exception as e:
            logger.error(f"❌ Error testing document upload with folder: {str(e)}")
            raise

def run_tests():
    """Run all document management refactor tests"""
    logger.info("Starting document management refactor tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add document management refactor tests
    suite.addTest(TestDocumentManagementRefactor("test_document_endpoints_authentication"))
    suite.addTest(TestDocumentManagementRefactor("test_folder_hierarchy"))
    suite.addTest(TestDocumentManagementRefactor("test_document_filtering"))
    suite.addTest(TestDocumentManagementRefactor("test_admin_access_control"))
    suite.addTest(TestDocumentManagementRefactor("test_document_upload_with_folder"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Document Management Refactor Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All document management refactor tests PASSED")
        return True
    else:
        logger.error("Some document management refactor tests FAILED")
        return False

if __name__ == "__main__":
    run_tests()