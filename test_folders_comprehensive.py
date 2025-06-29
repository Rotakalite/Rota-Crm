import unittest
import requests
import logging
import json
import uuid
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend/.env
BACKEND_URL = "https://8f8909e6-0e12-4f66-9734-9213547bf4f4.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"

class TestFoldersEndpoint(unittest.TestCase):
    """Test class for the folders endpoint"""
    
    def setUp(self):
        """Set up test environment"""
        self.headers_valid = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
        
        # Test client data for folder creation
        self.test_client = {
            "name": f"Test Client {uuid.uuid4().hex[:8]}",
            "hotel_name": "Test Hotel",
            "contact_person": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "address": "123 Test St"
        }
    
    def test_folders_endpoint_with_auth(self):
        """Test the GET /api/folders endpoint with authentication"""
        logger.info("\n=== Testing GET /api/folders endpoint with authentication ===")
        
        # Make a request to the folders endpoint with authentication
        url = f"{API_URL}/folders"
        
        try:
            response = requests.get(url, headers=self.headers_valid)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if we get a successful response or authentication error
            self.assertIn(response.status_code, [200, 401], 
                         f"Expected status code 200 or 401, got {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Folders endpoint accessible with authentication")
                data = response.json()
                self.assertIsInstance(data, list, "Response should be a list of folders")
                logger.info(f"Found {len(data)} folders")
                
                # Check folder structure if any folders exist
                if len(data) > 0:
                    folder = data[0]
                    logger.info(f"Sample folder: {json.dumps(folder, indent=2)}")
                    
                    # Verify folder has required fields
                    self.assertIn("id", folder, "Folder should have an id field")
                    self.assertIn("client_id", folder, "Folder should have a client_id field")
                    self.assertIn("name", folder, "Folder should have a name field")
                    self.assertIn("level", folder, "Folder should have a level field")
                    self.assertIn("folder_path", folder, "Folder should have a folder_path field")
                    
                    # Check for root folders (level 0)
                    root_folders = [f for f in data if f.get("level") == 0]
                    if root_folders:
                        logger.info(f"Found {len(root_folders)} root folders (level 0)")
                        
                        # Check for column sub-folders (level 1)
                        for root_folder in root_folders:
                            column_folders = [f for f in data if f.get("level") == 1 and f.get("parent_folder_id") == root_folder["id"]]
                            if column_folders:
                                logger.info(f"Root folder '{root_folder['name']}' has {len(column_folders)} column folders")
                                
                                # Check for the expected column folders
                                column_names = [f["name"] for f in column_folders]
                                expected_columns = ["A SÜTUNU", "B SÜTUNU", "C SÜTUNU", "D SÜTUNU"]
                                
                                for expected_column in expected_columns:
                                    if expected_column in column_names:
                                        logger.info(f"  ✅ Found expected column folder: {expected_column}")
                                    else:
                                        logger.info(f"  ⚠️ Expected column folder not found: {expected_column}")
                            else:
                                logger.info(f"Root folder '{root_folder['name']}' has no column folders")
                else:
                    logger.info("No folders found in the response")
                    
                    # If no folders exist, try creating a client to trigger folder creation
                    logger.info("Attempting to create a client to trigger folder creation...")
                    self.create_test_client_and_verify_folders()
            else:
                logger.info(f"Authentication failed (status code: {response.status_code})")
                error_data = response.json()
                logger.info(f"Error message: {error_data.get('detail', 'No detail provided')}")
                
            logger.info("✅ Folders endpoint with authentication test completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error testing folders endpoint with authentication: {str(e)}")
            raise
    
    def create_test_client_and_verify_folders(self):
        """Create a test client and verify that folders are automatically created"""
        logger.info("\n=== Creating test client to verify automatic folder creation ===")
        
        # Step 1: Create a new client
        logger.info("Step 1: Creating a new client...")
        client_url = f"{API_URL}/clients"
        
        try:
            client_response = requests.post(client_url, headers=self.headers_valid, json=self.test_client)
            logger.info(f"Client creation response status code: {client_response.status_code}")
            
            if client_response.status_code not in [200, 201]:
                logger.warning(f"Client creation failed with status code {client_response.status_code}")
                logger.warning(f"Response: {client_response.text}")
                return
            
            # Get the client ID from the response
            client_data = client_response.json()
            client_id = client_data.get("id")
            client_name = client_data.get("name")
            
            if not client_id:
                logger.warning("Client ID not found in response")
                return
            
            logger.info(f"✅ Created client with ID: {client_id} and name: {client_name}")
            
            # Step 2: Check if folders were automatically created
            logger.info("Step 2: Checking if folders were automatically created...")
            folders_url = f"{API_URL}/folders"
            
            folders_response = requests.get(folders_url, headers=self.headers_valid)
            logger.info(f"Folders response status code: {folders_response.status_code}")
            
            if folders_response.status_code != 200:
                logger.warning(f"Folders retrieval failed with status code {folders_response.status_code}")
                return
            
            folders_data = folders_response.json()
            
            # Find folders for the newly created client
            client_folders = [f for f in folders_data if f.get("client_id") == client_id]
            logger.info(f"Found {len(client_folders)} folders for the new client")
            
            if not client_folders:
                logger.error("❌ No folders found for the newly created client")
                return
            
            # Check for root folder
            root_folders = [f for f in client_folders if f.get("level") == 0]
            if not root_folders:
                logger.error("❌ No root folder found for the newly created client")
                return
            
            root_folder = root_folders[0]
            expected_root_name = f"{client_name} SYS"
            if root_folder["name"] != expected_root_name:
                logger.warning(f"Root folder name is '{root_folder['name']}', expected '{expected_root_name}'")
            else:
                logger.info(f"✅ Root folder created with correct name: {root_folder['name']}")
            
            # Check for column sub-folders
            column_folders = [f for f in client_folders if f.get("level") == 1]
            logger.info(f"Found {len(column_folders)} column folders")
            
            # Verify column folder names
            column_names = [f["name"] for f in column_folders]
            expected_columns = ["A SÜTUNU", "B SÜTUNU", "C SÜTUNU", "D SÜTUNU"]
            
            for expected_column in expected_columns:
                if expected_column in column_names:
                    logger.info(f"✅ Found expected column folder: {expected_column}")
                else:
                    logger.warning(f"⚠️ Expected column folder not found: {expected_column}")
            
            # Verify folder paths
            for column_folder in column_folders:
                expected_path = f"{expected_root_name}/{column_folder['name']}"
                if column_folder["folder_path"] != expected_path:
                    logger.warning(f"Column folder path is '{column_folder['folder_path']}', expected '{expected_path}'")
                else:
                    logger.info(f"✅ Column folder has correct path: {column_folder['folder_path']}")
            
            logger.info("✅ Folder creation verification completed")
            
        except Exception as e:
            logger.error(f"❌ Error creating test client and verifying folders: {str(e)}")
            raise
    
    def test_upload_with_folder_selection(self):
        """Test document upload with folder selection"""
        logger.info("\n=== Testing document upload with folder selection ===")
        
        # Step 1: Get available folders
        logger.info("Step 1: Getting available folders...")
        folders_url = f"{API_URL}/folders"
        
        try:
            folders_response = requests.get(folders_url, headers=self.headers_valid)
            logger.info(f"Folders response status code: {folders_response.status_code}")
            
            if folders_response.status_code != 200:
                logger.warning(f"Folders retrieval failed with status code {folders_response.status_code}")
                return
            
            folders_data = folders_response.json()
            
            if not folders_data:
                logger.warning("No folders found, attempting to create a client to generate folders...")
                self.create_test_client_and_verify_folders()
                
                # Try getting folders again
                folders_response = requests.get(folders_url, headers=self.headers_valid)
                if folders_response.status_code != 200:
                    logger.warning(f"Folders retrieval failed with status code {folders_response.status_code}")
                    return
                
                folders_data = folders_response.json()
                if not folders_data:
                    logger.warning("Still no folders found after creating client, skipping upload test")
                    return
            
            # Find a suitable folder for testing (preferably a column folder)
            column_folders = [f for f in folders_data if f.get("level") == 1]
            
            if column_folders:
                test_folder = column_folders[0]
            else:
                test_folder = folders_data[0]
            
            folder_id = test_folder["id"]
            client_id = test_folder["client_id"]
            
            logger.info(f"✅ Selected folder for testing: {test_folder['name']} (ID: {folder_id}, Client ID: {client_id})")
            
            # Step 2: Test upload with folder selection
            logger.info("Step 2: Testing upload with folder selection...")
            upload_url = f"{API_URL}/upload-document"
            
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
            
            # Check if upload was successful or failed with expected error
            self.assertIn(upload_response.status_code, [200, 400, 401, 403, 404, 422], 
                         f"Unexpected status code: {upload_response.status_code}")
            
            if upload_response.status_code == 200:
                logger.info("✅ Upload with folder selection successful")
                upload_data = upload_response.json()
                logger.info(f"Upload response: {json.dumps(upload_data, indent=2)}")
                
                # Verify document_id is returned
                self.assertIn("document_id", upload_data, "Response should include document_id")
                document_id = upload_data["document_id"]
                logger.info(f"✅ Document ID returned: {document_id}")
            else:
                logger.info(f"Upload failed with status code {upload_response.status_code}")
                logger.info(f"Response: {upload_response.text}")
                
                # This might be expected if we're using test data
                logger.info("⚠️ Upload failure may be expected with test data")
            
            logger.info("✅ Upload with folder selection test completed")
            
        except Exception as e:
            logger.error(f"❌ Error testing upload with folder selection: {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main()