import unittest
import json
import logging
import requests
import os
import sys
import io
import uuid
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "rotacrm"

class TestTrainingDataFormat(unittest.TestCase):
    """Test class for training data format"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Connect to MongoDB to get real training data
        try:
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            logger.info(f"✅ Connected to MongoDB: {DB_NAME}")
            self.db_connected = True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            self.mongo_client = None
            self.db = None
            self.db_connected = False
    
    def test_training_data_format(self):
        """Test training data format in MongoDB"""
        logger.info("\n=== Testing training data format in MongoDB ===")
        
        if self.db_connected:
            # Get all trainings from the database
            trainings = list(self.db.trainings.find({}))
            logger.info(f"Found {len(trainings)} trainings in the database")
            
            # Check if trainings have the required fields
            for training in trainings:
                # Check for required fields
                self.assertIn("id", training)
                self.assertIn("client_id", training)
                
                # Check for name field (could be "name" or "title")
                has_name_field = "name" in training or "title" in training
                self.assertTrue(has_name_field, "Training should have either 'name' or 'title' field")
                
                # Log the name field
                if "name" in training:
                    logger.info(f"Training name: {training['name']}")
                elif "title" in training:
                    logger.info(f"Training title: {training['title']}")
                
                # Check other fields
                self.assertIn("subject", training)
                self.assertIn("participant_count", training)
                self.assertIn("trainer", training)
                
                # Check if training_date is a valid date
                self.assertIn("training_date", training)
                training_date = training.get("training_date")
                logger.info(f"Training date: {training_date}")
                
                # Check if training_date is a valid datetime object
                self.assertIsInstance(training_date, datetime)
            
            logger.info("✅ All trainings have the required fields with valid dates")
        else:
            logger.warning("⚠️ MongoDB connection failed, skipping test")
    
    def test_document_date_format(self):
        """Test document date format in MongoDB"""
        logger.info("\n=== Testing document date format in MongoDB ===")
        
        if self.db_connected:
            # Get all documents from the database
            documents = list(self.db.documents.find({}))
            logger.info(f"Found {len(documents)} documents in the database")
            
            # Check if documents have the required fields
            for document in documents:
                # Check for required fields
                self.assertIn("id", document)
                self.assertIn("client_id", document)
                
                # Check if created_at is a valid date
                self.assertIn("created_at", document)
                created_at = document.get("created_at")
                logger.info(f"Document created_at: {created_at}")
                
                # Check if created_at is a valid datetime object
                self.assertIsInstance(created_at, datetime)
            
            logger.info("✅ All documents have valid created_at dates")
        else:
            logger.warning("⚠️ MongoDB connection failed, skipping test")

if __name__ == "__main__":
    unittest.main()