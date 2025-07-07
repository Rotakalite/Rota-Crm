import unittest
import json
import logging
import requests
import os
import sys
import io
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pymongo

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://fa8c9f7b-7d18-4995-aa12-a264e654b749.preview.emergentagent.com/api"
RAILWAY_MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "sustainable_tourism_crm"

# Test JWT token - this is a sample token for testing
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

class TestEmailManagementRealData:
    """Test class for Email Management real data endpoints and MongoDB data"""
    
    def __init__(self):
        """Initialize test environment"""
        self.api_url = RAILWAY_API_URL
        self.mongo_url = RAILWAY_MONGO_URL
        self.db_name = DB_NAME
        self.headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        
        # Connect to MongoDB
        self.mongo_client = pymongo.MongoClient(self.mongo_url)
        self.db = self.mongo_client[self.db_name]
    
    def check_mongodb_connection(self):
        """Check if MongoDB connection is working"""
        try:
            # List all collections in the database
            collections = self.db.list_collection_names()
            logger.info(f"Successfully connected to MongoDB. Collections: {collections}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            return False
    
    def get_real_clients_from_db(self):
        """Get all clients directly from MongoDB"""
        try:
            clients = list(self.db.clients.find())
            logger.info(f"Found {len(clients)} clients in MongoDB")
            
            # Format client data for display
            formatted_clients = []
            for client in clients:
                if "_id" in client:
                    del client["_id"]  # Remove MongoDB ObjectId which is not JSON serializable
                
                formatted_client = {
                    "id": client.get("id", ""),
                    "name": client.get("name", ""),
                    "hotel_name": client.get("hotel_name", ""),
                    "email": client.get("email", ""),
                    "contact_person": client.get("contact_person", ""),
                    "current_stage": client.get("current_stage", "")
                }
                formatted_clients.append(formatted_client)
            
            return formatted_clients
        except Exception as e:
            logger.error(f"Error fetching clients from MongoDB: {str(e)}")
            return []
    
    def get_real_documents_from_db(self):
        """Get all documents directly from MongoDB"""
        try:
            documents = list(self.db.documents.find())
            logger.info(f"Found {len(documents)} documents in MongoDB")
            
            # Format document data for display
            formatted_documents = []
            for doc in documents:
                if "_id" in doc:
                    del doc["_id"]  # Remove MongoDB ObjectId which is not JSON serializable
                
                # Get client info
                client = self.db.clients.find_one({"id": doc.get("client_id", "")})
                client_name = client.get("hotel_name", "Unknown Client") if client else "Unknown Client"
                
                formatted_doc = {
                    "id": doc.get("id", ""),
                    "name": doc.get("name", ""),
                    "document_type": doc.get("document_type", ""),
                    "stage": doc.get("stage", ""),
                    "file_path": doc.get("file_path", ""),
                    "client_id": doc.get("client_id", ""),
                    "client_name": client_name,
                    "created_at": doc.get("created_at", "")
                }
                formatted_documents.append(formatted_doc)
            
            return formatted_documents
        except Exception as e:
            logger.error(f"Error fetching documents from MongoDB: {str(e)}")
            return []
    
    def get_real_trainings_from_db(self):
        """Get all trainings directly from MongoDB"""
        try:
            trainings = list(self.db.trainings.find())
            logger.info(f"Found {len(trainings)} trainings in MongoDB")
            
            # Format training data for display
            formatted_trainings = []
            for training in trainings:
                if "_id" in training:
                    del training["_id"]  # Remove MongoDB ObjectId which is not JSON serializable
                
                # Get client info
                client = self.db.clients.find_one({"id": training.get("client_id", "")})
                client_name = client.get("hotel_name", "Unknown Client") if client else "Unknown Client"
                
                formatted_training = {
                    "id": training.get("id", ""),
                    "name": training.get("name", ""),
                    "subject": training.get("subject", ""),
                    "participant_count": training.get("participant_count", 0),
                    "trainer": training.get("trainer", ""),
                    "training_date": training.get("training_date", ""),
                    "description": training.get("description", ""),
                    "status": training.get("status", ""),
                    "client_id": training.get("client_id", ""),
                    "client_name": client_name
                }
                formatted_trainings.append(formatted_training)
            
            return formatted_trainings
        except Exception as e:
            logger.error(f"Error fetching trainings from MongoDB: {str(e)}")
            return []
    
    def test_email_management_clients_endpoint(self):
        """Test the /api/email-management/clients-real endpoint"""
        logger.info("\n=== Testing /api/email-management/clients-real endpoint ===")
        
        url = f"{self.api_url}/email-management/clients-real"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.verify_clients_response(data)
                
                logger.info("✅ GET /api/email-management/clients-real test passed")
                return data
            elif response.status_code == 404:
                logger.error("❌ Endpoint returned 404 Not Found")
                return None
            else:
                logger.error(f"❌ Unexpected status code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Error testing clients endpoint: {str(e)}")
            return None
    
    def test_email_management_documents_endpoint(self):
        """Test the /api/email-management/documents-real endpoint"""
        logger.info("\n=== Testing /api/email-management/documents-real endpoint ===")
        
        url = f"{self.api_url}/email-management/documents-real"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.verify_documents_response(data)
                
                logger.info("✅ GET /api/email-management/documents-real test passed")
                return data
            elif response.status_code == 404:
                logger.error("❌ Endpoint returned 404 Not Found")
                return None
            else:
                logger.error(f"❌ Unexpected status code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Error testing documents endpoint: {str(e)}")
            return None
    
    def test_email_management_trainings_endpoint(self):
        """Test the /api/email-management/trainings-real endpoint"""
        logger.info("\n=== Testing /api/email-management/trainings-real endpoint ===")
        
        url = f"{self.api_url}/email-management/trainings-real"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.verify_trainings_response(data)
                
                logger.info("✅ GET /api/email-management/trainings-real test passed")
                return data
            elif response.status_code == 404:
                logger.error("❌ Endpoint returned 404 Not Found")
                return None
            else:
                logger.error(f"❌ Unexpected status code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Error testing trainings endpoint: {str(e)}")
            return None
    
    def test_standard_api_endpoints(self):
        """Test the standard API endpoints for comparison"""
        logger.info("\n=== Testing standard API endpoints for comparison ===")
        
        # Test /api/clients endpoint
        logger.info("Testing /api/clients endpoint...")
        url = f"{self.api_url}/clients"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} clients via standard API")
                
                # Log a few client details for comparison
                if len(data) > 0:
                    sample_clients = data[:min(3, len(data))]
                    for client in sample_clients:
                        logger.info(f"Client: {client.get('name')} - {client.get('hotel_name')} - {client.get('email')}")
            else:
                logger.error(f"❌ Unexpected status code: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing clients endpoint: {str(e)}")
        
        # Test /api/documents endpoint
        logger.info("Testing /api/documents endpoint...")
        url = f"{self.api_url}/documents"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} documents via standard API")
                
                # Log a few document details for comparison
                if len(data) > 0:
                    sample_docs = data[:min(3, len(data))]
                    for doc in sample_docs:
                        logger.info(f"Document: {doc.get('name')} - {doc.get('document_type')} - Client: {doc.get('client_id')}")
            else:
                logger.error(f"❌ Unexpected status code: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing documents endpoint: {str(e)}")
        
        # Test /api/trainings endpoint
        logger.info("Testing /api/trainings endpoint...")
        url = f"{self.api_url}/trainings"
        
        try:
            response = requests.get(url, headers=self.headers)
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} trainings via standard API")
                
                # Log a few training details for comparison
                if len(data) > 0:
                    sample_trainings = data[:min(3, len(data))]
                    for training in sample_trainings:
                        logger.info(f"Training: {training.get('name')} - {training.get('subject')} - Client: {training.get('client_id')}")
            else:
                logger.error(f"❌ Unexpected status code: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing trainings endpoint: {str(e)}")
    
    def verify_clients_response(self, data):
        """Verify the structure of the clients response"""
        assert "clients" in data, "Response should contain 'clients' key"
        clients = data["clients"]
        assert isinstance(clients, list), "Clients should be a list"
        
        if len(clients) > 0:
            client = clients[0]
            assert "id" in client, "Client should have 'id' field"
            assert "name" in client, "Client should have 'name' field"
            assert "email" in client, "Client should have 'email' field"
            assert "contact_person" in client, "Client should have 'contact_person' field"
            assert "category" in client, "Client should have 'category' field"
            assert "client_id" in client, "Client should have 'client_id' field"
    
    def verify_documents_response(self, data):
        """Verify the structure of the documents response"""
        assert "documents" in data, "Response should contain 'documents' key"
        documents = data["documents"]
        assert isinstance(documents, list), "Documents should be a list"
        
        if len(documents) > 0:
            doc = documents[0]
            assert "id" in doc, "Document should have 'id' field"
            assert "title" in doc, "Document should have 'title' field"
            assert "type" in doc, "Document should have 'type' field"
            assert "category" in doc, "Document should have 'category' field"
            assert "upload_date" in doc, "Document should have 'upload_date' field"
            assert "file_size" in doc, "Document should have 'file_size' field"
            assert "file_path" in doc, "Document should have 'file_path' field"
            assert "client_id" in doc, "Document should have 'client_id' field"
            assert "client_name" in doc, "Document should have 'client_name' field"
    
    def verify_trainings_response(self, data):
        """Verify the structure of the trainings response"""
        assert "trainings" in data, "Response should contain 'trainings' key"
        trainings = data["trainings"]
        assert isinstance(trainings, list), "Trainings should be a list"
        
        if len(trainings) > 0:
            training = trainings[0]
            assert "id" in training, "Training should have 'id' field"
            assert "title" in training, "Training should have 'title' field"
            assert "description" in training, "Training should have 'description' field"
            assert "duration" in training, "Training should have 'duration' field"
            assert "level" in training, "Training should have 'level' field"
            assert "category" in training, "Training should have 'category' field"
            assert "client_id" in training, "Training should have 'client_id' field"
            assert "client_name" in training, "Training should have 'client_name' field"
            assert "trainer" in training, "Training should have 'trainer' field"
            assert "training_date" in training, "Training should have 'training_date' field"
            assert "status" in training, "Training should have 'status' field"
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("\n=== Starting Email Management Real Data Tests ===\n")
        
        # Check MongoDB connection
        if not self.check_mongodb_connection():
            logger.error("❌ MongoDB connection failed. Aborting tests.")
            return
        
        # Get data directly from MongoDB
        logger.info("\n=== Getting data directly from MongoDB ===\n")
        
        clients = self.get_real_clients_from_db()
        logger.info(f"Found {len(clients)} clients in MongoDB")
        if len(clients) > 0:
            logger.info("Sample clients from MongoDB:")
            for client in clients[:min(3, len(clients))]:
                logger.info(f"Client: {client.get('name')} - {client.get('hotel_name')} - {client.get('email')}")
        
        documents = self.get_real_documents_from_db()
        logger.info(f"Found {len(documents)} documents in MongoDB")
        if len(documents) > 0:
            logger.info("Sample documents from MongoDB:")
            for doc in documents[:min(3, len(documents))]:
                logger.info(f"Document: {doc.get('name')} - {doc.get('document_type')} - Client: {doc.get('client_name')}")
        
        trainings = self.get_real_trainings_from_db()
        logger.info(f"Found {len(trainings)} trainings in MongoDB")
        if len(trainings) > 0:
            logger.info("Sample trainings from MongoDB:")
            for training in trainings[:min(3, len(trainings))]:
                logger.info(f"Training: {training.get('name')} - {training.get('subject')} - Client: {training.get('client_name')}")
        
        # Test API endpoints
        logger.info("\n=== Testing API endpoints ===\n")
        
        # Test standard API endpoints for comparison
        self.test_standard_api_endpoints()
        
        # Test email management endpoints
        clients_data = self.test_email_management_clients_endpoint()
        documents_data = self.test_email_management_documents_endpoint()
        trainings_data = self.test_email_management_trainings_endpoint()
        
        # Compare MongoDB data with API responses
        logger.info("\n=== Comparing MongoDB data with API responses ===\n")
        
        if clients_data:
            api_clients_count = len(clients_data.get("clients", []))
            logger.info(f"MongoDB clients: {len(clients)}, API clients: {api_clients_count}")
        else:
            logger.info("No clients data from API to compare")
        
        if documents_data:
            api_documents_count = len(documents_data.get("documents", []))
            logger.info(f"MongoDB documents: {len(documents)}, API documents: {api_documents_count}")
        else:
            logger.info("No documents data from API to compare")
        
        if trainings_data:
            api_trainings_count = len(trainings_data.get("trainings", []))
            logger.info(f"MongoDB trainings: {len(trainings)}, API trainings: {api_trainings_count}")
        else:
            logger.info("No trainings data from API to compare")
        
        logger.info("\n=== Email Management Real Data Tests Completed ===\n")

if __name__ == "__main__":
    tester = TestEmailManagementRealData()
    tester.run_all_tests()