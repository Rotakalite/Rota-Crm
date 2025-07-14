import unittest
import logging
import requests
import pymongo
from bson import ObjectId
import gridfs
import io
import os
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API URL
API_URL = "https://4ee1e29f-eceb-4966-ad56-8377a758d2bb.preview.emergentagent.com/api"

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "rotacrm"

# Test JWT token
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

class TestDocumentDownloadIssue(unittest.TestCase):
    """Test class for document download issue"""
    
    def setUp(self):
        """Set up test environment"""
        # Connect to MongoDB
        self.mongo_client = pymongo.MongoClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        self.fs = gridfs.GridFS(self.db)
        
        # Headers for authentication
        self.headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        
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
            logger.info(f"Using existing client ID: {self.test_client_id}")
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
            logger.info(f"Created test client with ID: {self.test_client_id}")
        
        # Get a folder ID for the client
        self.test_folder_id = None
        folders = list(self.db.folders.find({"client_id": self.test_client_id}, {"id": 1}).limit(1))
        if folders:
            self.test_folder_id = folders[0]["id"]
            logger.info(f"Using existing folder ID: {self.test_folder_id}")
        else:
            logger.warning("No folders found for the client. Creating a test folder.")
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
            logger.info(f"Created test folder with ID: {self.test_folder_id}")
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove the test PDF file
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
        
        # Close MongoDB connection
        if hasattr(self, 'mongo_client'):
            self.mongo_client.close()
    
    def test_upload_download_workflow(self):
        """Test the complete upload-download workflow"""
        logger.info("\n=== Testing upload-download workflow ===")
        
        try:
            # Step 1: Upload a PDF file
            logger.info("Step 1: Uploading a PDF file...")
            
            upload_url = f"{API_URL}/upload-document"
            
            with open(self.test_pdf_path, "rb") as f:
                files = {
                    'file': ('test_document.pdf', f, 'application/pdf')
                }
                
                data = {
                    'client_id': self.test_client_id,
                    'folder_id': self.test_folder_id,
                    'document_name': 'Test PDF Document',
                    'document_type': 'CARBON_REPORT',
                    'stage': 'I.Aşama'
                }
                
                response = requests.post(upload_url, headers=self.headers, files=files, data=data)
                logger.info(f"Upload response status code: {response.status_code}")
                
                # Upload should return 200 OK
                self.assertEqual(response.status_code, 200)
                
                # Get the document ID from the response
                upload_data = response.json()
                self.assertIn("document_id", upload_data)
                
                document_id = upload_data["document_id"]
                logger.info(f"Uploaded document ID: {document_id}")
            
            # Step 2: Verify the document was created in the database
            logger.info("Step 2: Verifying document in database...")
            
            document = self.db.documents.find_one({"id": document_id})
            self.assertIsNotNone(document)
            self.assertEqual(document["name"], "Test PDF Document")
            self.assertEqual(document["document_type"], "CARBON_REPORT")
            self.assertEqual(document["stage"], "I.Aşama")
            
            # Check if the document has a gridfs_id field
            self.assertIn("gridfs_id", document)
            self.assertIsNotNone(document["gridfs_id"])
            
            gridfs_id = document["gridfs_id"]
            logger.info(f"Document has GridFS ID: {gridfs_id}")
            
            # Step 3: Verify the file was stored in GridFS
            logger.info("Step 3: Verifying file in GridFS...")
            
            file_id_obj = ObjectId(gridfs_id)
            self.assertTrue(self.fs.exists(file_id_obj))
            
            grid_file = self.fs.get(file_id_obj)
            self.assertIsNotNone(grid_file)
            
            # Check file metadata
            self.assertEqual(grid_file.filename, "test_document.pdf")
            self.assertEqual(grid_file.content_type, "application/pdf")
            
            # Check file content
            content = grid_file.read()
            self.assertGreater(len(content), 0)
            self.assertTrue(content.startswith(b"%PDF-"))
            
            logger.info(f"GridFS file info: filename={grid_file.filename}, content_type={grid_file.content_type}, length={grid_file.length}")
            
            # Step 4: Download the document
            logger.info("Step 4: Downloading the document...")
            
            download_url = f"{API_URL}/documents/{document_id}/download"
            
            response = requests.get(download_url, headers=self.headers)
            logger.info(f"Download response status code: {response.status_code}")
            
            # Download should return 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Check content type
            content_type = response.headers.get("Content-Type")
            logger.info(f"Content-Type: {content_type}")
            self.assertEqual(content_type, "application/pdf")
            
            # Check content disposition
            content_disposition = response.headers.get("Content-Disposition")
            logger.info(f"Content-Disposition: {content_disposition}")
            self.assertIn("attachment", content_disposition)
            
            # Check content length
            content_length = response.headers.get("Content-Length")
            logger.info(f"Content-Length: {content_length}")
            self.assertIsNotNone(content_length)
            
            # Get the content
            downloaded_content = response.content
            
            # Check if content is a PDF (starts with %PDF)
            is_pdf = downloaded_content.startswith(b"%PDF-")
            logger.info(f"Is PDF: {is_pdf}")
            self.assertTrue(is_pdf, "Downloaded content should be a PDF")
            
            # Check if content is text (contains placeholder text)
            is_placeholder = b"This is a placeholder document content" in downloaded_content
            logger.info(f"Is Placeholder: {is_placeholder}")
            self.assertFalse(is_placeholder, "Downloaded content should not be a placeholder")
            
            # Compare with original content
            with open(self.test_pdf_path, "rb") as f:
                original_content = f.read()
            
            self.assertEqual(downloaded_content, original_content, "Downloaded content should match original content")
            
            logger.info("✅ Upload-download workflow test passed")
        except Exception as e:
            logger.error(f"❌ Error testing upload-download workflow: {str(e)}")
            raise
    
    def test_existing_documents(self):
        """Test downloading existing documents"""
        logger.info("\n=== Testing existing documents ===")
        
        try:
            # Step 1: Get a list of existing documents
            logger.info("Step 1: Getting list of existing documents...")
            
            list_url = f"{API_URL}/documents"
            
            response = requests.get(list_url, headers=self.headers)
            logger.info(f"List response status code: {response.status_code}")
            
            # List should return 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Get the documents from the response
            documents = response.json()
            self.assertIsInstance(documents, list)
            
            logger.info(f"Found {len(documents)} documents")
            
            if not documents:
                logger.warning("No existing documents found, skipping test")
                return
            
            # Step 2: Download each document and check if it's a PDF
            logger.info("Step 2: Downloading and checking each document...")
            
            for i, doc in enumerate(documents[:5]):  # Test first 5 documents
                document_id = doc["id"]
                document_title = doc["title"]
                logger.info(f"Testing document {i+1}: ID={document_id}, Title={document_title}")
                
                # Download the document
                download_url = f"{API_URL}/documents/{document_id}/download"
                
                response = requests.get(download_url, headers=self.headers)
                logger.info(f"Download response status code: {response.status_code}")
                
                # Download should return 200 OK
                self.assertEqual(response.status_code, 200)
                
                # Check content type
                content_type = response.headers.get("Content-Type")
                logger.info(f"Content-Type: {content_type}")
                
                # Check content disposition
                content_disposition = response.headers.get("Content-Disposition")
                logger.info(f"Content-Disposition: {content_disposition}")
                
                # Get the content
                content = response.content
                
                # Check if content is a PDF (starts with %PDF)
                is_pdf = content.startswith(b"%PDF-")
                logger.info(f"Is PDF: {is_pdf}")
                
                # Check if content is text (contains placeholder text)
                is_placeholder = b"This is a placeholder document content" in content
                logger.info(f"Is Placeholder: {is_placeholder}")
                
                # Verify content is not a placeholder
                self.assertFalse(is_placeholder, f"Document {document_id} content should not be a placeholder")
                
                # For PDF documents, verify content starts with PDF header
                if content_type == "application/pdf":
                    self.assertTrue(is_pdf, f"Document {document_id} with content type application/pdf should start with %PDF")
                
                # Check if the document has a gridfs_id field in the database
                db_doc = self.db.documents.find_one({"id": document_id})
                if db_doc:
                    logger.info(f"Document in database: {db_doc.get('name')}")
                    
                    if "gridfs_id" in db_doc:
                        gridfs_id = db_doc["gridfs_id"]
                        logger.info(f"Document has GridFS ID: {gridfs_id}")
                        
                        # Verify the file exists in GridFS
                        try:
                            file_id_obj = ObjectId(gridfs_id)
                            exists = self.fs.exists(file_id_obj)
                            logger.info(f"File exists in GridFS: {exists}")
                            
                            if exists:
                                # Get the file from GridFS
                                grid_file = self.fs.get(file_id_obj)
                                
                                # Check file metadata
                                logger.info(f"GridFS file info: filename={grid_file.filename}, content_type={grid_file.content_type}, length={grid_file.length}")
                                
                                # Read the file content
                                gridfs_content = grid_file.read()
                                
                                # Compare with downloaded content
                                content_matches = gridfs_content == content
                                logger.info(f"GridFS content matches downloaded content: {content_matches}")
                                
                                self.assertTrue(content_matches, f"Document {document_id} GridFS content should match downloaded content")
                        except Exception as e:
                            logger.error(f"Error checking GridFS for document {document_id}: {str(e)}")
                    else:
                        logger.warning(f"Document {document_id} does not have a gridfs_id field")
                else:
                    logger.warning(f"Document {document_id} not found in database")
            
            logger.info("✅ Existing documents test passed")
        except Exception as e:
            logger.error(f"❌ Error testing existing documents: {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main()