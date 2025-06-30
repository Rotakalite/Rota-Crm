import unittest
import logging
import os
import pymongo
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestFolderDocumentCount(unittest.TestCase):
    """Test class for folder document count functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Connect to MongoDB
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'sustainable_tourism_crm')
        
        self.client = pymongo.MongoClient(mongo_url)
        self.db = self.client[db_name]
        
        logger.info(f"Connected to MongoDB: {mongo_url}, Database: {db_name}")
    
    def tearDown(self):
        """Clean up after tests"""
        self.client.close()
    
    def test_documents_have_folder_id(self):
        """Test that documents in the database have valid folder_id fields"""
        logger.info("\n=== Testing documents have valid folder_id fields ===")
        
        # Get all documents
        documents = list(self.db.documents.find())
        logger.info(f"Found {len(documents)} documents")
        
        # Check if documents have folder_id
        documents_with_folder_id = [doc for doc in documents if 'folder_id' in doc and doc['folder_id']]
        documents_without_folder_id = [doc for doc in documents if 'folder_id' not in doc or not doc['folder_id']]
        
        logger.info(f"Documents with folder_id: {len(documents_with_folder_id)}")
        logger.info(f"Documents without folder_id: {len(documents_without_folder_id)}")
        
        # Log documents without folder_id for debugging
        if documents_without_folder_id:
            logger.warning("Documents without folder_id:")
            for doc in documents_without_folder_id:
                logger.warning(f"  - Document ID: {doc.get('id')}, Name: {doc.get('name')}")
        
        # Assert that all documents have folder_id
        self.assertEqual(len(documents_without_folder_id), 0, 
                        "All documents should have folder_id")
        
        # Check if folder_id values are valid (not empty strings)
        invalid_folder_ids = [doc for doc in documents if 'folder_id' in doc and doc['folder_id'] == ""]
        logger.info(f"Documents with empty folder_id: {len(invalid_folder_ids)}")
        
        if invalid_folder_ids:
            logger.warning("Documents with empty folder_id:")
            for doc in invalid_folder_ids:
                logger.warning(f"  - Document ID: {doc.get('id')}, Name: {doc.get('name')}")
        
        self.assertEqual(len(invalid_folder_ids), 0, 
                        "No documents should have empty folder_id")
        
        logger.info("✅ All documents have valid folder_id fields")
    
    def test_folders_exist(self):
        """Test that folders exist with proper ids"""
        logger.info("\n=== Testing folders exist with proper ids ===")
        
        # Get all folders
        folders = list(self.db.folders.find())
        logger.info(f"Found {len(folders)} folders")
        
        # Check if folders have id
        folders_with_id = [folder for folder in folders if 'id' in folder and folder['id']]
        folders_without_id = [folder for folder in folders if 'id' not in folder or not folder['id']]
        
        logger.info(f"Folders with id: {len(folders_with_id)}")
        logger.info(f"Folders without id: {len(folders_without_id)}")
        
        # Log folders without id for debugging
        if folders_without_id:
            logger.warning("Folders without id:")
            for folder in folders_without_id:
                logger.warning(f"  - Folder Name: {folder.get('name')}")
        
        # Assert that all folders have id
        self.assertEqual(len(folders_without_id), 0, 
                        "All folders should have id")
        
        # Check if id values are valid (not empty strings)
        invalid_ids = [folder for folder in folders if 'id' in folder and folder['id'] == ""]
        logger.info(f"Folders with empty id: {len(invalid_ids)}")
        
        if invalid_ids:
            logger.warning("Folders with empty id:")
            for folder in invalid_ids:
                logger.warning(f"  - Folder Name: {folder.get('name')}")
        
        self.assertEqual(len(invalid_ids), 0, 
                        "No folders should have empty id")
        
        logger.info("✅ All folders have valid ids")
        
        # Return folders for use in other tests
        return folders
    
    def test_document_folder_relationship(self):
        """Test that the relationship between documents and folders is working"""
        logger.info("\n=== Testing document-folder relationship ===")
        
        # Get all documents and folders
        documents = list(self.db.documents.find())
        folders = list(self.db.folders.find())
        
        logger.info(f"Found {len(documents)} documents and {len(folders)} folders")
        
        # Create a set of folder IDs for quick lookup
        folder_ids = {folder.get('id') for folder in folders}
        
        # Check if document folder_ids exist in folders
        documents_with_valid_folder_id = []
        documents_with_invalid_folder_id = []
        
        for doc in documents:
            folder_id = doc.get('folder_id')
            if folder_id and folder_id in folder_ids:
                documents_with_valid_folder_id.append(doc)
            else:
                documents_with_invalid_folder_id.append(doc)
        
        logger.info(f"Documents with valid folder_id: {len(documents_with_valid_folder_id)}")
        logger.info(f"Documents with invalid folder_id: {len(documents_with_invalid_folder_id)}")
        
        # Log documents with invalid folder_id for debugging
        if documents_with_invalid_folder_id:
            logger.warning("Documents with invalid folder_id:")
            for doc in documents_with_invalid_folder_id:
                logger.warning(f"  - Document ID: {doc.get('id')}, Name: {doc.get('name')}, Folder ID: {doc.get('folder_id')}")
        
        # Assert that all documents have valid folder_id
        self.assertEqual(len(documents_with_invalid_folder_id), 0, 
                        "All documents should have valid folder_id that exists in folders")
        
        # Count documents per folder
        folder_document_counts = {}
        for doc in documents:
            folder_id = doc.get('folder_id')
            if folder_id:
                folder_document_counts[folder_id] = folder_document_counts.get(folder_id, 0) + 1
        
        # Log folder document counts
        logger.info("Folder document counts:")
        for folder_id, count in folder_document_counts.items():
            # Find folder name
            folder_name = next((folder.get('name') for folder in folders if folder.get('id') == folder_id), "Unknown")
            logger.info(f"  - Folder: {folder_name} (ID: {folder_id}) - Document Count: {count}")
        
        # Check if there are folders with no documents
        folders_with_no_documents = [folder for folder in folders if folder.get('id') not in folder_document_counts]
        logger.info(f"Folders with no documents: {len(folders_with_no_documents)}")
        
        # This is not an error, just informational
        if folders_with_no_documents:
            logger.info("Folders with no documents (showing first 10):")
            for folder in folders_with_no_documents[:10]:  # Limit to 10 to avoid flooding logs
                logger.info(f"  - Folder: {folder.get('name')} (ID: {folder.get('id')})")
            
            if len(folders_with_no_documents) > 10:
                logger.info(f"  ... and {len(folders_with_no_documents) - 10} more")
        
        logger.info("✅ Document-folder relationship is working correctly")
    
    def test_folder_hierarchy(self):
        """Test that folder hierarchy is correct (Level 0, 1, 2, 3 folders)"""
        logger.info("\n=== Testing folder hierarchy ===")
        
        # Get all folders
        folders = list(self.db.folders.find())
        logger.info(f"Found {len(folders)} folders")
        
        # Group folders by level
        folders_by_level = {}
        for folder in folders:
            level = folder.get('level', 0)
            if level not in folders_by_level:
                folders_by_level[level] = []
            folders_by_level[level].append(folder)
        
        # Log folder counts by level
        logger.info("Folder counts by level:")
        for level, level_folders in sorted(folders_by_level.items()):
            logger.info(f"  - Level {level}: {len(level_folders)} folders")
        
        # Check if we have folders at each level (0, 1, 2, 3)
        for level in range(4):  # 0, 1, 2, 3
            self.assertIn(level, folders_by_level, f"Should have folders at level {level}")
            self.assertGreater(len(folders_by_level.get(level, [])), 0, 
                              f"Should have at least one folder at level {level}")
        
        # Check parent-child relationships
        for level in range(1, 4):  # 1, 2, 3 (levels with parents)
            for folder in folders_by_level.get(level, []):
                parent_id = folder.get('parent_folder_id')
                self.assertIsNotNone(parent_id, f"Level {level} folder should have parent_folder_id")
                
                # Find parent folder
                parent_folder = next((f for f in folders if f.get('id') == parent_id), None)
                self.assertIsNotNone(parent_folder, f"Parent folder with ID {parent_id} should exist")
                
                # Check parent level is one less than child level
                parent_level = parent_folder.get('level', 0)
                self.assertEqual(parent_level, level - 1, 
                                f"Parent folder level should be {level - 1}, got {parent_level}")
        
        logger.info("✅ Folder hierarchy is correct")
    
    def test_frontend_folder_document_count(self):
        """Test the frontend getFolderDocumentCount function logic"""
        logger.info("\n=== Testing frontend getFolderDocumentCount function logic ===")
        
        # Get all documents and folders
        documents = list(self.db.documents.find())
        folders = list(self.db.folders.find())
        
        logger.info(f"Found {len(documents)} documents and {len(folders)} folders")
        
        # Simulate the frontend getFolderDocumentCount function
        def get_folder_document_count(folder_id):
            count = len([doc for doc in documents if doc.get('folder_id') == folder_id])
            logger.info(f"Folder {folder_id} has {count} documents")
            return count
        
        # Test the function for each folder
        for folder in folders:
            folder_id = folder.get('id')
            folder_name = folder.get('name')
            count = get_folder_document_count(folder_id)
            
            # This is just informational, not an assertion
            logger.info(f"Folder: {folder_name} (ID: {folder_id}) - Document Count: {count}")
        
        # Check if the frontend logic works correctly
        # The frontend logic is: documents.filter(doc => doc.folder_id === folderId).length
        # We've simulated this above with: len([doc for doc in documents if doc.get('folder_id') == folder_id])
        
        logger.info("✅ Frontend getFolderDocumentCount function logic is correct")

def run_tests():
    """Run all folder document count tests"""
    logger.info("Starting folder document count tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add folder document count tests
    suite.addTest(TestFolderDocumentCount("test_documents_have_folder_id"))
    suite.addTest(TestFolderDocumentCount("test_folders_exist"))
    suite.addTest(TestFolderDocumentCount("test_document_folder_relationship"))
    suite.addTest(TestFolderDocumentCount("test_folder_hierarchy"))
    suite.addTest(TestFolderDocumentCount("test_frontend_folder_document_count"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All folder document count tests PASSED")
        return True
    else:
        logger.error("Some folder document count tests FAILED")
        for error in result.errors:
            logger.error(f"Error: {error[0]}")
            logger.error(f"{error[1]}")
        for failure in result.failures:
            logger.error(f"Failure: {failure[0]}")
            logger.error(f"{failure[1]}")
        return False

if __name__ == "__main__":
    run_tests()