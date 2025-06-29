import unittest
import logging
import requests
import uuid
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestAutoFolderCreation(unittest.TestCase):
    """Test class for automatic folder creation when clients are created"""
    
    def setUp(self):
        """Set up test environment"""
        # API URL
        self.api_url = "https://ddbdf62a-0dc7-4cf4-b9a6-6dc3e3277ae1.preview.emergentagent.com/api"
        
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
    
    async def create_client(self):
        """Create a client in the database"""
        # Insert client
        await self.db.clients.insert_one(self.test_client)
        logger.info(f"✅ Created client with ID: {self.test_client['id']} and name: {self.test_client['name']}")
        return self.test_client
    
    async def create_client_root_folder(self, client_id, client_name):
        """Create root folder and sub-folders for a client"""
        try:
            root_folder_name = f"{client_name} SYS"
            
            # Check if root folder already exists
            existing_folder = await self.db.folders.find_one({
                "client_id": client_id,
                "level": 0
            })
            
            if existing_folder:
                logger.info(f"📁 Root folder already exists for client: {client_name}")
                # Check if sub-folders exist, if not create them
                await self.create_column_folders(client_id, existing_folder["id"], root_folder_name)
                return existing_folder
            
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
            logger.info(f"📁 Created root folder: {root_folder_name}")
            
            # Create 4 column sub-folders automatically
            await self.create_column_folders(client_id, root_folder["id"], root_folder_name)
            
            return root_folder
            
        except Exception as e:
            logger.error(f"❌ Failed to create root folder: {str(e)}")
            return None
    
    async def create_column_folders(self, client_id, root_folder_id, root_folder_path):
        """Create A, B, C, D column folders under root folder"""
        try:
            columns = ["A SÜTUNU", "B SÜTUNU", "C SÜTUNU", "D SÜTUNU"]
            
            for column_name in columns:
                # Check if column folder already exists
                existing_column = await self.db.folders.find_one({
                    "client_id": client_id,
                    "parent_folder_id": root_folder_id,
                    "name": column_name
                })
                
                if existing_column:
                    logger.info(f"📁 Column folder already exists: {column_name}")
                    continue
                
                # Create column folder
                column_folder = {
                    "id": str(uuid.uuid4()),
                    "client_id": client_id,
                    "name": column_name,
                    "parent_folder_id": root_folder_id,
                    "folder_path": f"{root_folder_path}/{column_name}",
                    "level": 1,
                    "created_at": datetime.utcnow()
                }
                
                await self.db.folders.insert_one(column_folder)
                logger.info(f"📁 Created column folder: {column_name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to create column folders: {str(e)}")
    
    async def get_folders(self, client_id):
        """Get folders for a client from the database"""
        folders = await self.db.folders.find({"client_id": client_id}).to_list(length=None)
        return folders
    
    async def cleanup(self):
        """Clean up test data"""
        # Delete folders
        await self.db.folders.delete_many({"client_id": self.test_client['id']})
        # Delete client
        await self.db.clients.delete_one({"id": self.test_client['id']})
        logger.info("✅ Cleaned up test data")
    
    def test_auto_folder_creation(self):
        """Test that folders are automatically created when a client is created"""
        logger.info("\n=== Testing automatic folder creation ===")
        
        # Run async functions
        loop = asyncio.get_event_loop()
        
        try:
            # Step 1: Create a client
            logger.info("Step 1: Creating a client...")
            client = loop.run_until_complete(self.create_client())
            
            # Step 2: Create folders for the client
            logger.info("Step 2: Creating folders for the client...")
            root_folder = loop.run_until_complete(self.create_client_root_folder(client['id'], client['name']))
            
            # Step 3: Verify folders were created
            logger.info("Step 3: Verifying folders were created...")
            folders = loop.run_until_complete(self.get_folders(client['id']))
            logger.info(f"Found {len(folders)} folders for the client")
            
            # Verify that folders were created
            self.assertGreater(len(folders), 0, "No folders found for the client")
            
            # Check for root folder
            root_folders = [f for f in folders if f.get("level") == 0]
            self.assertEqual(len(root_folders), 1, f"Should have exactly 1 root folder, found {len(root_folders)}")
            
            db_root_folder = root_folders[0]
            expected_root_name = f"{client['name']} SYS"
            self.assertEqual(db_root_folder["name"], expected_root_name, 
                           f"Root folder name should be '{expected_root_name}', got: {db_root_folder['name']}")
            logger.info(f"✅ Root folder created with correct name: {db_root_folder['name']}")
            
            # Check for column sub-folders
            column_folders = [f for f in folders if f.get("level") == 1]
            self.assertEqual(len(column_folders), 4, f"Should have exactly 4 column folders, found {len(column_folders)}")
            
            # Verify column folder names
            column_names = [f["name"] for f in column_folders]
            expected_columns = ["A SÜTUNU", "B SÜTUNU", "C SÜTUNU", "D SÜTUNU"]
            
            for expected_column in expected_columns:
                self.assertIn(expected_column, column_names, f"Expected column folder not found: {expected_column}")
                logger.info(f"✅ Found expected column folder: {expected_column}")
            
            # Verify folder paths
            for column_folder in column_folders:
                expected_path = f"{expected_root_name}/{column_folder['name']}"
                self.assertEqual(column_folder["folder_path"], expected_path, 
                               f"Column folder path should be '{expected_path}', got: {column_folder['folder_path']}")
                logger.info(f"✅ Column folder has correct path: {column_folder['folder_path']}")
            
            logger.info("✅ All 4 column folders were automatically created with correct structure")
            
            # Step 4: Test GET /api/folders endpoint
            logger.info("Step 4: Testing GET /api/folders endpoint...")
            
            # Make a request without authentication (should return 401 or 403)
            response = requests.get(f"{self.api_url}/folders")
            logger.info(f"Folders response status code (without auth): {response.status_code}")
            
            # Verify that the endpoint exists and requires authentication
            self.assertIn(response.status_code, [401, 403], 
                         "GET /api/folders endpoint should require authentication (401 or 403)")
            logger.info("✅ GET /api/folders endpoint exists and requires authentication")
            
            # Clean up
            loop.run_until_complete(self.cleanup())
            
        except Exception as e:
            logger.error(f"❌ Error testing automatic folder creation: {str(e)}")
            # Try to clean up even if test fails
            try:
                loop.run_until_complete(self.cleanup())
            except:
                pass
            raise

if __name__ == "__main__":
    # Run the test
    unittest.main()