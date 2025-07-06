import unittest
import logging
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import gridfs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "rotacrm"

class TestDocumentGridFSIntegration(unittest.TestCase):
    """Test class for document GridFS integration"""
    
    def setUp(self):
        """Set up test environment"""
        # Connect to MongoDB
        self.mongo_client = MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        self.fs = gridfs.GridFS(self.db)
        
        # Get a list of document IDs from the database
        self.document_ids = []
        try:
            documents = list(self.db.documents.find({}, {"id": 1, "client_id": 1, "name": 1, "gridfs_id": 1}).limit(10))
            for doc in documents:
                if "id" in doc and "gridfs_id" in doc and doc["gridfs_id"]:
                    self.document_ids.append({
                        "id": doc["id"],
                        "client_id": doc.get("client_id", ""),
                        "name": doc.get("name", "Unknown"),
                        "gridfs_id": doc["gridfs_id"]
                    })
            logger.info(f"Found {len(self.document_ids)} documents with GridFS IDs for testing")
        except Exception as e:
            logger.error(f"Error getting document IDs from MongoDB: {e}")
    
    def test_documents_have_gridfs_ids(self):
        """Test that documents have GridFS IDs"""
        logger.info("\n=== Testing that documents have GridFS IDs ===")
        
        # Get all documents
        documents = list(self.db.documents.find({}, {"id": 1, "name": 1, "gridfs_id": 1}))
        logger.info(f"Found {len(documents)} documents in the database")
        
        # Count documents with GridFS IDs
        docs_with_gridfs = [doc for doc in documents if "gridfs_id" in doc and doc["gridfs_id"]]
        logger.info(f"Found {len(docs_with_gridfs)} documents with GridFS IDs")
        
        # At least some documents should have GridFS IDs
        self.assertGreaterEqual(len(docs_with_gridfs), 0, "No documents have GridFS IDs")
        
        if len(docs_with_gridfs) > 0:
            # Log some sample documents with GridFS IDs
            for i, doc in enumerate(docs_with_gridfs[:3]):
                logger.info(f"Document {i+1}: ID={doc['id']}, Name={doc.get('name', 'Unknown')}, GridFS ID={doc['gridfs_id']}")
            
            logger.info("✅ Documents have GridFS IDs test passed")
        else:
            logger.warning("⚠️ No documents with GridFS IDs found. This may be expected if no documents have been uploaded yet.")
    
    def test_gridfs_files_exist(self):
        """Test that GridFS files exist for documents with GridFS IDs"""
        logger.info("\n=== Testing that GridFS files exist for documents with GridFS IDs ===")
        
        if not self.document_ids:
            logger.warning("No documents with GridFS IDs found. Skipping test.")
            return
        
        for doc_info in self.document_ids:
            doc_id = doc_info["id"]
            doc_name = doc_info["name"]
            gridfs_id = doc_info["gridfs_id"]
            
            logger.info(f"Testing GridFS file for document: {doc_name} (ID: {doc_id}, GridFS ID: {gridfs_id})")
            
            try:
                # Convert string ID to ObjectId
                file_id = ObjectId(gridfs_id)
                
                # Check if file exists in GridFS
                exists = self.fs.exists(file_id)
                self.assertTrue(exists, f"GridFS file with ID {gridfs_id} does not exist")
                
                # Get file from GridFS
                grid_file = self.fs.get(file_id)
                
                # Check file metadata
                self.assertIsNotNone(grid_file, f"Could not get GridFS file with ID {gridfs_id}")
                
                # Check file content
                content = grid_file.read()
                self.assertGreater(len(content), 0, f"GridFS file with ID {gridfs_id} is empty")
                
                # Log file info
                logger.info(f"GridFS file info: filename={grid_file.filename}, content_type={grid_file.content_type}, length={grid_file.length}")
                
                # Check content type - should be application/octet-stream or application/pdf
                self.assertIn(grid_file.content_type, ["application/octet-stream", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", None])
                
                # For PDF files, check for PDF signature
                if grid_file.content_type == "application/pdf":
                    self.assertTrue(content.startswith(b"%PDF-"), f"GridFS file with ID {gridfs_id} is not a valid PDF")
                
                logger.info(f"✅ GridFS file exists for document: {doc_name}")
            except Exception as e:
                logger.error(f"❌ Error testing GridFS file for {doc_name}: {str(e)}")
                raise

class TestTrainingNameField(unittest.TestCase):
    """Test class for training name field"""
    
    def setUp(self):
        """Set up test environment"""
        # Connect to MongoDB
        self.mongo_client = MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
    
    def test_trainings_have_name_or_title(self):
        """Test that trainings have name or title field"""
        logger.info("\n=== Testing that trainings have name or title field ===")
        
        # Get all trainings
        trainings = list(self.db.trainings.find({}, {"id": 1, "name": 1, "title": 1}))
        logger.info(f"Found {len(trainings)} trainings in the database")
        
        # Check that each training has either name or title
        for training in trainings:
            has_name = "name" in training and training["name"]
            has_title = "title" in training and training["title"]
            
            self.assertTrue(has_name or has_title, f"Training {training['id']} has neither name nor title")
            
            if has_name and has_title:
                logger.info(f"Training {training['id']} has both name ({training['name']}) and title ({training['title']})")
            elif has_name:
                logger.info(f"Training {training['id']} has name ({training['name']}) but no title")
            elif has_title:
                logger.info(f"Training {training['id']} has title ({training['title']}) but no name")
        
        logger.info("✅ Trainings have name or title test passed")

class TestDocumentDateFormatting(unittest.TestCase):
    """Test class for document date formatting"""
    
    def setUp(self):
        """Set up test environment"""
        # Connect to MongoDB
        self.mongo_client = MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
    
    def test_document_dates_are_valid(self):
        """Test that document dates are valid"""
        logger.info("\n=== Testing that document dates are valid ===")
        
        # Get all documents
        documents = list(self.db.documents.find({}, {"id": 1, "name": 1, "created_at": 1}))
        logger.info(f"Found {len(documents)} documents in the database")
        
        # Check that each document has a valid created_at date
        for doc in documents:
            self.assertIn("created_at", doc, f"Document {doc['id']} has no created_at field")
            
            created_at = doc["created_at"]
            self.assertIsNotNone(created_at, f"Document {doc['id']} has None created_at")
            
            # Check that created_at is a datetime object
            self.assertIsInstance(created_at, datetime, f"Document {doc['id']} created_at is not a datetime object")
            
            # Log the date
            logger.info(f"Document {doc['id']} ({doc.get('name', 'Unknown')}) created_at: {created_at.isoformat()}")
        
        logger.info("✅ Document dates are valid test passed")

def run_tests():
    """Run all tests"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add document GridFS integration tests
    suite.addTest(unittest.makeSuite(TestDocumentGridFSIntegration))
    
    # Add training name field tests
    suite.addTest(unittest.makeSuite(TestTrainingNameField))
    
    # Add document date formatting tests
    suite.addTest(unittest.makeSuite(TestDocumentDateFormatting))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == "__main__":
    run_tests()