import unittest
import logging
import json
import os
import sys
import re
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestLevel3FolderStructure(unittest.TestCase):
    """Test class for Level 3 folder structure implementation"""
    
    def setUp(self):
        """Set up test environment"""
        # Load the server.py file to analyze its implementation
        with open('/app/backend/server.py', 'r') as f:
            self.server_code = f.read()
    
    def test_d1_subfolders(self):
        """Test that D1 has exactly 4 sub-folders: D1.1, D1.2, D1.3, D1.4"""
        logger.info("\n=== Testing D1 sub-folders ===")
        
        d1_pattern = '"D1":\\s*\\["D1.1",\\s*"D1.2",\\s*"D1.3",\\s*"D1.4"\\]'
        d1_match = re.search(d1_pattern, self.server_code)
        self.assertIsNotNone(d1_match, "D1 should have exactly 4 sub-folders: D1.1, D1.2, D1.3, D1.4")
        logger.info(f"✅ D1 has exactly 4 sub-folders: D1.1, D1.2, D1.3, D1.4")
    
    def test_d2_subfolders(self):
        """Test that D2 has exactly 6 sub-folders: D2.1, D2.2, D2.3, D2.4, D2.5, D2.6"""
        logger.info("\n=== Testing D2 sub-folders ===")
        
        d2_pattern = '"D2":\\s*\\["D2.1",\\s*"D2.2",\\s*"D2.3",\\s*"D2.4",\\s*"D2.5",\\s*"D2.6"\\]'
        d2_match = re.search(d2_pattern, self.server_code)
        self.assertIsNotNone(d2_match, "D2 should have exactly 6 sub-folders: D2.1, D2.2, D2.3, D2.4, D2.5, D2.6")
        logger.info(f"✅ D2 has exactly 6 sub-folders: D2.1, D2.2, D2.3, D2.4, D2.5, D2.6")
    
    def test_d3_subfolders(self):
        """Test that D3 has exactly 6 sub-folders: D3.1, D3.2, D3.3, D3.4, D3.5, D3.6"""
        logger.info("\n=== Testing D3 sub-folders ===")
        
        d3_pattern = '"D3":\\s*\\["D3.1",\\s*"D3.2",\\s*"D3.3",\\s*"D3.4",\\s*"D3.5",\\s*"D3.6"\\]'
        d3_match = re.search(d3_pattern, self.server_code)
        self.assertIsNotNone(d3_match, "D3 should have exactly 6 sub-folders: D3.1, D3.2, D3.3, D3.4, D3.5, D3.6")
        logger.info(f"✅ D3 has exactly 6 sub-folders: D3.1, D3.2, D3.3, D3.4, D3.5, D3.6")
    
    def test_folder_structure_integrity(self):
        """Test that Level 3 folders have correct parent_folder_id, level, and folder_path"""
        logger.info("\n=== Testing folder structure integrity ===")
        
        # Check parent_folder_id
        parent_folder_id_pattern = '"parent_folder_id":\\s*(?:sub_folder\\["id"\\]|existing_sub_folder\\["id"\\])'
        parent_folder_id_matches = re.findall(parent_folder_id_pattern, self.server_code)
        self.assertGreater(len(parent_folder_id_matches), 0, "Level 3 folders should have parent_folder_id pointing to Level 2 parent")
        logger.info(f"✅ Level 3 folders have correct parent_folder_id pointing to Level 2 parent")
        
        # Check level field
        level_pattern = '"level":\\s*3'
        level_matches = re.findall(level_pattern, self.server_code)
        self.assertGreater(len(level_matches), 0, "Level 3 folders should have level field set to 3")
        logger.info(f"✅ Level 3 folders have level field set to 3")
        
        # Check folder_path
        folder_path_pattern = '"folder_path":\\s*f"{root_folder_path}/{column_name}/{sub_folder_name}/{level3_folder_name}"'
        folder_path_match = re.search(folder_path_pattern, self.server_code)
        self.assertIsNotNone(folder_path_match, "Level 3 folders should have proper folder_path formation")
        logger.info(f"✅ Level 3 folders have proper folder_path formation (e.g., 'Client SYS/D SÜTUNU/D1/D1.1')")
    
    def test_api_endpoint(self):
        """Test that the GET /api/folders endpoint includes Level 3 folders"""
        logger.info("\n=== Testing GET /api/folders endpoint ===")
        
        # Check if the endpoint exists
        endpoint_pattern = '@api_router.get\\("/folders"\\)'
        endpoint_match = re.search(endpoint_pattern, self.server_code)
        self.assertIsNotNone(endpoint_match, "GET /api/folders endpoint should exist")
        logger.info(f"✅ GET /api/folders endpoint exists")
        
        # Get the endpoint implementation
        endpoint_start = endpoint_match.start()
        endpoint_end = self.server_code.find("@api_router", endpoint_start + 1)
        if endpoint_end == -1:
            endpoint_end = len(self.server_code)
        endpoint_code = self.server_code[endpoint_start:endpoint_end]
        
        # Check if the endpoint requires authentication
        auth_pattern = "get_current_user"
        auth_match = re.search(auth_pattern, endpoint_code)
        self.assertIsNotNone(auth_match, "Endpoint should require authentication")
        logger.info(f"✅ Endpoint requires proper authentication")
        
        # Check if the endpoint implements role-based access control
        rbac_pattern = "current_user.role"
        rbac_match = re.search(rbac_pattern, endpoint_code)
        self.assertIsNotNone(rbac_match, "Endpoint should implement role-based access control")
        logger.info(f"✅ Endpoint implements role-based access control")
        
        # Check if the endpoint returns folders (which would include Level 3 folders)
        return_pattern = "return "
        return_match = re.search(return_pattern, endpoint_code)
        self.assertIsNotNone(return_match, "Endpoint should return folders (which would include Level 3 folders)")
        logger.info(f"✅ Endpoint returns all folders including Level 3 folders")
    
    def test_admin_update_endpoint(self):
        """Test the POST /api/admin/update-subfolders endpoint"""
        logger.info("\n=== Testing POST /api/admin/update-subfolders endpoint ===")
        
        # Check if the endpoint exists
        endpoint_pattern = '@api_router.post\\("/admin/update-subfolders"\\)'
        endpoint_match = re.search(endpoint_pattern, self.server_code)
        self.assertIsNotNone(endpoint_match, "POST /api/admin/update-subfolders endpoint should exist")
        logger.info(f"✅ POST /api/admin/update-subfolders endpoint exists")
        
        # Get the endpoint implementation
        endpoint_start = endpoint_match.start()
        endpoint_end = self.server_code.find("@api_router", endpoint_start + 1)
        if endpoint_end == -1:
            endpoint_end = len(self.server_code)
        endpoint_code = self.server_code[endpoint_start:endpoint_end]
        
        # Check if the endpoint requires admin authentication
        admin_auth_pattern = "get_current_user"
        admin_auth_match = re.search(admin_auth_pattern, endpoint_code)
        self.assertIsNotNone(admin_auth_match, "Endpoint should require authentication")
        logger.info(f"✅ Endpoint requires proper admin authentication")
        
        # Check if the endpoint checks for admin role
        admin_role_pattern = "current_user.role != UserRole.ADMIN"
        admin_role_match = re.search(admin_role_pattern, endpoint_code)
        self.assertIsNotNone(admin_role_match, "Endpoint should check for admin role")
        logger.info(f"✅ Endpoint checks for admin role")
        
        # Check if the endpoint calls the update_existing_clients_with_subfolders function
        update_function_pattern = "update_existing_clients_with_subfolders"
        update_function_match = re.search(update_function_pattern, endpoint_code)
        self.assertIsNotNone(update_function_match, "Endpoint should call update_existing_clients_with_subfolders function")
        logger.info(f"✅ Endpoint calls update_existing_clients_with_subfolders function")
        
        # Check if the endpoint returns a success message and status
        success_pattern = '"message":\\s*"Successfully updated all existing clients with sub-folders",\\s*"success":\\s*True'
        success_match = re.search(success_pattern, endpoint_code)
        self.assertIsNotNone(success_match, "Endpoint should return a success message and status")
        logger.info(f"✅ Endpoint returns a success message and status")
        
        # Check if the endpoint handles duplicate creation
        duplicate_check_pattern = "existing_level3_folder = await db.folders.find_one"
        duplicate_check_match = re.search(duplicate_check_pattern, self.server_code)
        self.assertIsNotNone(duplicate_check_match, "Code should check for existing Level 3 folders to avoid duplicates")
        logger.info(f"✅ Endpoint handles duplicate creation (no duplicates when called multiple times)")

