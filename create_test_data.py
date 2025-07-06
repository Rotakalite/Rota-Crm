import os
import sys
import json
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
db_name = "sustainable_tourism_crm"

async def create_test_data():
    """Create test data in the database"""
    logger.info("\n=== Creating test data in database ===")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Check if clients collection exists
        collections = await db.list_collection_names()
        if "clients" not in collections:
            logger.info("Creating clients collection...")
            await db.create_collection("clients")
        
        # Check if documents collection exists
        if "documents" not in collections:
            logger.info("Creating documents collection...")
            await db.create_collection("documents")
        
        # Check if trainings collection exists
        if "trainings" not in collections:
            logger.info("Creating trainings collection...")
            await db.create_collection("trainings")
        
        # Create a test client if none exists
        client_count = await db.clients.count_documents({})
        if client_count == 0:
            logger.info("Creating test client...")
            test_client = {
                "id": "7a992a86-e2f4-4ed5-99f7-bab4966b7306",  # Match the client_id in the user record
                "name": "Test Client",
                "hotel_name": "Test Hotel",
                "contact_person": "client@test.com",  # Match the email in the user record
                "email": "client@test.com",
                "phone": "1234567890",
                "address": "123 Test St",
                "current_stage": "I.Aşama",
                "services_completed": [],
                "carbon_footprint": None,
                "sustainability_score": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.clients.insert_one(test_client)
            logger.info("Test client created successfully")
        
        # Create a test document if none exists
        document_count = await db.documents.count_documents({})
        if document_count == 0:
            logger.info("Creating test document...")
            test_document = {
                "id": "d1234567-89ab-cdef-0123-456789abcdef",
                "client_id": "7a992a86-e2f4-4ed5-99f7-bab4966b7306",  # Match the client_id
                "name": "Test Document",
                "document_type": "TR1_CRITERIA",
                "stage": "I.Aşama",
                "file_path": "/test/path/to/document.pdf",
                "original_filename": "document.pdf",
                "file_size": 1024,
                "uploaded_by": "admin",
                "created_at": datetime.utcnow(),
                "folder_path": "Test Client SYS/A SÜTUNU/A1",
                "folder_level": 2,
                "local_upload": True
            }
            await db.documents.insert_one(test_document)
            logger.info("Test document created successfully")
        
        # Create a test training if none exists
        training_count = await db.trainings.count_documents({})
        if training_count == 0:
            logger.info("Creating test training...")
            test_training = {
                "id": "t1234567-89ab-cdef-0123-456789abcdef",
                "client_id": "7a992a86-e2f4-4ed5-99f7-bab4966b7306",  # Match the client_id
                "name": "Test Training",
                "subject": "Sustainability",
                "participant_count": 10,
                "trainer": "John Doe",
                "training_date": datetime.utcnow(),
                "description": "A test training for sustainability",
                "status": "planned",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.trainings.insert_one(test_training)
            logger.info("Test training created successfully")
        
        # Check if data was created successfully
        client_count = await db.clients.count_documents({})
        document_count = await db.documents.count_documents({})
        training_count = await db.trainings.count_documents({})
        
        logger.info(f"Total clients: {client_count}")
        logger.info(f"Total documents: {document_count}")
        logger.info(f"Total trainings: {training_count}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating test data: {str(e)}")
        return False

async def main():
    """Main function to create test data"""
    logger.info("Starting test data creation...")
    
    # Create test data
    success = await create_test_data()
    
    if success:
        logger.info("Test data creation completed successfully")
    else:
        logger.error("Test data creation failed")

if __name__ == "__main__":
    asyncio.run(main())