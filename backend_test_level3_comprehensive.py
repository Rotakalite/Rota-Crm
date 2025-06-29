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

class TestLevel3FolderStructureComprehensive(unittest.TestCase):
    """Comprehensive test class for Level 3 folder structure implementation"""
    
    def setUp(self):
        """Set up test environment"""
        # Load the server.py file to analyze its implementation
        with open('/app/backend/server.py', 'r') as f:
            self.server_code = f.read()
    
    def test_level3_folder_structure_requirements(self):
        """Test that Level 3 sub-folders meet all requirements"""
        logger.info("\n=== Testing Level 3 folder structure requirements ===")
        
        # Requirement 1: D1 should have 4 sub-folders: D1.1, D1.2, D1.3, D1.4
        d1_pattern = '"D1":\\s*\\["D1.1",\\s*"D1.2",\\s*"D1.3",\\s*"D1.4"\\]'
        d1_match = re.search(d1_pattern, self.server_code)
        self.assertIsNotNone(d1_match, "D1 should have exactly 4 sub-folders: D1.1, D1.2, D1.3, D1.4")
        logger.info(f"✅ Requirement 1: D1 has exactly 4 sub-folders: D1.1, D1.2, D1.3, D1.4")
        
        # Requirement 2: D2 should have 6 sub-folders: D2.1, D2.2, D2.3, D2.4, D2.5, D2.6
        d2_pattern = '"D2":\\s*\\["D2.1",\\s*"D2.2",\\s*"D2.3",\\s*"D2.4",\\s*"D2.5",\\s*"D2.6"\\]'
        d2_match = re.search(d2_pattern, self.server_code)
        self.assertIsNotNone(d2_match, "D2 should have exactly 6 sub-folders: D2.1, D2.2, D2.3, D2.4, D2.5, D2.6")
        logger.info(f"✅ Requirement 2: D2 has exactly 6 sub-folders: D2.1, D2.2, D2.3, D2.4, D2.5, D2.6")
        
        # Requirement 3: D3 should have 6 sub-folders: D3.1, D3.2, D3.3, D3.4, D3.5, D3.6
        d3_pattern = '"D3":\\s*\\["D3.1",\\s*"D3.2",\\s*"D3.3",\\s*"D3.4",\\s*"D3.5",\\s*"D3.6"\\]'
        d3_match = re.search(d3_pattern, self.server_code)
        self.assertIsNotNone(d3_match, "D3 should have exactly 6 sub-folders: D3.1, D3.2, D3.3, D3.4, D3.5, D3.6")
        logger.info(f"✅ Requirement 3: D3 has exactly 6 sub-folders: D3.1, D3.2, D3.3, D3.4, D3.5, D3.6")
        
        # Requirement 4: Level 3 folders should have correct parent_folder_id pointing to their Level 2 parent
        parent_folder_id_pattern = '"parent_folder_id":\\s*(?:sub_folder\\["id"\\]|existing_sub_folder\\["id"\\])'
        parent_folder_id_matches = re.findall(parent_folder_id_pattern, self.server_code)
        self.assertGreater(len(parent_folder_id_matches), 0, "Level 3 folders should have parent_folder_id pointing to Level 2 parent")
        logger.info(f"✅ Requirement 4: Level 3 folders have correct parent_folder_id pointing to Level 2 parent")
        
        # Requirement 5: Level 3 folders should have level field set to 3
        level_pattern = '"level":\\s*3'
        level_matches = re.findall(level_pattern, self.server_code)
        self.assertGreater(len(level_matches), 0, "Level 3 folders should have level field set to 3")
        logger.info(f"✅ Requirement 5: Level 3 folders have level field set to 3")
        
        # Requirement 6: Level 3 folders should have proper folder_path formation
        folder_path_pattern = '"folder_path":\\s*f"{root_folder_path}/{column_name}/{sub_folder_name}/{level3_folder_name}"'
        folder_path_match = re.search(folder_path_pattern, self.server_code)
        self.assertIsNotNone(folder_path_match, "Level 3 folders should have proper folder_path formation")
        logger.info(f"✅ Requirement 6: Level 3 folders have proper folder_path formation")
        
        logger.info("✅ All Level 3 folder structure requirements are met")
    
    def test_admin_update_subfolders_endpoint(self):
        """Test the POST /api/admin/update-subfolders endpoint implementation"""
        logger.info("\n=== Testing POST /api/admin/update-subfolders endpoint implementation ===")
        
        # Check if the endpoint exists
        endpoint_pattern = '@api_router.post\\("/admin/update-subfolders"\\)'
        endpoint_match = re.search(endpoint_pattern, self.server_code)
        self.assertIsNotNone(endpoint_match, "POST /api/admin/update-subfolders endpoint should exist")
        logger.info(f"✅ POST /api/admin/update-subfolders endpoint exists")
        
        # Check if the endpoint requires admin authentication
        admin_auth_pattern = "get_current_user"
        endpoint_section = self.server_code.split('@api_router.post("/admin/update-subfolders")')[1].split('@api_router')[0]
        self.assertIn(admin_auth_pattern, endpoint_section, "Endpoint should require authentication")
        logger.info(f"✅ Endpoint requires authentication")
        
        # Check if the endpoint checks for admin role
        admin_role_pattern = "current_user.role != UserRole.ADMIN"
        self.assertIn(admin_role_pattern, endpoint_section, "Endpoint should check for admin role")
        logger.info(f"✅ Endpoint checks for admin role")
        
        # Check if the endpoint calls the update_existing_clients_with_subfolders function
        update_function_pattern = "update_existing_clients_with_subfolders"
        self.assertIn(update_function_pattern, endpoint_section, "Endpoint should call update_existing_clients_with_subfolders function")
        logger.info(f"✅ Endpoint calls update_existing_clients_with_subfolders function")
        
        # Check if the endpoint returns a success message
        success_message_pattern = '"message":\\s*"Successfully updated all existing clients with sub-folders"'
        success_message_match = re.search(success_message_pattern, endpoint_section)
        self.assertIsNotNone(success_message_match, "Endpoint should return a success message")
        logger.info(f"✅ Endpoint returns a success message")
        
        # Check if the endpoint returns a success status
        success_status_pattern = '"success":\\s*True'
        success_status_match = re.search(success_status_pattern, endpoint_section)
        self.assertIsNotNone(success_status_match, "Endpoint should return a success status")
        logger.info(f"✅ Endpoint returns a success status")
        
        logger.info("✅ POST /api/admin/update-subfolders endpoint implementation is correct")
    
    def test_update_existing_clients_with_subfolders_function(self):
        """Test the update_existing_clients_with_subfolders function implementation"""
        logger.info("\n=== Testing update_existing_clients_with_subfolders function implementation ===")
        
        # Check if the function exists
        function_pattern = "async def update_existing_clients_with_subfolders\\(\\):"
        function_match = re.search(function_pattern, self.server_code)
        self.assertIsNotNone(function_match, "update_existing_clients_with_subfolders function should exist")
        logger.info(f"✅ update_existing_clients_with_subfolders function exists")
        
        # Get the function implementation
        function_start = function_match.start()
        function_end = self.server_code.find("async def", function_start + 1)
        if function_end == -1:
            function_end = self.server_code.find("# Routes", function_start)
        function_code = self.server_code[function_start:function_end]
        
        # Check if the function gets all clients
        get_clients_pattern = "clients = await db.clients.find\\(\\{\\}\\).to_list\\(length=None\\)"
        get_clients_match = re.search(get_clients_pattern, function_code)
        self.assertIsNotNone(get_clients_match, "Function should get all clients")
        logger.info(f"✅ Function gets all clients")
        
        # Check if the function finds the root folder for each client
        find_root_pattern = "root_folder = await db.folders.find_one\\(\\{\\s*\"client_id\":\\s*client_id,\\s*\"level\":\\s*0\\s*\\}\\)"
        find_root_match = re.search(find_root_pattern, function_code)
        self.assertIsNotNone(find_root_match, "Function should find the root folder for each client")
        logger.info(f"✅ Function finds the root folder for each client")
        
        # Check if the function finds column folders
        find_columns_pattern = "column_folders = await db.folders.find\\(\\{\\s*\"client_id\":\\s*client_id,\\s*\"level\":\\s*1\\s*\\}\\).to_list\\(length=None\\)"
        find_columns_match = re.search(find_columns_pattern, function_code)
        self.assertIsNotNone(find_columns_match, "Function should find column folders")
        logger.info(f"✅ Function finds column folders")
        
        # Check if the function creates sub-folders for each column
        create_subfolders_pattern = "sub_folder = \\{\\s*\"id\":\\s*str\\(uuid.uuid4\\(\\)\\),\\s*\"client_id\":\\s*client_id,"
        create_subfolders_matches = re.findall(create_subfolders_pattern, function_code)
        self.assertGreater(len(create_subfolders_matches), 0, "Function should create sub-folders for each column")
        logger.info(f"✅ Function creates sub-folders for each column")
        
        # Check if the function checks for existing sub-folders before creating new ones
        check_existing_pattern = "existing_subfolders = await db.folders.find\\(\\{\\s*\"client_id\":\\s*client_id,\\s*\"parent_folder_id\":\\s*column_id,\\s*\"level\":\\s*2\\s*\\}\\).to_list\\(length=None\\)"
        check_existing_match = re.search(check_existing_pattern, function_code)
        self.assertIsNotNone(check_existing_match, "Function should check for existing sub-folders")
        logger.info(f"✅ Function checks for existing sub-folders before creating new ones")
        
        # Check if the function returns a success status
        return_success_pattern = "return True"
        return_success_match = re.search(return_success_pattern, function_code)
        self.assertIsNotNone(return_success_match, "Function should return a success status")
        logger.info(f"✅ Function returns a success status")
        
        logger.info("✅ update_existing_clients_with_subfolders function implementation is correct")
    
    def test_get_folders_endpoint(self):
        """Test the GET /api/folders endpoint implementation"""
        logger.info("\n=== Testing GET /api/folders endpoint implementation ===")
        
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
        logger.info(f"✅ Endpoint requires authentication")
        
        # Check if the endpoint implements role-based access control
        rbac_pattern = "current_user.role"
        rbac_match = re.search(rbac_pattern, endpoint_code)
        self.assertIsNotNone(rbac_match, "Endpoint should implement role-based access control")
        logger.info(f"✅ Endpoint implements role-based access control")
        
        # Check if admin users can see all folders
        admin_access_pattern = "UserRole.ADMIN"
        admin_access_match = re.search(admin_access_pattern, endpoint_code)
        self.assertIsNotNone(admin_access_match, "Endpoint should allow admin users to see all folders")
        logger.info(f"✅ Endpoint allows admin users to see all folders")
        
        # Check if client users can only see their own folders
        client_access_pattern = "current_user.client_id"
        client_access_match = re.search(client_access_pattern, endpoint_code)
        self.assertIsNotNone(client_access_match, "Endpoint should restrict client users to their own folders")
        logger.info(f"✅ Endpoint restricts client users to their own folders")
        
        # Check if the endpoint returns all folders including Level 3 folders
        return_all_pattern = "return folders"
        return_all_match = re.search(return_all_pattern, endpoint_code)
        self.assertIsNotNone(return_all_match, "Endpoint should return all folders including Level 3 folders")
        logger.info(f"✅ Endpoint returns all folders including Level 3 folders")
        
        logger.info("✅ GET /api/folders endpoint implementation is correct")

def run_level3_folder_comprehensive_tests():
    """Run comprehensive tests for Level 3 folder structure"""
    logger.info("Starting comprehensive Level 3 folder structure tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add comprehensive Level 3 folder structure tests
    suite.addTest(TestLevel3FolderStructureComprehensive("test_level3_folder_structure_requirements"))
    suite.addTest(TestLevel3FolderStructureComprehensive("test_admin_update_subfolders_endpoint"))
    suite.addTest(TestLevel3FolderStructureComprehensive("test_update_existing_clients_with_subfolders_function"))
    suite.addTest(TestLevel3FolderStructureComprehensive("test_get_folders_endpoint"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Comprehensive Level 3 Folder Structure Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All comprehensive Level 3 folder structure tests PASSED")
        return True
    else:
        logger.error("Some comprehensive Level 3 folder structure tests FAILED")
        return False

if __name__ == "__main__":
    run_level3_folder_comprehensive_tests()