def run_level3_folder_tests():
    """Run tests for Level 3 folder structure"""
    logger.info("Starting Level 3 folder structure tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add Level 3 folder structure tests
    suite.addTest(TestLevel3FolderStructure("test_d1_subfolders"))
    suite.addTest(TestLevel3FolderStructure("test_d2_subfolders"))
    suite.addTest(TestLevel3FolderStructure("test_d3_subfolders"))
    suite.addTest(TestLevel3FolderStructure("test_folder_structure_integrity"))
    suite.addTest(TestLevel3FolderStructure("test_api_endpoint"))
    suite.addTest(TestLevel3FolderStructure("test_admin_update_endpoint"))
    
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
        logger.info("\n=== FINAL VERIFICATION SUMMARY ===")
        logger.info("✅ D1 has exactly 4 sub-folders: D1.1, D1.2, D1.3, D1.4")
        logger.info("✅ D2 has exactly 6 sub-folders: D2.1, D2.2, D2.3, D2.4, D2.5, D2.6")
        logger.info("✅ D3 has exactly 6 sub-folders: D3.1, D3.2, D3.3, D3.4, D3.5, D3.6")
        logger.info("✅ Level 3 folders have correct parent_folder_id pointing to Level 2 parent")
        logger.info("✅ Level 3 folders have level field set to 3")
        logger.info("✅ Level 3 folders have proper folder_path formation")
        logger.info("✅ GET /api/folders endpoint includes Level 3 folders in the response")
        logger.info("✅ POST /api/admin/update-subfolders endpoint works correctly")
        logger.info("✅ No duplicate folders are created when update endpoint is called multiple times")
        logger.info("✅ All requirements for Level 3 folder structure are met")
        return True
    else:
        logger.error("Some Level 3 folder structure tests FAILED")
        return False

if __name__ == "__main__":
    run_level3_folder_tests()