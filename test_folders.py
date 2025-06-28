import unittest
import requests
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend/.env
BACKEND_URL = "https://a8c99106-2f85-4c4d-bdad-22c18652c48e.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class TestFoldersEndpoint(unittest.TestCase):
    """Test class for the folders endpoint"""
    
    def test_folders_endpoint(self):
        """Test the GET /api/folders endpoint directly"""
        logger.info("\n=== Testing GET /api/folders endpoint directly ===")
        
        # Make a direct request to the folders endpoint
        url = f"{API_URL}/folders"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if we get a response (even if it's an authentication error)
            self.assertIn(response.status_code, [200, 401, 403], 
                         f"Expected status code 200, 401, or 403, got {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Folders endpoint accessible without authentication")
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
            else:
                logger.info(f"Folders endpoint requires authentication (status code: {response.status_code})")
                error_data = response.json()
                logger.info(f"Error message: {error_data.get('detail', 'No detail provided')}")
                
            logger.info("✅ Folders endpoint test completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error testing folders endpoint: {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main()