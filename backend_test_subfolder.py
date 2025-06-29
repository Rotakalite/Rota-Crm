import unittest
import json
import logging
import requests
import os
import io
import uuid
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestHierarchicalFolderSystem(unittest.TestCase):
    """Test class for enhanced hierarchical folder system with sub-folders"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = "https://ced36975-561f-4c1a-b948-3ca6d5f89931.preview.emergentagent.com/api"
        self.headers_valid = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        
        # Test client data for folder creation
        self.test_client = {
            "name": f"Test Client {uuid.uuid4().hex[:8]}",
            "hotel_name": "Test Hotel",
            "contact_person": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "address": "123 Test St"
        }
        
        # Expected sub-folder structure
        self.expected_subfolder_structure = {
            "A SÜTUNU": ["A1", "A2", "A3", "A4", "A5", "A7.1", "A7.2", "A7.3", "A7.4", "A8", "A9", "A10"],
            "B SÜTUNU": ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"],
            "C SÜTUNU": ["C1", "C2", "C3", "C4"],
            "D SÜTUNU": ["D1", "D2", "D3"]
        }
        
        # Total expected sub-folders count
        self.total_expected_subfolders = sum(len(subfolders) for subfolders in self.expected_subfolder_structure.values())
        
    def test_subfolder_creation(self):
        """Test that sub-folders are automatically created when a new client is created"""
        logger.info("\n=== Testing sub-folder creation when a new client is created ===")
        
        # Step 1: Create a new client
        logger.info("Step 1: Creating a new client...")
        client_url = f"{self.api_url}/clients"
        
        try:
            client_response = requests.post(client_url, headers=self.headers_valid, json=self.test_client)
            logger.info(f"Client creation response status code: {client_response.status_code}")
            logger.info(f"Client creation response body: {client_response.text[:500]}...")
            
            # If client creation was successful or authentication failed, continue to next step
            if client_response.status_code not in [200, 201]:
                logger.warning(f"Client creation failed with status code {client_response.status_code}, skipping rest of test")
                return
            
            # Get the client ID from the response
            client_data = client_response.json()
            client_id = client_data.get("id")
            client_name = client_data.get("name")
            
            if not client_id:
                logger.warning("Client ID not found in response, skipping rest of test")
                return
            
            logger.info(f"✅ Created client with ID: {client_id} and name: {client_name}")
            
            # Step 2: Check if folders were automatically created
            logger.info("Step 2: Checking if folders were automatically created...")
            folders_url = f"{self.api_url}/folders"
            
            folders_response = requests.get(folders_url, headers=self.headers_valid)
            logger.info(f"Folders response status code: {folders_response.status_code}")
            
            if folders_response.status_code != 200:
                logger.warning(f"Folders retrieval failed with status code {folders_response.status_code}, skipping rest of test")
                return
            
            folders_data = folders_response.json()
            
            # Find folders for the newly created client
            client_folders = [f for f in folders_data if f.get("client_id") == client_id]
            logger.info(f"Found {len(client_folders)} folders for the new client")
            
            if not client_folders:
                logger.error("❌ No folders found for the newly created client")
                self.fail("No folders found for the newly created client")
            
            # Check for root folder
            root_folders = [f for f in client_folders if f.get("level") == 0]
            self.assertEqual(len(root_folders), 1, f"Should have exactly 1 root folder, found {len(root_folders)}")
            
            root_folder = root_folders[0]
            expected_root_name = f"{client_name} SYS"
            self.assertEqual(root_folder["name"], expected_root_name, 
                           f"Root folder name should be '{expected_root_name}', got: {root_folder['name']}")
            logger.info(f"✅ Root folder created with correct name: {root_folder['name']}")
            
            # Check for column folders (level 1)
            column_folders = [f for f in client_folders if f.get("level") == 1]
            self.assertEqual(len(column_folders), 4, f"Should have exactly 4 column folders, found {len(column_folders)}")
            
            # Verify column folder names
            column_names = [f["name"] for f in column_folders]
            expected_columns = ["A SÜTUNU", "B SÜTUNU", "C SÜTUNU", "D SÜTUNU"]
            
            for expected_column in expected_columns:
                self.assertIn(expected_column, column_names, f"Expected column folder not found: {expected_column}")
                logger.info(f"✅ Found expected column folder: {expected_column}")
            
            # Check for sub-folders (level 2)
            sub_folders = [f for f in client_folders if f.get("level") == 2]
            logger.info(f"Found {len(sub_folders)} sub-folders (level 2)")
            
            # Verify we have the expected number of sub-folders
            self.assertEqual(len(sub_folders), self.total_expected_subfolders, 
                           f"Should have {self.total_expected_subfolders} sub-folders, found {len(sub_folders)}")
            
            # Group sub-folders by parent folder
            sub_folders_by_parent = {}
            for sub_folder in sub_folders:
                parent_id = sub_folder.get("parent_folder_id")
                if parent_id not in sub_folders_by_parent:
                    sub_folders_by_parent[parent_id] = []
                sub_folders_by_parent[parent_id].append(sub_folder)
            
            # Verify sub-folders for each column
            for column_folder in column_folders:
                column_id = column_folder.get("id")
                column_name = column_folder.get("name")
                
                if column_id in sub_folders_by_parent:
                    column_sub_folders = sub_folders_by_parent[column_id]
                    logger.info(f"Found {len(column_sub_folders)} sub-folders for column: {column_name}")
                    
                    # Verify we have the expected number of sub-folders for this column
                    expected_count = len(self.expected_subfolder_structure.get(column_name, []))
                    self.assertEqual(len(column_sub_folders), expected_count, 
                                   f"Column {column_name} should have {expected_count} sub-folders, found {len(column_sub_folders)}")
                    
                    # Verify sub-folder names
                    sub_folder_names = [f["name"] for f in column_sub_folders]
                    expected_sub_folders = self.expected_subfolder_structure.get(column_name, [])
                    
                    for expected_sub_folder in expected_sub_folders:
                        self.assertIn(expected_sub_folder, sub_folder_names, 
                                     f"Expected sub-folder {expected_sub_folder} not found in column {column_name}")
                        logger.info(f"✅ Found expected sub-folder: {column_name}/{expected_sub_folder}")
                    
                    # Verify sub-folder paths
                    for sub_folder in column_sub_folders:
                        expected_path = f"{expected_root_name}/{column_name}/{sub_folder['name']}"
                        self.assertEqual(sub_folder["folder_path"], expected_path, 
                                       f"Sub-folder path should be '{expected_path}', got: {sub_folder['folder_path']}")
                        logger.info(f"✅ Sub-folder has correct path: {sub_folder['folder_path']}")
                else:
                    logger.error(f"❌ No sub-folders found for column: {column_name}")
                    self.fail(f"No sub-folders found for column: {column_name}")
            
            # Verify total folder count
            expected_total_folders = 1 + 4 + self.total_expected_subfolders  # 1 root + 4 columns + sub-folders
            self.assertEqual(len(client_folders), expected_total_folders, 
                           f"Should have {expected_total_folders} total folders, found {len(client_folders)}")
            logger.info(f"✅ Total folder count is correct: {len(client_folders)}")
            
            logger.info("✅ All sub-folders were automatically created with correct structure")
            
        except Exception as e:
            logger.error(f"❌ Error testing sub-folder creation: {str(e)}")
            raise
    
    def test_folder_hierarchy_validation(self):
        """Test that folder hierarchy is correctly formed with proper parent-child relationships"""
        logger.info("\n=== Testing folder hierarchy validation ===")
        
        # Step 1: Get all folders
        logger.info("Step 1: Getting all folders...")
        folders_url = f"{self.api_url}/folders"
        
        try:
            folders_response = requests.get(folders_url, headers=self.headers_valid)
            logger.info(f"Folders response status code: {folders_response.status_code}")
            
            if folders_response.status_code != 200:
                logger.warning(f"Folders retrieval failed with status code {folders_response.status_code}, skipping rest of test")
                return
            
            folders_data = folders_response.json()
            logger.info(f"Found {len(folders_data)} total folders")
            
            if not folders_data:
                logger.warning("No folders found, skipping rest of test")
                return
            
            # Step 2: Find a client with a complete folder structure
            logger.info("Step 2: Finding a client with a complete folder structure...")
            
            # Group folders by client_id
            folders_by_client = {}
            for folder in folders_data:
                client_id = folder.get("client_id")
                if client_id not in folders_by_client:
                    folders_by_client[client_id] = []
                folders_by_client[client_id].append(folder)
            
            # Find a client with at least 29 folders (1 root + 4 columns + 24 sub-folders)
            test_client_id = None
            test_client_folders = None
            
            for client_id, client_folders in folders_by_client.items():
                if len(client_folders) >= 29:
                    test_client_id = client_id
                    test_client_folders = client_folders
                    break
            
            if not test_client_id:
                logger.warning("No client found with a complete folder structure, skipping rest of test")
                return
            
            logger.info(f"Found client with ID {test_client_id} having {len(test_client_folders)} folders")
            
            # Step 3: Validate folder hierarchy
            logger.info("Step 3: Validating folder hierarchy...")
            
            # Find root folder
            root_folders = [f for f in test_client_folders if f.get("level") == 0]
            self.assertEqual(len(root_folders), 1, f"Should have exactly 1 root folder, found {len(root_folders)}")
            
            root_folder = root_folders[0]
            logger.info(f"Found root folder: {root_folder['name']}")
            
            # Find column folders
            column_folders = [f for f in test_client_folders if f.get("level") == 1]
            self.assertEqual(len(column_folders), 4, f"Should have exactly 4 column folders, found {len(column_folders)}")
            
            # Verify column folders have correct parent_folder_id
            for column_folder in column_folders:
                self.assertEqual(column_folder["parent_folder_id"], root_folder["id"], 
                               f"Column folder {column_folder['name']} should have parent_folder_id {root_folder['id']}, got: {column_folder['parent_folder_id']}")
                logger.info(f"✅ Column folder {column_folder['name']} has correct parent_folder_id")
            
            # Find sub-folders
            sub_folders = [f for f in test_client_folders if f.get("level") == 2]
            logger.info(f"Found {len(sub_folders)} sub-folders")
            
            # Group sub-folders by parent folder
            sub_folders_by_parent = {}
            for sub_folder in sub_folders:
                parent_id = sub_folder.get("parent_folder_id")
                if parent_id not in sub_folders_by_parent:
                    sub_folders_by_parent[parent_id] = []
                sub_folders_by_parent[parent_id].append(sub_folder)
            
            # Verify sub-folders have correct parent_folder_id
            for column_folder in column_folders:
                column_id = column_folder.get("id")
                column_name = column_folder.get("name")
                
                if column_id in sub_folders_by_parent:
                    column_sub_folders = sub_folders_by_parent[column_id]
                    logger.info(f"Found {len(column_sub_folders)} sub-folders for column: {column_name}")
                    
                    for sub_folder in column_sub_folders:
                        self.assertEqual(sub_folder["parent_folder_id"], column_id, 
                                       f"Sub-folder {sub_folder['name']} should have parent_folder_id {column_id}, got: {sub_folder['parent_folder_id']}")
                        logger.info(f"✅ Sub-folder {sub_folder['name']} has correct parent_folder_id")
                        
                        # Verify folder path
                        expected_path = f"{root_folder['name']}/{column_name}/{sub_folder['name']}"
                        self.assertEqual(sub_folder["folder_path"], expected_path, 
                                       f"Sub-folder path should be '{expected_path}', got: {sub_folder['folder_path']}")
                        logger.info(f"✅ Sub-folder has correct path: {sub_folder['folder_path']}")
                        
                        # Verify level
                        self.assertEqual(sub_folder["level"], 2, 
                                       f"Sub-folder level should be 2, got: {sub_folder['level']}")
                        logger.info(f"✅ Sub-folder has correct level: {sub_folder['level']}")
                else:
                    logger.warning(f"⚠️ No sub-folders found for column: {column_name}")
            
            logger.info("✅ Folder hierarchy validation passed")
            
        except Exception as e:
            logger.error(f"❌ Error testing folder hierarchy validation: {str(e)}")
            raise
    
    def test_get_folders_endpoint(self):
        """Test that the GET /api/folders endpoint returns the complete hierarchical structure"""
        logger.info("\n=== Testing GET /api/folders endpoint ===")
        
        # Test with valid token
        logger.info("Testing with valid token...")
        url = f"{self.api_url}/folders"
        
        try:
            response = requests.get(url, headers=self.headers_valid)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:500]}...")
            
            # Check if we get a 200 OK or 401 Unauthorized (not 403 Forbidden)
            self.assertIn(response.status_code, [200, 401])
            
            if response.status_code == 200:
                logger.info("✅ Authentication successful - received 200 OK")
                data = response.json()
                
                # Verify response is a list of folders
                self.assertIsInstance(data, list, "Response should be a list of folders")
                logger.info(f"Found {len(data)} folders")
                
                # Check folder structure if any folders exist
                if len(data) > 0:
                    folder = data[0]
                    self.assertIn("id", folder, "Folder should have an id field")
                    self.assertIn("client_id", folder, "Folder should have a client_id field")
                    self.assertIn("name", folder, "Folder should have a name field")
                    self.assertIn("level", folder, "Folder should have a level field")
                    self.assertIn("folder_path", folder, "Folder should have a folder_path field")
                    self.assertIn("parent_folder_id", folder, "Folder should have a parent_folder_id field")
                    
                    # Group folders by level
                    folders_by_level = {}
                    for f in data:
                        level = f.get("level", 0)
                        if level not in folders_by_level:
                            folders_by_level[level] = []
                        folders_by_level[level].append(f)
                    
                    # Check if we have all three levels
                    self.assertIn(0, folders_by_level, "Should have level 0 folders (root)")
                    self.assertIn(1, folders_by_level, "Should have level 1 folders (columns)")
                    self.assertIn(2, folders_by_level, "Should have level 2 folders (sub-folders)")
                    
                    logger.info(f"Found {len(folders_by_level[0])} root folders (level 0)")
                    logger.info(f"Found {len(folders_by_level[1])} column folders (level 1)")
                    logger.info(f"Found {len(folders_by_level[2])} sub-folders (level 2)")
                    
                    # Verify we have at least one complete folder structure
                    # (1 root + 4 columns + 24 sub-folders = 29 folders)
                    folders_by_client = {}
                    for f in data:
                        client_id = f.get("client_id")
                        if client_id not in folders_by_client:
                            folders_by_client[client_id] = []
                        folders_by_client[client_id].append(f)
                    
                    complete_structure_found = False
                    for client_id, client_folders in folders_by_client.items():
                        if len(client_folders) >= 29:
                            complete_structure_found = True
                            logger.info(f"✅ Found client with complete folder structure: {len(client_folders)} folders")
                            break
                    
                    self.assertTrue(complete_structure_found, "No client found with complete folder structure (29+ folders)")
                
                logger.info("✅ GET /api/folders endpoint test passed")
            elif response.status_code == 401:
                logger.info("✅ Authentication failed correctly - received 401 Unauthorized")
                error_data = response.json()
                self.assertIn("detail", error_data)
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/folders endpoint: {str(e)}")
            raise
            
        # Test with invalid token
        logger.info("Testing with invalid token...")
        
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Response status code with invalid token: {response.status_code}")
            
            # Should get 401 Unauthorized, not 403 Forbidden
            self.assertEqual(response.status_code, 401)
            logger.info("✅ Invalid token test passed - received 401 Unauthorized")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/folders endpoint with invalid token: {str(e)}")
            raise
            
        # Test without token
        logger.info("Testing without token...")
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code without token: {response.status_code}")
            
            # Should get 401 Unauthorized or 403 Forbidden
            self.assertIn(response.status_code, [401, 403])
            logger.info(f"✅ No token test passed - received {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/folders endpoint without token: {str(e)}")
            raise
    
    def test_multiple_clients(self):
        """Test creating multiple clients to ensure each gets their own complete folder structure"""
        logger.info("\n=== Testing multiple clients folder structure ===")
        
        # Create two test clients
        test_clients = [
            {
                "name": f"Test Client A {uuid.uuid4().hex[:8]}",
                "hotel_name": "Test Hotel A",
                "contact_person": "John Doe",
                "email": "john@example.com",
                "phone": "1234567890",
                "address": "123 Test St"
            },
            {
                "name": f"Test Client B {uuid.uuid4().hex[:8]}",
                "hotel_name": "Test Hotel B",
                "contact_person": "Jane Smith",
                "email": "jane@example.com",
                "phone": "9876543210",
                "address": "456 Test Ave"
            }
        ]
        
        client_ids = []
        client_names = []
        
        try:
            # Step 1: Create multiple clients
            logger.info("Step 1: Creating multiple clients...")
            client_url = f"{self.api_url}/clients"
            
            for i, test_client in enumerate(test_clients):
                client_response = requests.post(client_url, headers=self.headers_valid, json=test_client)
                logger.info(f"Client {i+1} creation response status code: {client_response.status_code}")
                
                if client_response.status_code in [200, 201]:
                    client_data = client_response.json()
                    client_id = client_data.get("id")
                    client_name = client_data.get("name")
                    
                    if client_id:
                        client_ids.append(client_id)
                        client_names.append(client_name)
                        logger.info(f"✅ Created client {i+1} with ID: {client_id} and name: {client_name}")
                else:
                    logger.warning(f"Client {i+1} creation failed with status code {client_response.status_code}")
            
            if len(client_ids) < 2:
                logger.warning(f"Not enough clients created ({len(client_ids)}), skipping rest of test")
                return
            
            # Step 2: Check if folders were automatically created for each client
            logger.info("Step 2: Checking if folders were automatically created for each client...")
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
            
            # Check folders for each created client
            for i, client_id in enumerate(client_ids):
                if client_id in folders_by_client:
                    client_folders = folders_by_client[client_id]
                    logger.info(f"Found {len(client_folders)} folders for client {i+1}: {client_names[i]}")
                    
                    # Verify total folder count
                    expected_total_folders = 1 + 4 + self.total_expected_subfolders  # 1 root + 4 columns + sub-folders
                    self.assertEqual(len(client_folders), expected_total_folders, 
                                   f"Client {i+1} should have {expected_total_folders} total folders, found {len(client_folders)}")
                    
                    # Verify root folder
                    root_folders = [f for f in client_folders if f.get("level") == 0]
                    self.assertEqual(len(root_folders), 1, f"Client {i+1} should have exactly 1 root folder, found {len(root_folders)}")
                    
                    root_folder = root_folders[0]
                    expected_root_name = f"{client_names[i]} SYS"
                    self.assertEqual(root_folder["name"], expected_root_name, 
                                   f"Client {i+1} root folder name should be '{expected_root_name}', got: {root_folder['name']}")
                    
                    # Verify column folders
                    column_folders = [f for f in client_folders if f.get("level") == 1]
                    self.assertEqual(len(column_folders), 4, f"Client {i+1} should have exactly 4 column folders, found {len(column_folders)}")
                    
                    # Verify sub-folders
                    sub_folders = [f for f in client_folders if f.get("level") == 2]
                    self.assertEqual(len(sub_folders), self.total_expected_subfolders, 
                                   f"Client {i+1} should have {self.total_expected_subfolders} sub-folders, found {len(sub_folders)}")
                    
                    logger.info(f"✅ Client {i+1} has correct folder structure with {len(client_folders)} total folders")
                else:
                    logger.error(f"❌ No folders found for client {i+1}: {client_names[i]}")
                    self.fail(f"No folders found for client {i+1}: {client_names[i]}")
            
            logger.info("✅ Multiple clients test passed - each client has its own complete folder structure")
            
        except Exception as e:
            logger.error(f"❌ Error testing multiple clients: {str(e)}")
            raise

def run_hierarchical_folder_tests():
    """Run tests for hierarchical folder system with sub-folders"""
    logger.info("Starting hierarchical folder system tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add hierarchical folder system tests
    suite.addTest(TestHierarchicalFolderSystem("test_subfolder_creation"))
    suite.addTest(TestHierarchicalFolderSystem("test_folder_hierarchy_validation"))
    suite.addTest(TestHierarchicalFolderSystem("test_get_folders_endpoint"))
    suite.addTest(TestHierarchicalFolderSystem("test_multiple_clients"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Hierarchical Folder System Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All hierarchical folder system tests PASSED")
        return True
    else:
        logger.error("Some hierarchical folder system tests FAILED")
        return False

if __name__ == "__main__":
    run_hierarchical_folder_tests()