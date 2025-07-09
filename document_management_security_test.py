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

# Test JWT tokens for different user types
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CLIENT1_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
CLIENT2_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0FOT19DTElFTlRfMDAxIiwiZW1haWwiOiJjYW5lcnBhbEBnbWFpbC5jb20iLCJuYW1lIjoiQ0FOTyBDbGllbnQifQ.signature"
CONSULTANT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ09OU1VMVEFOVF8wMDEiLCJlbWFpbCI6ImNvbnN1bHRhbnRAcm90YWthbGl0ZWRhbmlzbWFubGlrLmNvbSIsIm5hbWUiOiJDb25zdWx0YW50IFVzZXIifQ.signature"
INVALID_TOKEN = "invalid.token.format"

class TestDocumentManagementSecurity(unittest.TestCase):
    """Test class for document management security fixes"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client1 = {"Authorization": f"Bearer {CLIENT1_TOKEN}"}
        self.headers_client2 = {"Authorization": f"Bearer {CLIENT2_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test data
        self.test_client_id = "8bfd3a85-2483-4b63-9e80-e53747c3db7e"  # Example client ID
        
    def test_folders_endpoint_authentication(self):
        """Test that GET /api/folders endpoint requires authentication"""
        logger.info("\n=== Testing GET /api/folders endpoint authentication ===")
        
        url = f"{self.api_url}/folders"
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized or 403 Forbidden
            self.assertIn(response.status_code, [401, 403], 
                         "GET /api/folders should require authentication (401 or 403)")
            
            logger.info("✅ GET /api/folders endpoint requires authentication")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/folders authentication: {str(e)}")
            raise
        
        # Test with invalid token
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401, 
                            "GET /api/folders should return 401 for invalid token")
            
            logger.info("✅ GET /api/folders endpoint returns 401 for invalid token")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/folders with invalid token: {str(e)}")
            raise
    
    def test_belge_list_endpoint_authentication(self):
        """Test that GET /api/belge/list endpoint requires authentication"""
        logger.info("\n=== Testing GET /api/belge/list endpoint authentication ===")
        
        url = f"{self.api_url}/belge/list"
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized or 403 Forbidden
            self.assertIn(response.status_code, [401, 403], 
                         "GET /api/belge/list should require authentication (401 or 403)")
            
            logger.info("✅ GET /api/belge/list endpoint requires authentication")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/belge/list authentication: {str(e)}")
            raise
        
        # Test with invalid token
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401, 
                            "GET /api/belge/list should return 401 for invalid token")
            
            logger.info("✅ GET /api/belge/list endpoint returns 401 for invalid token")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/belge/list with invalid token: {str(e)}")
            raise
    
    def test_belge_upload_endpoint_authentication(self):
        """Test that POST /api/belge/upload endpoint requires authentication"""
        logger.info("\n=== Testing POST /api/belge/upload endpoint authentication ===")
        
        url = f"{self.api_url}/belge/upload"
        
        # Create a small test file
        test_file = io.BytesIO(b"test file content")
        test_file.name = "test.txt"
        
        # Form data for the request
        form_data = {
            "client_id": self.test_client_id,
            "folder_id": "test_folder_id",
            "document_name": "Test Document",
            "document_type": "STAGE_1_DOC",
            "stage": "STAGE_1",
            "description": "Test description"
        }
        
        files = {
            "file": ("test.txt", test_file, "text/plain")
        }
        
        # Test with no authentication
        try:
            response = requests.post(url, headers=self.headers_no_auth, files=files, data=form_data)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized or 403 Forbidden
            self.assertIn(response.status_code, [401, 403], 
                         "POST /api/belge/upload should require authentication (401 or 403)")
            
            logger.info("✅ POST /api/belge/upload endpoint requires authentication")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/belge/upload authentication: {str(e)}")
            raise
        
        # Test with invalid token
        try:
            response = requests.post(url, headers=self.headers_invalid, files=files, data=form_data)
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401, 
                            "POST /api/belge/upload should return 401 for invalid token")
            
            logger.info("✅ POST /api/belge/upload endpoint returns 401 for invalid token")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/belge/upload with invalid token: {str(e)}")
            raise
    
    def test_belge_download_endpoint_authentication(self):
        """Test that GET /api/belge/download/{id} endpoint requires authentication"""
        logger.info("\n=== Testing GET /api/belge/download/{id} endpoint authentication ===")
        
        # Use a random document ID for testing
        document_id = str(uuid.uuid4())
        url = f"{self.api_url}/belge/download/{document_id}"
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized or 403 Forbidden
            self.assertIn(response.status_code, [401, 403], 
                         "GET /api/belge/download/{id} should require authentication (401 or 403)")
            
            logger.info("✅ GET /api/belge/download/{id} endpoint requires authentication")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/belge/download/{id} authentication: {str(e)}")
            raise
        
        # Test with invalid token
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401, 
                            "GET /api/belge/download/{id} should return 401 for invalid token")
            
            logger.info("✅ GET /api/belge/download/{id} endpoint returns 401 for invalid token")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/belge/download/{id} with invalid token: {str(e)}")
            raise
    
    def test_belge_delete_endpoint_authentication(self):
        """Test that DELETE /api/belge/delete/{id} endpoint requires authentication"""
        logger.info("\n=== Testing DELETE /api/belge/delete/{id} endpoint authentication ===")
        
        # Use a random document ID for testing
        document_id = str(uuid.uuid4())
        url = f"{self.api_url}/belge/delete/{document_id}"
        
        # Test with no authentication
        try:
            response = requests.delete(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized or 403 Forbidden
            self.assertIn(response.status_code, [401, 403], 
                         "DELETE /api/belge/delete/{id} should require authentication (401 or 403)")
            
            logger.info("✅ DELETE /api/belge/delete/{id} endpoint requires authentication")
        except Exception as e:
            logger.error(f"❌ Error testing DELETE /api/belge/delete/{id} authentication: {str(e)}")
            raise
        
        # Test with invalid token
        try:
            response = requests.delete(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401, 
                            "DELETE /api/belge/delete/{id} should return 401 for invalid token")
            
            logger.info("✅ DELETE /api/belge/delete/{id} endpoint returns 401 for invalid token")
        except Exception as e:
            logger.error(f"❌ Error testing DELETE /api/belge/delete/{id} with invalid token: {str(e)}")
            raise
    
    def test_client_filtering_folders(self):
        """Test that client users can only see their own folders"""
        logger.info("\n=== Testing client filtering for folders ===")
        
        url = f"{self.api_url}/folders"
        
        # Test with admin user (should see all folders)
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            if response.status_code == 200:
                admin_data = response.json()
                admin_folder_count = len(admin_data)
                logger.info(f"Admin can see {admin_folder_count} folders")
                
                # Admin should see multiple folders
                self.assertGreater(admin_folder_count, 0, "Admin should see at least some folders")
                
                # Test with client1 user
                client1_response = requests.get(url, headers=self.headers_client1)
                logger.info(f"Client1 response status code: {client1_response.status_code}")
                
                if client1_response.status_code == 200:
                    client1_data = client1_response.json()
                    client1_folder_count = len(client1_data)
                    logger.info(f"Client1 can see {client1_folder_count} folders")
                    
                    # Client1 should see fewer folders than admin
                    if client1_folder_count > 0:
                        # If client1 has folders, they should be fewer than what admin sees
                        self.assertLessEqual(client1_folder_count, admin_folder_count, 
                                           "Client1 should see fewer or equal folders compared to admin")
                        
                        # Check that all folders belong to client1
                        client1_ids = set()
                        for folder in client1_data:
                            client_id = folder.get("client_id")
                            if client_id:
                                client1_ids.add(client_id)
                        
                        # Client1 should only see folders for one client ID (their own)
                        self.assertLessEqual(len(client1_ids), 1, 
                                           "Client1 should only see folders for one client ID (their own)")
                        
                        logger.info(f"Client1 sees folders for {len(client1_ids)} client IDs")
                    
                    # Test with client2 user
                    client2_response = requests.get(url, headers=self.headers_client2)
                    logger.info(f"Client2 response status code: {client2_response.status_code}")
                    
                    if client2_response.status_code == 200:
                        client2_data = client2_response.json()
                        client2_folder_count = len(client2_data)
                        logger.info(f"Client2 can see {client2_folder_count} folders")
                        
                        # Client2 should also see fewer folders than admin
                        if client2_folder_count > 0:
                            self.assertLessEqual(client2_folder_count, admin_folder_count, 
                                               "Client2 should see fewer or equal folders compared to admin")
                            
                            # Check that all folders belong to client2
                            client2_ids = set()
                            for folder in client2_data:
                                client_id = folder.get("client_id")
                                if client_id:
                                    client2_ids.add(client_id)
                            
                            # Client2 should only see folders for one client ID (their own)
                            self.assertLessEqual(len(client2_ids), 1, 
                                               "Client2 should only see folders for one client ID (their own)")
                            
                            logger.info(f"Client2 sees folders for {len(client2_ids)} client IDs")
                            
                            # Client1 and client2 should see different folders
                            if client1_folder_count > 0 and client2_folder_count > 0 and len(client1_ids) > 0 and len(client2_ids) > 0:
                                self.assertNotEqual(list(client1_ids)[0], list(client2_ids)[0], 
                                                  "Client1 and client2 should see folders for different client IDs")
                                logger.info("✅ Client1 and client2 see folders for different client IDs")
                    else:
                        logger.warning(f"Client2 response failed with status code {client2_response.status_code}")
                else:
                    logger.warning(f"Client1 response failed with status code {client1_response.status_code}")
            else:
                logger.warning(f"Admin response failed with status code {response.status_code}")
                
            logger.info("✅ Client filtering for folders test completed")
        except Exception as e:
            logger.error(f"❌ Error testing client filtering for folders: {str(e)}")
            raise
    
    def test_client_filtering_documents(self):
        """Test that client users can only see their own documents"""
        logger.info("\n=== Testing client filtering for documents ===")
        
        url = f"{self.api_url}/belge/list"
        
        # Test with admin user (should see all documents)
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            if response.status_code == 200:
                admin_data = response.json()
                admin_doc_count = len(admin_data.get("documents", []))
                logger.info(f"Admin can see {admin_doc_count} documents")
                
                # Test with client1 user
                client1_response = requests.get(url, headers=self.headers_client1)
                logger.info(f"Client1 response status code: {client1_response.status_code}")
                
                if client1_response.status_code == 200:
                    client1_data = client1_response.json()
                    client1_doc_count = len(client1_data.get("documents", []))
                    logger.info(f"Client1 can see {client1_doc_count} documents")
                    
                    # Client1 should see fewer documents than admin
                    if admin_doc_count > 0:
                        self.assertLessEqual(client1_doc_count, admin_doc_count, 
                                           "Client1 should see fewer or equal documents compared to admin")
                    
                    # Check that all documents belong to client1
                    if client1_doc_count > 0:
                        client1_ids = set()
                        for doc in client1_data.get("documents", []):
                            client_id = doc.get("client_id")
                            if client_id:
                                client1_ids.add(client_id)
                        
                        # Client1 should only see documents for one client ID (their own)
                        self.assertLessEqual(len(client1_ids), 1, 
                                           "Client1 should only see documents for one client ID (their own)")
                        
                        logger.info(f"Client1 sees documents for {len(client1_ids)} client IDs")
                    
                    # Test with client2 user
                    client2_response = requests.get(url, headers=self.headers_client2)
                    logger.info(f"Client2 response status code: {client2_response.status_code}")
                    
                    if client2_response.status_code == 200:
                        client2_data = client2_response.json()
                        client2_doc_count = len(client2_data.get("documents", []))
                        logger.info(f"Client2 can see {client2_doc_count} documents")
                        
                        # Client2 should also see fewer documents than admin
                        if admin_doc_count > 0:
                            self.assertLessEqual(client2_doc_count, admin_doc_count, 
                                               "Client2 should see fewer or equal documents compared to admin")
                        
                        # Check that all documents belong to client2
                        if client2_doc_count > 0:
                            client2_ids = set()
                            for doc in client2_data.get("documents", []):
                                client_id = doc.get("client_id")
                                if client_id:
                                    client2_ids.add(client_id)
                            
                            # Client2 should only see documents for one client ID (their own)
                            self.assertLessEqual(len(client2_ids), 1, 
                                               "Client2 should only see documents for one client ID (their own)")
                            
                            logger.info(f"Client2 sees documents for {len(client2_ids)} client IDs")
                            
                            # Client1 and client2 should see different documents
                            if client1_doc_count > 0 and client2_doc_count > 0 and len(client1_ids) > 0 and len(client2_ids) > 0:
                                self.assertNotEqual(list(client1_ids)[0], list(client2_ids)[0], 
                                                  "Client1 and client2 should see documents for different client IDs")
                                logger.info("✅ Client1 and client2 see documents for different client IDs")
                    else:
                        logger.warning(f"Client2 response failed with status code {client2_response.status_code}")
                else:
                    logger.warning(f"Client1 response failed with status code {client1_response.status_code}")
            else:
                logger.warning(f"Admin response failed with status code {response.status_code}")
                
            logger.info("✅ Client filtering for documents test completed")
        except Exception as e:
            logger.error(f"❌ Error testing client filtering for documents: {str(e)}")
            raise
    
    def test_consultant_access(self):
        """Test that consultant users can only see assigned client data"""
        logger.info("\n=== Testing consultant access to client data ===")
        
        # Test folders endpoint
        folders_url = f"{self.api_url}/folders"
        
        try:
            # Test with consultant user
            consultant_response = requests.get(folders_url, headers=self.headers_consultant)
            logger.info(f"Consultant response status code for folders: {consultant_response.status_code}")
            
            if consultant_response.status_code == 200:
                consultant_data = consultant_response.json()
                consultant_folder_count = len(consultant_data)
                logger.info(f"Consultant can see {consultant_folder_count} folders")
                
                # Consultant should see folders for multiple clients (their assigned clients)
                if consultant_folder_count > 0:
                    consultant_client_ids = set()
                    for folder in consultant_data:
                        client_id = folder.get("client_id")
                        if client_id:
                            consultant_client_ids.add(client_id)
                    
                    logger.info(f"Consultant sees folders for {len(consultant_client_ids)} client IDs")
                    
                    # Test documents endpoint
                    documents_url = f"{self.api_url}/belge/list"
                    consultant_doc_response = requests.get(documents_url, headers=self.headers_consultant)
                    logger.info(f"Consultant response status code for documents: {consultant_doc_response.status_code}")
                    
                    if consultant_doc_response.status_code == 200:
                        consultant_doc_data = consultant_doc_response.json()
                        consultant_doc_count = len(consultant_doc_data.get("documents", []))
                        logger.info(f"Consultant can see {consultant_doc_count} documents")
                        
                        # Check client IDs in documents
                        if consultant_doc_count > 0:
                            consultant_doc_client_ids = set()
                            for doc in consultant_doc_data.get("documents", []):
                                client_id = doc.get("client_id")
                                if client_id:
                                    consultant_doc_client_ids.add(client_id)
                            
                            logger.info(f"Consultant sees documents for {len(consultant_doc_client_ids)} client IDs")
                            
                            # The client IDs in documents should be a subset of the client IDs in folders
                            if len(consultant_doc_client_ids) > 0 and len(consultant_client_ids) > 0:
                                for doc_client_id in consultant_doc_client_ids:
                                    self.assertIn(doc_client_id, consultant_client_ids, 
                                                "Document client ID should be in folder client IDs")
                                
                                logger.info("✅ Consultant sees documents only for clients they can see folders for")
                    else:
                        logger.warning(f"Consultant documents response failed with status code {consultant_doc_response.status_code}")
            else:
                logger.warning(f"Consultant folders response failed with status code {consultant_response.status_code}")
                
            logger.info("✅ Consultant access test completed")
        except Exception as e:
            logger.error(f"❌ Error testing consultant access: {str(e)}")
            raise
    
    def test_authorization_cross_client_access(self):
        """Test that client users cannot access other client's data"""
        logger.info("\n=== Testing authorization for cross-client access ===")
        
        # First, get client1's folders
        folders_url = f"{self.api_url}/folders"
        
        try:
            client1_response = requests.get(folders_url, headers=self.headers_client1)
            logger.info(f"Client1 response status code for folders: {client1_response.status_code}")
            
            if client1_response.status_code == 200:
                client1_data = client1_response.json()
                client1_folder_count = len(client1_data)
                logger.info(f"Client1 can see {client1_folder_count} folders")
                
                # Find a folder that belongs to client1
                client1_folder = None
                for folder in client1_data:
                    if folder.get("level") == 0:  # Root folder
                        client1_folder = folder
                        break
                
                if client1_folder:
                    logger.info(f"Found client1 folder: {client1_folder.get('name')}")
                    
                    # Now try to access this folder's documents with client2's token
                    documents_url = f"{self.api_url}/belge/list"
                    params = {"folder_id": client1_folder.get("id")}
                    
                    client2_doc_response = requests.get(documents_url, headers=self.headers_client2, params=params)
                    logger.info(f"Client2 response status code for client1's documents: {client2_doc_response.status_code}")
                    
                    # Should get 403 Forbidden or empty results
                    if client2_doc_response.status_code == 200:
                        client2_doc_data = client2_doc_response.json()
                        client2_doc_count = len(client2_doc_data.get("documents", []))
                        logger.info(f"Client2 can see {client2_doc_count} documents for client1's folder")
                        
                        # Client2 should not see any documents for client1's folder
                        self.assertEqual(client2_doc_count, 0, 
                                       "Client2 should not see any documents for client1's folder")
                        
                        logger.info("✅ Client2 cannot see client1's documents")
                    elif client2_doc_response.status_code == 403:
                        logger.info("✅ Client2 gets 403 Forbidden when trying to access client1's documents")
                    else:
                        logger.warning(f"Unexpected status code: {client2_doc_response.status_code}")
                else:
                    logger.warning("Could not find a root folder for client1")
            else:
                logger.warning(f"Client1 folders response failed with status code {client1_response.status_code}")
                
            logger.info("✅ Authorization for cross-client access test completed")
        except Exception as e:
            logger.error(f"❌ Error testing authorization for cross-client access: {str(e)}")
            raise
    
    def test_token_validation(self):
        """Test token validation for API calls"""
        logger.info("\n=== Testing token validation for API calls ===")
        
        # Test endpoints with invalid token
        endpoints = [
            {"url": f"{self.api_url}/folders", "method": "get"},
            {"url": f"{self.api_url}/belge/list", "method": "get"},
            {"url": f"{self.api_url}/belge/download/{str(uuid.uuid4())}", "method": "get"},
            {"url": f"{self.api_url}/belge/delete/{str(uuid.uuid4())}", "method": "delete"}
        ]
        
        for endpoint in endpoints:
            url = endpoint["url"]
            method = endpoint["method"]
            
            try:
                # Test with invalid token
                if method == "get":
                    response = requests.get(url, headers=self.headers_invalid)
                elif method == "delete":
                    response = requests.delete(url, headers=self.headers_invalid)
                else:
                    continue
                
                logger.info(f"Invalid token response status code for {url}: {response.status_code}")
                
                # Should get 401 Unauthorized
                self.assertEqual(response.status_code, 401, 
                                f"{method.upper()} {url} should return 401 for invalid token")
                
                logger.info(f"✅ {method.upper()} {url} returns 401 for invalid token")
                
                # Test with no token
                if method == "get":
                    response = requests.get(url, headers=self.headers_no_auth)
                elif method == "delete":
                    response = requests.delete(url, headers=self.headers_no_auth)
                else:
                    continue
                
                logger.info(f"No token response status code for {url}: {response.status_code}")
                
                # Should get 403 Forbidden
                self.assertIn(response.status_code, [401, 403], 
                             f"{method.upper()} {url} should return 401 or 403 for no token")
                
                logger.info(f"✅ {method.upper()} {url} returns {response.status_code} for no token")
            except Exception as e:
                logger.error(f"❌ Error testing token validation for {url}: {str(e)}")
                raise
        
        logger.info("✅ Token validation test completed")

def run_document_management_security_tests():
    """Run all document management security tests"""
    logger.info("Starting document management security tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add all test methods
    suite.addTest(TestDocumentManagementSecurity("test_folders_endpoint_authentication"))
    suite.addTest(TestDocumentManagementSecurity("test_belge_list_endpoint_authentication"))
    suite.addTest(TestDocumentManagementSecurity("test_belge_upload_endpoint_authentication"))
    suite.addTest(TestDocumentManagementSecurity("test_belge_download_endpoint_authentication"))
    suite.addTest(TestDocumentManagementSecurity("test_belge_delete_endpoint_authentication"))
    suite.addTest(TestDocumentManagementSecurity("test_client_filtering_folders"))
    suite.addTest(TestDocumentManagementSecurity("test_client_filtering_documents"))
    suite.addTest(TestDocumentManagementSecurity("test_consultant_access"))
    suite.addTest(TestDocumentManagementSecurity("test_authorization_cross_client_access"))
    suite.addTest(TestDocumentManagementSecurity("test_token_validation"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Document Management Security Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All document management security tests PASSED")
        return True
    else:
        logger.error("Some document management security tests FAILED")
        return False

if __name__ == "__main__":
    run_document_management_security_tests()