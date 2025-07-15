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
RAILWAY_API_URL = "https://7397d81a-245d-49b9-a61b-31977569672c.preview.emergentagent.com/api"

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "rotacrm"

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestLevel4FolderStructure(unittest.TestCase):
    """Test class for Level 4 folder structure implementation"""
    
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
    
    def test_create_level4_structure(self):
        """Test POST /api/folders/create-level4-structure endpoint"""
        logger.info("\n=== Testing POST /api/folders/create-level4-structure endpoint ===")
        
        url = f"{self.api_url}/folders/create-level4-structure"
        
        # Test with admin authentication
        try:
            response = requests.post(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK or 201 Created
            self.assertIn(response.status_code, [200, 201])
            
            # Response should contain success message and counts
            data = response.json()
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("message", data)
            self.assertIn("level4_structure", data)
            self.assertIn("parent_folders_processed", data)
            
            # Verify the level4_structure contains the correct folder names
            expected_level4_folders = ["POLİTİKALAR", "PROSEDÜRLER", "FORMLAR", "LİSTELER", "KAYITLAR"]
            self.assertEqual(data["level4_structure"], expected_level4_folders)
            
            # Log the number of parent folders processed and folders created
            parent_folders_processed = data["parent_folders_processed"]
            created_count = int(data["message"].split("created ")[1].split(" Level")[0])
            logger.info(f"Parent folders processed: {parent_folders_processed}")
            logger.info(f"Level 4 folders created: {created_count}")
            
            # Verify that a reasonable number of folders were created
            # Note: The exact number may vary depending on the database state
            self.assertGreaterEqual(created_count, 1, "At least one Level 4 folder should be created")
            
            logger.info("✅ POST /api/folders/create-level4-structure with admin auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing create level4 structure endpoint: {str(e)}")
            raise
    
    def test_verify_level4_folders_in_database(self):
        """Verify Level 4 folders in the database"""
        logger.info("\n=== Verifying Level 4 folders in database ===")
        
        try:
            # Get all Level 4 folders from the database
            level4_folders = list(self.db.folders.find({"level": 4}))
            logger.info(f"Found {len(level4_folders)} Level 4 folders in database")
            
            # Verify that there are Level 4 folders
            self.assertGreater(len(level4_folders), 0, "There should be Level 4 folders in the database")
            
            # Get all Level 2 and Level 3 folders (parent folders)
            parent_folders = list(self.db.folders.find({"level": {"$in": [2, 3]}}))
            logger.info(f"Found {len(parent_folders)} Level 2 and Level 3 folders in database")
            
            # Verify that there are parent folders
            self.assertGreater(len(parent_folders), 0, "There should be Level 2 and Level 3 folders in the database")
            
            # Check that each parent folder has 5 Level 4 subfolders
            parent_folder_ids = [folder["id"] for folder in parent_folders]
            
            # Count Level 4 folders by parent_folder_id
            parent_folder_counts = {}
            for folder in level4_folders:
                parent_id = folder.get("parent_folder_id")
                if parent_id in parent_folder_ids:
                    parent_folder_counts[parent_id] = parent_folder_counts.get(parent_id, 0) + 1
            
            # Log the counts for a sample of parent folders
            sample_size = min(5, len(parent_folder_counts))
            sample_parents = list(parent_folder_counts.items())[:sample_size]
            for parent_id, count in sample_parents:
                logger.info(f"Parent folder {parent_id} has {count} Level 4 subfolders")
            
            # Verify that at least some parent folders have 5 Level 4 subfolders
            folders_with_5_subfolders = [parent_id for parent_id, count in parent_folder_counts.items() if count == 5]
            logger.info(f"Found {len(folders_with_5_subfolders)} parent folders with exactly 5 Level 4 subfolders")
            
            # There should be at least one parent folder with 5 Level 4 subfolders
            self.assertGreater(len(folders_with_5_subfolders), 0, "At least one parent folder should have 5 Level 4 subfolders")
            
            # Check the names of Level 4 folders
            level4_folder_names = set([folder["name"] for folder in level4_folders])
            expected_names = {"POLİTİKALAR", "PROSEDÜRLER", "FORMLAR", "LİSTELER", "KAYITLAR"}
            
            logger.info(f"Level 4 folder names found: {level4_folder_names}")
            
            # Verify that all expected names are present
            self.assertTrue(expected_names.issubset(level4_folder_names), 
                           f"All expected Level 4 folder names should be present. Missing: {expected_names - level4_folder_names}")
            
            logger.info("✅ Level 4 folders verification in database passed")
        except Exception as e:
            logger.error(f"❌ Error verifying Level 4 folders in database: {str(e)}")
            raise
    
    def test_get_folders_endpoint(self):
        """Test GET /api/folders endpoint to verify Level 4 folders are returned"""
        logger.info("\n=== Testing GET /api/folders endpoint for Level 4 folders ===")
        
        url = f"{self.api_url}/folders"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list of folders
            data = response.json()
            self.assertIsInstance(data, list)
            
            # Filter Level 4 folders
            level4_folders = [folder for folder in data if folder.get("level") == 4]
            logger.info(f"Found {len(level4_folders)} Level 4 folders in API response")
            
            # Verify that there are Level 4 folders
            self.assertGreater(len(level4_folders), 0, "There should be Level 4 folders in the API response")
            
            # Check the names of Level 4 folders
            level4_folder_names = set([folder["name"] for folder in level4_folders])
            expected_names = {"POLİTİKALAR", "PROSEDÜRLER", "FORMLAR", "LİSTELER", "KAYITLAR"}
            
            logger.info(f"Level 4 folder names found in API response: {level4_folder_names}")
            
            # Verify that all expected names are present
            self.assertTrue(expected_names.issubset(level4_folder_names), 
                           f"All expected Level 4 folder names should be present in API response. Missing: {expected_names - level4_folder_names}")
            
            # Verify folder hierarchy (parent-child relationships)
            # Sample a few Level 4 folders and check their parent_folder_id
            sample_size = min(5, len(level4_folders))
            sample_folders = level4_folders[:sample_size]
            
            for folder in sample_folders:
                parent_id = folder.get("parent_folder_id")
                self.assertIsNotNone(parent_id, "Level 4 folder should have a parent_folder_id")
                
                # Find the parent folder in the data
                parent_folder = next((f for f in data if f.get("id") == parent_id), None)
                self.assertIsNotNone(parent_folder, f"Parent folder with ID {parent_id} should exist")
                
                # Verify parent folder level is 2 or 3
                parent_level = parent_folder.get("level")
                self.assertIn(parent_level, [2, 3], f"Parent folder level should be 2 or 3, got {parent_level}")
                
                logger.info(f"Level 4 folder '{folder['name']}' has parent '{parent_folder['name']}' (level {parent_level})")
            
            logger.info("✅ GET /api/folders endpoint test for Level 4 folders passed")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/folders endpoint for Level 4 folders: {str(e)}")
            raise
    
    def test_folder_hierarchy(self):
        """Test the complete folder hierarchy from Level 0 to Level 4"""
        logger.info("\n=== Testing complete folder hierarchy from Level 0 to Level 4 ===")
        
        url = f"{self.api_url}/folders"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list of folders
            data = response.json()
            self.assertIsInstance(data, list)
            
            # Group folders by level
            folders_by_level = {}
            for folder in data:
                level = folder.get("level")
                if level is not None:
                    if level not in folders_by_level:
                        folders_by_level[level] = []
                    folders_by_level[level].append(folder)
            
            # Log the number of folders at each level
            for level, folders in sorted(folders_by_level.items()):
                logger.info(f"Level {level}: {len(folders)} folders")
            
            # Verify that all levels from 0 to 4 exist
            for level in range(5):
                self.assertIn(level, folders_by_level, f"Level {level} folders should exist")
                self.assertGreater(len(folders_by_level[level]), 0, f"There should be at least one Level {level} folder")
            
            # Sample a Level 4 folder and trace its hierarchy up to Level 0
            if 4 in folders_by_level and len(folders_by_level[4]) > 0:
                level4_folder = folders_by_level[4][0]
                logger.info(f"\nTracing hierarchy for Level 4 folder: {level4_folder['name']} (ID: {level4_folder['id']})")
                
                current_folder = level4_folder
                hierarchy = [current_folder]
                
                # Trace up to Level 0
                while current_folder.get("parent_folder_id"):
                    parent_id = current_folder.get("parent_folder_id")
                    parent_folder = next((f for f in data if f.get("id") == parent_id), None)
                    
                    if parent_folder:
                        hierarchy.append(parent_folder)
                        current_folder = parent_folder
                    else:
                        break
                
                # Log the hierarchy
                hierarchy.reverse()  # Start from Level 0
                for folder in hierarchy:
                    logger.info(f"Level {folder.get('level')}: {folder.get('name')} (ID: {folder.get('id')})")
                
                # Verify the hierarchy has 5 levels (0, 1, 2, 3, 4)
                self.assertEqual(len(hierarchy), 5, "Folder hierarchy should have 5 levels (0, 1, 2, 3, 4)")
                
                # Verify the levels are in the correct order
                for i, folder in enumerate(hierarchy):
                    self.assertEqual(folder.get("level"), i, f"Folder at position {i} should have level {i}")
            
            logger.info("✅ Complete folder hierarchy test passed")
        except Exception as e:
            logger.error(f"❌ Error testing complete folder hierarchy: {str(e)}")
            raise

def run_level4_folder_tests():
    """Run all Level 4 folder structure tests"""
    suite = unittest.TestSuite()
    
    # Add Level 4 folder structure tests
    suite.addTest(TestLevel4FolderStructure("test_create_level4_structure"))
    suite.addTest(TestLevel4FolderStructure("test_verify_level4_folders_in_database"))
    suite.addTest(TestLevel4FolderStructure("test_get_folders_endpoint"))
    suite.addTest(TestLevel4FolderStructure("test_folder_hierarchy"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Print summary
    logger.info("\n=== Level 4 Folder Structure Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All Level 4 folder structure tests PASSED")
        return True
    else:
        logger.error("Some Level 4 folder structure tests FAILED")
        return False

if __name__ == "__main__":
    run_level4_folder_tests()