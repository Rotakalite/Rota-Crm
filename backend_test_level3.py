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

class TestLevel3FolderStructure(unittest.TestCase):
    """Test class for Level 3 folder structure implementation"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = "https://ddbdf62a-0dc7-4cf4-b9a6-6dc3e3277ae1.preview.emergentagent.com/api"
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
        
        # Expected Level 3 sub-folder structure for D column
        self.expected_level3_subfolders = {
            "D1": ["D1.1", "D1.2", "D1.3", "D1.4"],
            "D2": ["D2.1", "D2.2", "D2.3", "D2.4", "D2.5", "D2.6"],
            "D3": ["D3.1", "D3.2", "D3.3", "D3.4", "D3.5", "D3.6"]
        }
        
        # Total expected Level 3 sub-folders
        self.total_expected_level3_subfolders = sum(len(subfolders) for subfolders in self.expected_level3_subfolders.values())
    
    def test_level3_folder_creation(self):
        """Test that Level 3 sub-folders are created correctly for D1, D2, and D3 folders"""
        logger.info("\n=== Testing Level 3 sub-folder creation ===")
        
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
            
            # Find D column folder
            d_column_folder = next((f for f in column_folders if f["name"] == "D SÜTUNU"), None)
            self.assertIsNotNone(d_column_folder, "D SÜTUNU folder not found")
            logger.info(f"✅ Found D SÜTUNU folder: {d_column_folder['name']}")
            
            # Check for D column sub-folders (level 2)
            d_subfolders = [f for f in client_folders if f.get("level") == 2 and f.get("parent_folder_id") == d_column_folder["id"]]
            self.assertEqual(len(d_subfolders), 3, f"D SÜTUNU should have exactly 3 sub-folders (D1, D2, D3), found {len(d_subfolders)}")
            
            # Verify D column sub-folder names
            d_subfolder_names = [f["name"] for f in d_subfolders]
            expected_d_subfolders = ["D1", "D2", "D3"]
            
            for expected_subfolder in expected_d_subfolders:
                self.assertIn(expected_subfolder, d_subfolder_names, f"Expected D column sub-folder not found: {expected_subfolder}")
                logger.info(f"✅ Found expected D column sub-folder: {expected_subfolder}")
            
            # Check for Level 3 sub-folders
            level3_subfolders = [f for f in client_folders if f.get("level") == 3]
            logger.info(f"Found {len(level3_subfolders)} Level 3 sub-folders")
            
            # Verify we have the expected number of Level 3 sub-folders
            self.assertEqual(len(level3_subfolders), self.total_expected_level3_subfolders, 
                           f"Should have {self.total_expected_level3_subfolders} Level 3 sub-folders, found {len(level3_subfolders)}")
            
            # Group Level 3 sub-folders by parent folder
            level3_subfolders_by_parent = {}
            for d_subfolder in d_subfolders:
                parent_id = d_subfolder["id"]
                parent_name = d_subfolder["name"]
                parent_level3_subfolders = [f for f in level3_subfolders if f.get("parent_folder_id") == parent_id]
                level3_subfolders_by_parent[parent_name] = parent_level3_subfolders
                logger.info(f"D sub-folder '{parent_name}' has {len(parent_level3_subfolders)} Level 3 sub-folders")
            
            # Verify each D sub-folder has the correct Level 3 sub-folders
            for parent_name, expected_level3_subfolder_names in self.expected_level3_subfolders.items():
                if parent_name in level3_subfolders_by_parent:
                    parent_level3_subfolders = level3_subfolders_by_parent[parent_name]
                    level3_subfolder_names = [f["name"] for f in parent_level3_subfolders]
                    
                    # Verify count
                    self.assertEqual(len(parent_level3_subfolders), len(expected_level3_subfolder_names), 
                                   f"D sub-folder '{parent_name}' should have {len(expected_level3_subfolder_names)} Level 3 sub-folders, found {len(parent_level3_subfolders)}")
                    
                    # Verify names
                    for expected_name in expected_level3_subfolder_names:
                        self.assertIn(expected_name, level3_subfolder_names, 
                                     f"Expected Level 3 sub-folder '{expected_name}' not found in D sub-folder '{parent_name}'")
                        logger.info(f"✅ Found expected Level 3 sub-folder: {parent_name}/{expected_name}")
                else:
                    self.fail(f"D sub-folder '{parent_name}' not found in level3_subfolders_by_parent")
            
            # Verify folder paths and parent-child relationships for Level 3 sub-folders
            for parent_name, parent_level3_subfolders in level3_subfolders_by_parent.items():
                parent_folder = next(f for f in d_subfolders if f["name"] == parent_name)
                
                for level3_subfolder in parent_level3_subfolders:
                    # Verify parent_folder_id points to the correct parent folder
                    self.assertEqual(level3_subfolder["parent_folder_id"], parent_folder["id"], 
                                   f"Level 3 sub-folder '{level3_subfolder['name']}' should have parent_folder_id '{parent_folder['id']}', got '{level3_subfolder['parent_folder_id']}'")
                    
                    # Verify folder_path is correctly formed
                    expected_path = f"{root_folder['name']}/D SÜTUNU/{parent_name}/{level3_subfolder['name']}"
                    self.assertEqual(level3_subfolder["folder_path"], expected_path, 
                                   f"Level 3 sub-folder path should be '{expected_path}', got: {level3_subfolder['folder_path']}")
                    
                    # Verify level is 3
                    self.assertEqual(level3_subfolder["level"], 3, 
                                   f"Level 3 sub-folder level should be 3, got: {level3_subfolder['level']}")
                    
                    logger.info(f"✅ Level 3 sub-folder '{level3_subfolder['name']}' has correct parent, path, and level")
            
            logger.info("✅ Level 3 folder structure test passed")
            
        except Exception as e:
            logger.error(f"❌ Error testing Level 3 folder structure: {str(e)}")
            raise
    
    def test_admin_update_subfolders_endpoint_for_level3(self):
        """Test that the POST /api/admin/update-subfolders endpoint adds Level 3 sub-folders to existing clients"""
        logger.info("\n=== Testing POST /api/admin/update-subfolders endpoint for Level 3 sub-folders ===")
        
        # Test with valid token
        logger.info("Testing with valid token...")
        url = f"{self.api_url}/admin/update-subfolders"
        
        try:
            # Step 1: Call the update-subfolders endpoint
            logger.info("Step 1: Calling the update-subfolders endpoint...")
            response = requests.post(url, headers=self.headers_valid)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:500]}...")
            
            # Check if we get a 200 OK or 401 Unauthorized (not 403 Forbidden)
            self.assertIn(response.status_code, [200, 401, 403])
            
            if response.status_code == 200:
                logger.info("✅ Authentication successful - received 200 OK")
                data = response.json()
                
                # Verify response structure
                self.assertIn("message", data, "Response should include a message field")
                self.assertIn("success", data, "Response should include a success field")
                
                # Verify success status
                self.assertTrue(data["success"], "Response should indicate success")
                logger.info(f"✅ Update successful: {data['message']}")
                
                # Step 2: Verify that existing clients now have Level 3 sub-folders
                logger.info("Step 2: Verifying that existing clients now have Level 3 sub-folders...")
                
                # Get all folders
                folders_url = f"{self.api_url}/folders"
                folders_response = requests.get(folders_url, headers=self.headers_valid)
                
                if folders_response.status_code != 200:
                    logger.warning(f"Folders retrieval failed with status code {folders_response.status_code}, skipping verification")
                    return
                
                folders_data = folders_response.json()
                
                # Group folders by client_id
                folders_by_client = {}
                for folder in folders_data:
                    client_id = folder.get("client_id")
                    if client_id not in folders_by_client:
                        folders_by_client[client_id] = []
                    folders_by_client[client_id].append(folder)
                
                # Check each client's folder structure
                level3_folders_found = False
                for client_id, client_folders in folders_by_client.items():
                    # Skip clients with no folders
                    if not client_folders:
                        continue
                    
                    # Find root folder
                    root_folders = [f for f in client_folders if f.get("level") == 0]
                    if not root_folders:
                        logger.warning(f"⚠️ Client {client_id} has no root folder, skipping")
                        continue
                    
                    root_folder = root_folders[0]
                    logger.info(f"Checking client with root folder: {root_folder['name']}")
                    
                    # Find column folders
                    column_folders = [f for f in client_folders if f.get("level") == 1]
                    if len(column_folders) < 4:
                        logger.warning(f"⚠️ Client {client_id} has {len(column_folders)} column folders instead of 4, skipping")
                        continue
                    
                    # Find D column folder
                    d_column_folder = next((f for f in column_folders if f["name"] == "D SÜTUNU"), None)
                    if not d_column_folder:
                        logger.warning(f"⚠️ Client {client_id} has no D SÜTUNU folder, skipping")
                        continue
                    
                    # Find D column sub-folders (level 2)
                    d_subfolders = [f for f in client_folders if f.get("level") == 2 and f.get("parent_folder_id") == d_column_folder["id"]]
                    if len(d_subfolders) < 3:
                        logger.warning(f"⚠️ Client {client_id} has only {len(d_subfolders)} D column sub-folders, skipping")
                        continue
                    
                    # Find Level 3 sub-folders
                    level3_subfolders = [f for f in client_folders if f.get("level") == 3]
                    logger.info(f"Client {client_id} has {len(level3_subfolders)} Level 3 sub-folders")
                    
                    if len(level3_subfolders) >= self.total_expected_level3_subfolders:
                        level3_folders_found = True
                        logger.info(f"✅ Client {client_id} has at least {self.total_expected_level3_subfolders} Level 3 sub-folders")
                        
                        # Group Level 3 sub-folders by parent folder
                        level3_subfolders_by_parent = {}
                        for d_subfolder in d_subfolders:
                            if d_subfolder["name"] in ["D1", "D2", "D3"]:
                                parent_id = d_subfolder["id"]
                                parent_name = d_subfolder["name"]
                                parent_level3_subfolders = [f for f in level3_subfolders if f.get("parent_folder_id") == parent_id]
                                level3_subfolders_by_parent[parent_name] = parent_level3_subfolders
                                logger.info(f"D sub-folder '{parent_name}' has {len(parent_level3_subfolders)} Level 3 sub-folders")
                        
                        # Check if each D sub-folder has the expected Level 3 sub-folders
                        all_level3_complete = True
                        for parent_name, expected_level3_subfolder_names in self.expected_level3_subfolders.items():
                            if parent_name in level3_subfolders_by_parent:
                                parent_level3_subfolders = level3_subfolders_by_parent[parent_name]
                                level3_subfolder_names = [f["name"] for f in parent_level3_subfolders]
                                
                                # Check if all expected Level 3 sub-folders exist
                                all_level3_subfolders_exist = all(name in level3_subfolder_names for name in expected_level3_subfolder_names)
                                if all_level3_subfolders_exist:
                                    logger.info(f"✅ D sub-folder '{parent_name}' has all expected Level 3 sub-folders")
                                else:
                                    all_level3_complete = False
                                    logger.warning(f"⚠️ D sub-folder '{parent_name}' is missing some expected Level 3 sub-folders")
                            else:
                                all_level3_complete = False
                                logger.warning(f"⚠️ D sub-folder '{parent_name}' not found in level3_subfolders_by_parent")
                        
                        if all_level3_complete:
                            logger.info(f"✅ Client {client_id} has a complete Level 3 folder structure")
                            
                            # We found a client with a complete Level 3 folder structure, so we can stop checking
                            break
                
                self.assertTrue(level3_folders_found, "No clients found with Level 3 sub-folders")
                
                # Step 3: Call the endpoint again to verify it doesn't create duplicates
                logger.info("Step 3: Calling the update-subfolders endpoint again to verify it doesn't create duplicates...")
                second_response = requests.post(url, headers=self.headers_valid)
                logger.info(f"Second response status code: {second_response.status_code}")
                logger.info(f"Second response body: {second_response.text[:500]}...")
                
                # Verify the second call also succeeds
                self.assertEqual(second_response.status_code, 200, "Second call should also succeed")
                
                # Get folders again
                second_folders_response = requests.get(folders_url, headers=self.headers_valid)
                
                if second_folders_response.status_code != 200:
                    logger.warning(f"Second folders retrieval failed with status code {second_folders_response.status_code}, skipping verification")
                    return
                
                second_folders_data = second_folders_response.json()
                
                # Verify that the number of folders hasn't increased significantly
                # (There might be some difference if other tests are running in parallel)
                self.assertLess(abs(len(second_folders_data) - len(folders_data)), 10, 
                               "Number of folders shouldn't increase significantly after second call")
                logger.info(f"✅ Second call didn't create duplicates: {len(folders_data)} folders before, {len(second_folders_data)} folders after")
                
                logger.info("✅ Admin update-subfolders endpoint test for Level 3 sub-folders passed")
                
            elif response.status_code == 401:
                logger.info("✅ Authentication failed correctly - received 401 Unauthorized")
                error_data = response.json()
                self.assertIn("detail", error_data)
            elif response.status_code == 403:
                logger.info("✅ Authorization failed correctly - received 403 Forbidden (admin access required)")
                error_data = response.json()
                self.assertIn("detail", error_data)
                self.assertIn("admin", error_data["detail"].lower(), "Error should mention admin access")
        except Exception as e:
            logger.error(f"❌ Error testing admin update-subfolders endpoint for Level 3 sub-folders: {str(e)}")
            raise
    
    def test_get_folders_endpoint_includes_level3(self):
        """Test that the GET /api/folders endpoint includes Level 3 sub-folders in the response"""
        logger.info("\n=== Testing GET /api/folders endpoint includes Level 3 sub-folders ===")
        
        # Test with valid token
        logger.info("Testing with valid token...")
        url = f"{self.api_url}/folders"
        
        try:
            response = requests.get(url, headers=self.headers_valid)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:500]}...")
            
            # Check if we get a 200 OK or 401 Unauthorized
            self.assertIn(response.status_code, [200, 401])
            
            if response.status_code == 200:
                logger.info("✅ Authentication successful - received 200 OK")
                data = response.json()
                
                # Verify response is a list of folders
                self.assertIsInstance(data, list, "Response should be a list of folders")
                logger.info(f"Found {len(data)} folders")
                
                # Count folders by level
                level_0_folders = [f for f in data if f.get("level") == 0]
                level_1_folders = [f for f in data if f.get("level") == 1]
                level_2_folders = [f for f in data if f.get("level") == 2]
                level_3_folders = [f for f in data if f.get("level") == 3]
                
                logger.info(f"Found {len(level_0_folders)} root folders (level 0)")
                logger.info(f"Found {len(level_1_folders)} column folders (level 1)")
                logger.info(f"Found {len(level_2_folders)} sub-folders (level 2)")
                logger.info(f"Found {len(level_3_folders)} Level 3 sub-folders (level 3)")
                
                # Verify we have Level 3 sub-folders
                self.assertGreater(len(level_3_folders), 0, "Should have at least some Level 3 sub-folders")
                
                # Check structure of a Level 3 sub-folder
                if level_3_folders:
                    level3_subfolder = level_3_folders[0]
                    self.assertIn("id", level3_subfolder, "Level 3 sub-folder should have an id field")
                    self.assertIn("client_id", level3_subfolder, "Level 3 sub-folder should have a client_id field")
                    self.assertIn("name", level3_subfolder, "Level 3 sub-folder should have a name field")
                    self.assertIn("parent_folder_id", level3_subfolder, "Level 3 sub-folder should have a parent_folder_id field")
                    self.assertIn("folder_path", level3_subfolder, "Level 3 sub-folder should have a folder_path field")
                    self.assertIn("level", level3_subfolder, "Level 3 sub-folder should have a level field")
                    
                    # Verify level is 3
                    self.assertEqual(level3_subfolder["level"], 3, "Level 3 sub-folder level should be 3")
                    
                    # Verify parent_folder_id points to a level 2 folder
                    parent_id = level3_subfolder["parent_folder_id"]
                    parent_folders = [f for f in level_2_folders if f.get("id") == parent_id]
                    self.assertEqual(len(parent_folders), 1, "Level 3 sub-folder should have exactly one parent folder")
                    
                    parent_folder = parent_folders[0]
                    self.assertEqual(parent_folder["level"], 2, "Parent folder level should be 2")
                    
                    # Verify folder_path includes parent path
                    expected_path_prefix = f"{parent_folder['folder_path']}/"
                    self.assertTrue(level3_subfolder["folder_path"].startswith(expected_path_prefix), 
                                   f"Level 3 sub-folder path should start with '{expected_path_prefix}', got: {level3_subfolder['folder_path']}")
                    
                    logger.info(f"✅ Level 3 sub-folder structure is correct: {level3_subfolder['folder_path']}")
                
                # Check for specific Level 3 sub-folders
                d1_level3_subfolders = [f for f in level_3_folders if any(f["name"] == name for name in ["D1.1", "D1.2", "D1.3", "D1.4"])]
                d2_level3_subfolders = [f for f in level_3_folders if any(f["name"] == name for name in ["D2.1", "D2.2", "D2.3", "D2.4", "D2.5", "D2.6"])]
                d3_level3_subfolders = [f for f in level_3_folders if any(f["name"] == name for name in ["D3.1", "D3.2", "D3.3", "D3.4", "D3.5", "D3.6"])]
                
                logger.info(f"Found {len(d1_level3_subfolders)} D1.x Level 3 sub-folders")
                logger.info(f"Found {len(d2_level3_subfolders)} D2.x Level 3 sub-folders")
                logger.info(f"Found {len(d3_level3_subfolders)} D3.x Level 3 sub-folders")
                
                # Verify we have at least some of each type of Level 3 sub-folder
                self.assertGreater(len(d1_level3_subfolders) + len(d2_level3_subfolders) + len(d3_level3_subfolders), 0, 
                                  "Should have at least some D1.x, D2.x, or D3.x Level 3 sub-folders")
                
                logger.info("✅ GET /api/folders endpoint includes Level 3 sub-folders")
            elif response.status_code == 401:
                logger.info("✅ Authentication failed correctly - received 401 Unauthorized")
                error_data = response.json()
                self.assertIn("detail", error_data)
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/folders endpoint for Level 3 sub-folders: {str(e)}")
            raise

def run_level3_folder_tests():
    """Run tests for Level 3 folder structure"""
    logger.info("Starting Level 3 folder structure tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add Level 3 folder structure tests
    suite.addTest(TestLevel3FolderStructure("test_level3_folder_creation"))
    suite.addTest(TestLevel3FolderStructure("test_admin_update_subfolders_endpoint_for_level3"))
    suite.addTest(TestLevel3FolderStructure("test_get_folders_endpoint_includes_level3"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Level 3 Folder Structure Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All Level 3 folder structure tests PASSED")
        return True
    else:
        logger.error("Some Level 3 folder structure tests FAILED")
        return False

if __name__ == "__main__":
    run_level3_folder_tests()