import unittest
import json
import logging
import requests
import os
import io
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestFolderDocumentCount(unittest.TestCase):
    """Test class for folder document count functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://36a5b90e-f3d9-4915-ab44-784415b46fb6.preview.emergentagent.com')
        self.api_url = f"{self.api_url}/api"
        self.headers_valid = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
        
    def test_documents_have_folder_id(self):
        """Test that documents in the database have valid folder_id fields"""
        logger.info("\n=== Testing documents have valid folder_id fields ===")
        
        # Get all documents
        url = f"{self.api_url}/documents"
        
        try:
            response = requests.get(url, headers=self.headers_valid)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                documents = response.json()
                logger.info(f"Found {len(documents)} documents")
                
                # Check if documents have folder_id
                documents_with_folder_id = [doc for doc in documents if doc.get('folder_id')]
                documents_without_folder_id = [doc for doc in documents if not doc.get('folder_id')]
                
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
                invalid_folder_ids = [doc for doc in documents if doc.get('folder_id') == ""]
                logger.info(f"Documents with empty folder_id: {len(invalid_folder_ids)}")
                
                if invalid_folder_ids:
                    logger.warning("Documents with empty folder_id:")
                    for doc in invalid_folder_ids:
                        logger.warning(f"  - Document ID: {doc.get('id')}, Name: {doc.get('name')}")
                
                self.assertEqual(len(invalid_folder_ids), 0, 
                                "No documents should have empty folder_id")
                
                logger.info("✅ All documents have valid folder_id fields")
            else:
                logger.error(f"Failed to get documents: {response.status_code}")
                self.fail(f"Failed to get documents: {response.status_code}")
        except Exception as e:
            logger.error(f"Error testing documents have folder_id: {str(e)}")
            self.fail(f"Error testing documents have folder_id: {str(e)}")
    
    def test_folders_exist(self):
        """Test that folders exist with proper ids"""
        logger.info("\n=== Testing folders exist with proper ids ===")
        
        # Get all folders
        url = f"{self.api_url}/folders"
        
        try:
            response = requests.get(url, headers=self.headers_valid)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                folders = response.json()
                logger.info(f"Found {len(folders)} folders")
                
                # Check if folders have id
                folders_with_id = [folder for folder in folders if folder.get('id')]
                folders_without_id = [folder for folder in folders if not folder.get('id')]
                
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
                invalid_ids = [folder for folder in folders if folder.get('id') == ""]
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
            else:
                logger.error(f"Failed to get folders: {response.status_code}")
                self.fail(f"Failed to get folders: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error testing folders exist: {str(e)}")
            self.fail(f"Error testing folders exist: {str(e)}")
            return []
    
    def test_document_folder_relationship(self):
        """Test that the relationship between documents and folders is working"""
        logger.info("\n=== Testing document-folder relationship ===")
        
        # Get all documents
        documents_url = f"{self.api_url}/documents"
        folders_url = f"{self.api_url}/folders"
        
        try:
            # Get documents
            documents_response = requests.get(documents_url, headers=self.headers_valid)
            logger.info(f"Documents response status code: {documents_response.status_code}")
            
            # Get folders
            folders_response = requests.get(folders_url, headers=self.headers_valid)
            logger.info(f"Folders response status code: {folders_response.status_code}")
            
            if documents_response.status_code == 200 and folders_response.status_code == 200:
                documents = documents_response.json()
                folders = folders_response.json()
                
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
                    logger.info("Folders with no documents:")
                    for folder in folders_with_no_documents[:10]:  # Limit to 10 to avoid flooding logs
                        logger.info(f"  - Folder: {folder.get('name')} (ID: {folder.get('id')})")
                    
                    if len(folders_with_no_documents) > 10:
                        logger.info(f"  ... and {len(folders_with_no_documents) - 10} more")
                
                logger.info("✅ Document-folder relationship is working correctly")
            else:
                if documents_response.status_code != 200:
                    logger.error(f"Failed to get documents: {documents_response.status_code}")
                if folders_response.status_code != 200:
                    logger.error(f"Failed to get folders: {folders_response.status_code}")
                self.fail("Failed to get documents or folders")
        except Exception as e:
            logger.error(f"Error testing document-folder relationship: {str(e)}")
            self.fail(f"Error testing document-folder relationship: {str(e)}")
    
    def test_folder_hierarchy(self):
        """Test that folder hierarchy is correct (Level 0, 1, 2, 3 folders)"""
        logger.info("\n=== Testing folder hierarchy ===")
        
        # Get all folders
        url = f"{self.api_url}/folders"
        
        try:
            response = requests.get(url, headers=self.headers_valid)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                folders = response.json()
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
            else:
                logger.error(f"Failed to get folders: {response.status_code}")
                self.fail(f"Failed to get folders: {response.status_code}")
        except Exception as e:
            logger.error(f"Error testing folder hierarchy: {str(e)}")
            self.fail(f"Error testing folder hierarchy: {str(e)}")

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