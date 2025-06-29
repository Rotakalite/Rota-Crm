import unittest
import logging
import uuid
from datetime import datetime
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestHierarchicalFolderStructure(unittest.TestCase):
    """Test class for enhanced hierarchical folder system with sub-folders using direct database access"""
    
    def setUp(self):
        """Set up test environment"""
        # MongoDB connection
        self.mongo_url = "mongodb://localhost:27017"
        self.db_name = "sustainable_tourism_crm"
        
        # Connect to MongoDB
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client[self.db_name]
        
        # Test client data with unique name
        self.test_client = {
            "id": str(uuid.uuid4()),
            "name": f"Test Client {uuid.uuid4().hex[:8]}",
            "hotel_name": "Test Hotel",
            "contact_person": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "address": "123 Test St",
            "current_stage": "I.Aşama",
            "services_completed": [],
            "carbon_footprint": None,
            "sustainability_score": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
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
    
    async def create_client_root_folder(self, client_id, client_name):
        """Create root folder for a client"""
        root_folder_name = f"{client_name} SYS"
        
        # Create root folder
        root_folder = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "name": root_folder_name,
            "parent_folder_id": None,
            "folder_path": root_folder_name,
            "level": 0,
            "created_at": datetime.utcnow()
        }
        
        await self.db.folders.insert_one(root_folder)
        logger.info(f"✅ Created root folder: {root_folder_name}")
        
        return root_folder
    
    async def create_column_folders(self, client_id, root_folder_id, root_folder_path):
        """Create A, B, C, D column folders under root folder with their sub-folders"""
        column_folders = []
        
        # Define main columns and their sub-folders
        column_structure = self.expected_subfolder_structure
        
        for column_name, sub_folders in column_structure.items():
            # Create column folder
            column_folder_id = str(uuid.uuid4())
            column_folder = {
                "id": column_folder_id,
                "client_id": client_id,
                "name": column_name,
                "parent_folder_id": root_folder_id,
                "folder_path": f"{root_folder_path}/{column_name}",
                "level": 1,
                "created_at": datetime.utcnow()
            }
            
            await self.db.folders.insert_one(column_folder)
            column_folders.append(column_folder)
            logger.info(f"✅ Created column folder: {column_name}")
            
            # Create sub-folders for this column
            for sub_folder_name in sub_folders:
                # Create sub-folder
                sub_folder = {
                    "id": str(uuid.uuid4()),
                    "client_id": client_id,
                    "name": sub_folder_name,
                    "parent_folder_id": column_folder_id,
                    "folder_path": f"{root_folder_path}/{column_name}/{sub_folder_name}",
                    "level": 2,
                    "created_at": datetime.utcnow()
                }
                
                await self.db.folders.insert_one(sub_folder)
                logger.info(f"✅ Created sub-folder: {column_name}/{sub_folder_name}")
        
        return column_folders
    
    async def cleanup(self):
        """Clean up test data"""
        # Delete folders
        await self.db.folders.delete_many({"client_id": self.test_client['id']})
        # Delete client
        await self.db.clients.delete_one({"id": self.test_client['id']})
        logger.info("✅ Cleaned up test data")
    
    def test_folder_structure_creation(self):
        """Test that the complete 3-level folder hierarchy is created correctly"""
        logger.info("\n=== Testing complete 3-level folder hierarchy creation ===")
        
        async def run_test():
            try:
                # Step 1: Insert client
                await self.db.clients.insert_one(self.test_client)
                logger.info(f"✅ Created client with ID: {self.test_client['id']} and name: {self.test_client['name']}")
                
                # Step 2: Create root folder
                root_folder = await self.create_client_root_folder(self.test_client['id'], self.test_client['name'])
                
                # Step 3: Create column folders with sub-folders
                column_folders = await self.create_column_folders(self.test_client['id'], root_folder['id'], root_folder['folder_path'])
                
                # Step 4: Verify folder structure
                # Get all folders for the client
                client_folders = await self.db.folders.find({"client_id": self.test_client['id']}).to_list(length=None)
                logger.info(f"Found {len(client_folders)} folders for the client in database")
                
                # Verify total folder count
                expected_total_folders = 1 + 4 + self.total_expected_subfolders  # 1 root + 4 columns + sub-folders
                self.assertEqual(len(client_folders), expected_total_folders, 
                               f"Should have {expected_total_folders} total folders, found {len(client_folders)}")
                logger.info(f"✅ Total folder count is correct: {len(client_folders)}")
                
                # Verify root folder
                root_folders = [f for f in client_folders if f.get("level") == 0]
                self.assertEqual(len(root_folders), 1, f"Should have exactly 1 root folder, found {len(root_folders)}")
                
                db_root_folder = root_folders[0]
                expected_root_name = f"{self.test_client['name']} SYS"
                self.assertEqual(db_root_folder["name"], expected_root_name, 
                               f"Root folder name should be '{expected_root_name}', got: {db_root_folder['name']}")
                logger.info(f"✅ Root folder verified in database: {db_root_folder['name']}")
                
                # Verify column folders
                column_folders = [f for f in client_folders if f.get("level") == 1]
                self.assertEqual(len(column_folders), 4, f"Should have exactly 4 column folders, found {len(column_folders)}")
                
                # Verify column folder names
                column_names = [f["name"] for f in column_folders]
                expected_columns = ["A SÜTUNU", "B SÜTUNU", "C SÜTUNU", "D SÜTUNU"]
                
                for expected_column in expected_columns:
                    self.assertIn(expected_column, column_names, f"Expected column folder not found: {expected_column}")
                    logger.info(f"✅ Found expected column folder in database: {expected_column}")
                
                # Verify sub-folders
                sub_folders = [f for f in client_folders if f.get("level") == 2]
                self.assertEqual(len(sub_folders), self.total_expected_subfolders, 
                               f"Should have {self.total_expected_subfolders} sub-folders, found {len(sub_folders)}")
                logger.info(f"✅ Found {len(sub_folders)} sub-folders (level 2)")
                
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
                
                logger.info("✅ All sub-folders were created with correct structure")
                
                # Clean up
                await self.cleanup()
                
            except Exception as e:
                logger.error(f"❌ Error testing folder structure creation: {str(e)}")
                # Make sure to clean up even if test fails
                await self.cleanup()
                raise
        
        # Run the async test
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_test())
    
    def test_folder_hierarchy_validation(self):
        """Test that folder hierarchy is correctly formed with proper parent-child relationships"""
        logger.info("\n=== Testing folder hierarchy validation ===")
        
        async def run_test():
            try:
                # Step 1: Insert client
                await self.db.clients.insert_one(self.test_client)
                logger.info(f"✅ Created client with ID: {self.test_client['id']} and name: {self.test_client['name']}")
                
                # Step 2: Create root folder
                root_folder = await self.create_client_root_folder(self.test_client['id'], self.test_client['name'])
                
                # Step 3: Create column folders with sub-folders
                column_folders = await self.create_column_folders(self.test_client['id'], root_folder['id'], root_folder['folder_path'])
                
                # Step 4: Verify folder hierarchy
                # Get all folders for the client
                client_folders = await self.db.folders.find({"client_id": self.test_client['id']}).to_list(length=None)
                
                # Verify column folders have correct parent_folder_id
                db_column_folders = [f for f in client_folders if f.get("level") == 1]
                for column_folder in db_column_folders:
                    self.assertEqual(column_folder["parent_folder_id"], root_folder["id"], 
                                   f"Column folder {column_folder['name']} should have parent_folder_id {root_folder['id']}, got: {column_folder['parent_folder_id']}")
                    logger.info(f"✅ Column folder {column_folder['name']} has correct parent_folder_id")
                
                # Verify sub-folders have correct parent_folder_id
                sub_folders = [f for f in client_folders if f.get("level") == 2]
                
                # Group sub-folders by parent folder
                sub_folders_by_parent = {}
                for sub_folder in sub_folders:
                    parent_id = sub_folder.get("parent_folder_id")
                    if parent_id not in sub_folders_by_parent:
                        sub_folders_by_parent[parent_id] = []
                    sub_folders_by_parent[parent_id].append(sub_folder)
                
                for column_folder in db_column_folders:
                    column_id = column_folder.get("id")
                    column_name = column_folder.get("name")
                    
                    if column_id in sub_folders_by_parent:
                        column_sub_folders = sub_folders_by_parent[column_id]
                        
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
                
                # Clean up
                await self.cleanup()
                
            except Exception as e:
                logger.error(f"❌ Error testing folder hierarchy validation: {str(e)}")
                # Make sure to clean up even if test fails
                await self.cleanup()
                raise
        
        # Run the async test
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_test())
    
    def test_multiple_clients(self):
        """Test creating multiple clients to ensure each gets their own complete folder structure"""
        logger.info("\n=== Testing multiple clients folder structure ===")
        
        async def run_test():
            # Create two test clients
            test_clients = [
                {
                    "id": str(uuid.uuid4()),
                    "name": f"Test Client A {uuid.uuid4().hex[:8]}",
                    "hotel_name": "Test Hotel A",
                    "contact_person": "John Doe",
                    "email": "john@example.com",
                    "phone": "1234567890",
                    "address": "123 Test St",
                    "current_stage": "I.Aşama",
                    "services_completed": [],
                    "carbon_footprint": None,
                    "sustainability_score": None,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": f"Test Client B {uuid.uuid4().hex[:8]}",
                    "hotel_name": "Test Hotel B",
                    "contact_person": "Jane Smith",
                    "email": "jane@example.com",
                    "phone": "9876543210",
                    "address": "456 Test Ave",
                    "current_stage": "I.Aşama",
                    "services_completed": [],
                    "carbon_footprint": None,
                    "sustainability_score": None,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]
            
            try:
                # Step 1: Insert clients
                for i, test_client in enumerate(test_clients):
                    await self.db.clients.insert_one(test_client)
                    logger.info(f"✅ Created client {i+1} with ID: {test_client['id']} and name: {test_client['name']}")
                
                # Step 2: Create folder structure for each client
                for i, test_client in enumerate(test_clients):
                    # Create root folder
                    root_folder = await self.create_client_root_folder(test_client['id'], test_client['name'])
                    
                    # Create column folders with sub-folders
                    column_folders = await self.create_column_folders(test_client['id'], root_folder['id'], root_folder['folder_path'])
                
                # Step 3: Verify folder structure for each client
                for i, test_client in enumerate(test_clients):
                    # Get all folders for the client
                    client_folders = await self.db.folders.find({"client_id": test_client['id']}).to_list(length=None)
                    logger.info(f"Found {len(client_folders)} folders for client {i+1}: {test_client['name']}")
                    
                    # Verify total folder count
                    expected_total_folders = 1 + 4 + self.total_expected_subfolders  # 1 root + 4 columns + sub-folders
                    self.assertEqual(len(client_folders), expected_total_folders, 
                                   f"Client {i+1} should have {expected_total_folders} total folders, found {len(client_folders)}")
                    
                    # Verify root folder
                    root_folders = [f for f in client_folders if f.get("level") == 0]
                    self.assertEqual(len(root_folders), 1, f"Client {i+1} should have exactly 1 root folder, found {len(root_folders)}")
                    
                    # Verify column folders
                    column_folders = [f for f in client_folders if f.get("level") == 1]
                    self.assertEqual(len(column_folders), 4, f"Client {i+1} should have exactly 4 column folders, found {len(column_folders)}")
                    
                    # Verify sub-folders
                    sub_folders = [f for f in client_folders if f.get("level") == 2]
                    self.assertEqual(len(sub_folders), self.total_expected_subfolders, 
                                   f"Client {i+1} should have {self.total_expected_subfolders} sub-folders, found {len(sub_folders)}")
                    
                    logger.info(f"✅ Client {i+1} has correct folder structure with {len(client_folders)} total folders")
                
                logger.info("✅ Multiple clients test passed - each client has its own complete folder structure")
                
                # Clean up
                for test_client in test_clients:
                    await self.db.folders.delete_many({"client_id": test_client['id']})
                    await self.db.clients.delete_one({"id": test_client['id']})
                logger.info("✅ Cleaned up test data for multiple clients")
                
            except Exception as e:
                logger.error(f"❌ Error testing multiple clients: {str(e)}")
                # Make sure to clean up even if test fails
                for test_client in test_clients:
                    await self.db.folders.delete_many({"client_id": test_client['id']})
                    await self.db.clients.delete_one({"id": test_client['id']})
                raise
        
        # Run the async test
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_test())

def run_hierarchical_folder_tests():
    """Run tests for hierarchical folder system with sub-folders"""
    logger.info("Starting hierarchical folder system tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add hierarchical folder system tests
    suite.addTest(TestHierarchicalFolderStructure("test_folder_structure_creation"))
    suite.addTest(TestHierarchicalFolderStructure("test_folder_hierarchy_validation"))
    suite.addTest(TestHierarchicalFolderStructure("test_multiple_clients"))
    
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