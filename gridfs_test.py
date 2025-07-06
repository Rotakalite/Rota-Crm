import unittest
import logging
import os
import uuid
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

class TestGridFSIntegration(unittest.TestCase):
    """Test class for GridFS integration"""
    
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
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove the test PDF file
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
    
    def test_gridfs_store_and_retrieve(self):
        """Test storing and retrieving files from GridFS"""
        logger.info("\n=== Testing GridFS store and retrieve functionality ===")
        
        # Step 1: Store a file in GridFS
        logger.info("Step 1: Storing a file in GridFS...")
        
        with open(self.test_pdf_path, "rb") as f:
            file_content = f.read()
        
        # Store file in GridFS
        file_id = self.fs.put(
            file_content,
            filename="test_document.pdf",
            content_type="application/pdf",
            metadata={
                "document_id": str(uuid.uuid4()),
                "client_id": self.test_client_id,
                "document_name": "Test Document",
                "document_type": "STAGE_1_DOC",
                "stage": "I.Aşama"
            }
        )
        
        logger.info(f"Stored file in GridFS with ID: {file_id}")
        
        # Step 2: Create a document record in the database
        logger.info("Step 2: Creating a document record in the database...")
        
        document_id = str(uuid.uuid4())
        document_data = {
            "id": document_id,
            "client_id": self.test_client_id,
            "name": "Test Document",
            "document_name": "Test Document",
            "document_type": "STAGE_1_DOC",
            "stage": "I.Aşama",
            "filename": "test_document.pdf",
            "content_type": "application/pdf",
            "file_size": len(file_content),
            "original_filename": "test_document.pdf",
            "uploaded_by": "test_user",
            "created_at": datetime.utcnow(),
            "folder_id": "",
            "folder_path": "",
            "folder_level": 0,
            "gridfs_id": str(file_id)  # Store GridFS file ID
        }
        
        self.db.documents.insert_one(document_data)
        logger.info(f"Created document record with ID: {document_id}")
        
        # Step 3: Retrieve the document record from the database
        logger.info("Step 3: Retrieving the document record from the database...")
        
        document = self.db.documents.find_one({"id": document_id})
        self.assertIsNotNone(document)
        self.assertEqual(document["name"], "Test Document")
        self.assertEqual(document["document_type"], "STAGE_1_DOC")
        self.assertEqual(document["stage"], "I.Aşama")
        self.assertIn("gridfs_id", document)
        self.assertIsNotNone(document["gridfs_id"])
        
        gridfs_id = document["gridfs_id"]
        logger.info(f"Document has GridFS ID: {gridfs_id}")
        
        # Step 4: Retrieve the file from GridFS
        logger.info("Step 4: Retrieving the file from GridFS...")
        
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
        
        # Compare with original content
        self.assertEqual(content, file_content)
        
        logger.info(f"GridFS file info: filename={grid_file.filename}, content_type={grid_file.content_type}, length={grid_file.length}")
        logger.info("✅ GridFS store and retrieve test passed")
    
    def test_document_date_formatting(self):
        """Test document date formatting"""
        logger.info("\n=== Testing document date formatting ===")
        
        # Create a document with a created_at date
        document_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        document_data = {
            "id": document_id,
            "client_id": self.test_client_id,
            "name": "Test Document for Date Formatting",
            "document_type": "STAGE_1_DOC",
            "stage": "I.Aşama",
            "created_at": created_at,
            "updated_at": created_at
        }
        
        self.db.documents.insert_one(document_data)
        logger.info(f"Created document with ID: {document_id} and created_at: {created_at.isoformat()}")
        
        # Retrieve the document
        document = self.db.documents.find_one({"id": document_id})
        self.assertIsNotNone(document)
        
        # Check that created_at is a datetime object
        self.assertIsInstance(document["created_at"], datetime)
        
        # Format the date as ISO string
        iso_date = document["created_at"].isoformat()
        logger.info(f"Document created_at as ISO string: {iso_date}")
        
        # Format the date as a string with the safe date formatting function
        # This is a simplified version of what would be in the frontend
        def safe_format_date(date_obj):
            if not date_obj:
                return ""
            try:
                if isinstance(date_obj, str):
                    # Try to parse the string as a date
                    date_obj = datetime.fromisoformat(date_obj.replace("Z", "+00:00"))
                return date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return ""
        
        formatted_date = safe_format_date(document["created_at"])
        logger.info(f"Document created_at with safe formatting: {formatted_date}")
        
        # Check that the formatted date is not empty
        self.assertNotEqual(formatted_date, "")
        
        # Check that the formatted date is not "Invalid Date"
        self.assertNotEqual(formatted_date, "Invalid Date")
        
        logger.info("✅ Document date formatting test passed")
    
    def test_training_name_field(self):
        """Test training name field"""
        logger.info("\n=== Testing training name field ===")
        
        # Create a training with only name field
        training_id_1 = str(uuid.uuid4())
        training_name = f"Test Training with Name Field {uuid.uuid4()}"
        
        training_data_1 = {
            "id": training_id_1,
            "client_id": self.test_client_id,
            "name": training_name,
            "subject": "Test Subject",
            "participant_count": 10,
            "trainer": "Test Trainer",
            "training_date": datetime.utcnow(),
            "description": "Test training created with name field",
            "status": "planned",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        self.db.trainings.insert_one(training_data_1)
        logger.info(f"Created training with ID: {training_id_1} and name: {training_name}")
        
        # Create a training with only title field
        training_id_2 = str(uuid.uuid4())
        training_title = f"Test Training with Title Field {uuid.uuid4()}"
        
        training_data_2 = {
            "id": training_id_2,
            "client_id": self.test_client_id,
            "title": training_title,
            "subject": "Test Subject",
            "participant_count": 10,
            "trainer": "Test Trainer",
            "training_date": datetime.utcnow(),
            "description": "Test training created with title field",
            "status": "planned",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        self.db.trainings.insert_one(training_data_2)
        logger.info(f"Created training with ID: {training_id_2} and title: {training_title}")
        
        # Create a training with both name and title fields
        training_id_3 = str(uuid.uuid4())
        training_name_3 = f"Test Training Name {uuid.uuid4()}"
        training_title_3 = f"Test Training Title {uuid.uuid4()}"
        
        training_data_3 = {
            "id": training_id_3,
            "client_id": self.test_client_id,
            "name": training_name_3,
            "title": training_title_3,
            "subject": "Test Subject",
            "participant_count": 10,
            "trainer": "Test Trainer",
            "training_date": datetime.utcnow(),
            "description": "Test training created with both name and title fields",
            "status": "planned",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        self.db.trainings.insert_one(training_data_3)
        logger.info(f"Created training with ID: {training_id_3}, name: {training_name_3}, and title: {training_title_3}")
        
        # Retrieve the trainings
        training_1 = self.db.trainings.find_one({"id": training_id_1})
        training_2 = self.db.trainings.find_one({"id": training_id_2})
        training_3 = self.db.trainings.find_one({"id": training_id_3})
        
        self.assertIsNotNone(training_1)
        self.assertIsNotNone(training_2)
        self.assertIsNotNone(training_3)
        
        # Check training 1 (name only)
        self.assertIn("name", training_1)
        self.assertEqual(training_1["name"], training_name)
        self.assertNotIn("title", training_1)
        
        # Check training 2 (title only)
        self.assertIn("title", training_2)
        self.assertEqual(training_2["title"], training_title)
        self.assertNotIn("name", training_2)
        
        # Check training 3 (both name and title)
        self.assertIn("name", training_3)
        self.assertEqual(training_3["name"], training_name_3)
        self.assertIn("title", training_3)
        self.assertEqual(training_3["title"], training_title_3)
        
        # Test the frontend logic for displaying training title
        def get_display_title(training):
            return training.get("title") or training.get("name") or "Unknown Training"
        
        # Training 1 should use name as display title
        display_title_1 = get_display_title(training_1)
        self.assertEqual(display_title_1, training_name)
        logger.info(f"Training 1 display title: {display_title_1}")
        
        # Training 2 should use title as display title
        display_title_2 = get_display_title(training_2)
        self.assertEqual(display_title_2, training_title)
        logger.info(f"Training 2 display title: {display_title_2}")
        
        # Training 3 should use title as display title (title takes precedence)
        display_title_3 = get_display_title(training_3)
        self.assertEqual(display_title_3, training_title_3)
        logger.info(f"Training 3 display title: {display_title_3}")
        
        logger.info("✅ Training name field test passed")

def run_tests():
    """Run all tests"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add GridFS integration tests
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestGridFSIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == "__main__":
    run_tests()