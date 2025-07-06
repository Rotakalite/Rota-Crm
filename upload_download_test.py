import unittest
import logging
import requests
import os
import io
import uuid
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import gridfs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL - use the local backend for direct testing
BACKEND_URL = "http://localhost:8001/api"

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "rotacrm"

class TestDocumentUploadDownload(unittest.TestCase):
    """Test class for document upload and download functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Connect to MongoDB
        self.mongo_client = MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        self.fs = gridfs.GridFS(self.db)
        
        # Create a test PDF file
        self.test_pdf_path = "/tmp/test_document.pdf"
        with open(self.test_pdf_path, "wb") as f:
            # Write a simple PDF file
            f.write(b"%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF")
        
        # Get a test client ID
        self.test_client_id = None
        clients = list(self.db.clients.find({}, {"id": 1}).limit(1))
        if clients:
            self.test_client_id = clients[0]["id"]
        else:
            logger.warning("No clients found in the database. Creating a test client.")
            # Create a test client
            client_id = str(uuid.uuid4())
            self.db.clients.insert_one({
                "id": client_id,
                "name": "Test Client",
                "hotel_name": "Test Hotel",
                "contact_person": "Test Person",
                "email": "test@example.com",
                "phone": "1234567890",
                "address": "Test Address",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            self.test_client_id = client_id
        
        # Get a test folder ID
        self.test_folder_id = None
        folders = list(self.db.folders.find({"client_id": self.test_client_id}, {"id": 1}).limit(1))
        if folders:
            self.test_folder_id = folders[0]["id"]
        else:
            logger.warning("No folders found for the test client. Creating a test folder.")
            # Create a test folder
            folder_id = str(uuid.uuid4())
            self.db.folders.insert_one({
                "id": folder_id,
                "client_id": self.test_client_id,
                "name": "Test Folder",
                "parent_folder_id": None,
                "folder_path": "Test Folder",
                "level": 0,
                "created_at": datetime.utcnow()
            })
            self.test_folder_id = folder_id
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove the test PDF file
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
    
    def test_document_upload_and_download(self):
        """Test document upload and download functionality"""
        logger.info("\n=== Testing document upload and download functionality ===")
        
        # Step 1: Upload a document
        logger.info("Step 1: Uploading a document...")
        
        # Prepare the upload data
        document_name = f"Test Document {uuid.uuid4()}"
        document_type = "STAGE_1_DOC"
        stage = "I.Aşama"
        
        # Create the multipart form data
        files = {
            "file": ("test_document.pdf", open(self.test_pdf_path, "rb"), "application/pdf")
        }
        data = {
            "client_id": self.test_client_id,
            "folder_id": self.test_folder_id,
            "document_name": document_name,
            "document_type": document_type,
            "stage": stage
        }
        
        # Upload the document
        upload_url = f"{BACKEND_URL}/upload-document"
        try:
            upload_response = requests.post(upload_url, files=files, data=data)
            logger.info(f"Upload response status code: {upload_response.status_code}")
            logger.info(f"Upload response: {upload_response.text}")
            
            # Check if the upload was successful
            self.assertIn(upload_response.status_code, [200, 201])
            
            # Parse the response
            upload_data = upload_response.json()
            self.assertIn("document_id", upload_data)
            
            document_id = upload_data["document_id"]
            logger.info(f"Uploaded document with ID: {document_id}")
            
            # Step 2: Verify the document was saved in the database with a GridFS ID
            logger.info("Step 2: Verifying document in database...")
            
            document = self.db.documents.find_one({"id": document_id})
            self.assertIsNotNone(document)
            self.assertEqual(document["name"], document_name)
            self.assertEqual(document["document_type"], document_type)
            self.assertEqual(document["stage"], stage)
            self.assertIn("gridfs_id", document)
            self.assertIsNotNone(document["gridfs_id"])
            
            gridfs_id = document["gridfs_id"]
            logger.info(f"Document has GridFS ID: {gridfs_id}")
            
            # Step 3: Verify the file exists in GridFS
            logger.info("Step 3: Verifying file in GridFS...")
            
            file_id = ObjectId(gridfs_id)
            self.assertTrue(self.fs.exists(file_id))
            
            grid_file = self.fs.get(file_id)
            self.assertIsNotNone(grid_file)
            
            # Check file content
            content = grid_file.read()
            self.assertGreater(len(content), 0)
            self.assertTrue(content.startswith(b"%PDF-"))
            
            logger.info(f"GridFS file info: filename={grid_file.filename}, content_type={grid_file.content_type}, length={grid_file.length}")
            
            # Step 4: Download the document
            logger.info("Step 4: Downloading the document...")
            
            download_url = f"{BACKEND_URL}/documents/{document_id}/download"
            download_response = requests.get(download_url)
            logger.info(f"Download response status code: {download_response.status_code}")
            
            # Check if the download was successful
            self.assertEqual(download_response.status_code, 200)
            
            # Check content type
            content_type = download_response.headers.get("Content-Type", "")
            logger.info(f"Content-Type: {content_type}")
            self.assertIn(content_type, ["application/octet-stream", "application/pdf"])
            
            # Check Content-Disposition header
            content_disposition = download_response.headers.get("Content-Disposition", "")
            logger.info(f"Content-Disposition: {content_disposition}")
            self.assertIn("attachment", content_disposition)
            
            # Check content length
            content_length = int(download_response.headers.get("Content-Length", "0"))
            logger.info(f"Content-Length: {content_length}")
            self.assertGreater(content_length, 0)
            
            # Check content
            download_content = download_response.content
            self.assertGreater(len(download_content), 0)
            
            # Check if content is NOT a placeholder text file
            self.assertNotIn(b"This is a placeholder document content", download_content)
            
            # Check if content is a PDF file
            self.assertTrue(download_content.startswith(b"%PDF-"))
            
            # Compare the downloaded content with the original GridFS content
            self.assertEqual(download_content, content)
            
            logger.info("✅ Document upload and download test passed")
        except Exception as e:
            logger.error(f"❌ Error testing document upload and download: {str(e)}")
            raise

def run_tests():
    """Run all tests"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add document upload and download tests
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestDocumentUploadDownload))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == "__main__":
    run_tests()