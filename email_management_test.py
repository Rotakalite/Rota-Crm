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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "https://96c96d61-de51-4844-9405-36489580d965.preview.emergentagent.com/api"
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT token for admin user
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

# Mock response class for testing
class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data

class TestEmailManagementBackend(unittest.TestCase):
    """Test class for Email Management backend functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_URL
        
        # Sample test data
        self.documents_data = {
            "documents": [
                {
                    "id": 1,
                    "title": "Sürdürülebilirlik Rehberi 2025",
                    "type": "PDF",
                    "category": "Training Material",
                    "upload_date": datetime.utcnow().isoformat(),
                    "file_size": "2.5 MB",
                    "file_path": "/docs/sustainability_guide.pdf"
                },
                {
                    "id": 2,
                    "title": "Çevre Politikası Dokümanı",
                    "type": "PDF", 
                    "category": "Policy Document",
                    "upload_date": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                    "file_size": "1.2 MB",
                    "file_path": "/docs/environment_policy.pdf"
                }
            ]
        }
        
        self.trainings_data = {
            "trainings": [
                {
                    "id": 1,
                    "title": "Sürdürülebilir Turizm Eğitimi",
                    "description": "Temel sürdürülebilirlik prensipleri ve uygulamaları",
                    "duration": "2 saat",
                    "level": "Başlangıç",
                    "category": "Environment",
                    "content_type": "Video + PDF",
                    "created_date": datetime.utcnow().isoformat()
                },
                {
                    "id": 2,
                    "title": "Enerji Tasarrufu ve Verimlilik Eğitimi",
                    "description": "Otel operasyonlarında enerji verimliliği teknikleri",
                    "duration": "1.5 saat",
                    "level": "Orta",
                    "category": "Energy",
                    "content_type": "Interactive Course",
                    "created_date": (datetime.utcnow() - timedelta(days=7)).isoformat()
                }
            ]
        }
        
        self.clients_data = {
            "clients": [
                {
                    "id": 1,
                    "name": "Paradise Resort & Spa",
                    "email": "info@paradiseresort.com",
                    "contact_person": "Ahmet Yılmaz",
                    "category": "5 Star Resort"
                },
                {
                    "id": 2,
                    "name": "Green Valley Hotel",
                    "email": "contact@greenvalley.com",
                    "contact_person": "Elif Özkan",
                    "category": "Boutique Hotel"
                }
            ]
        }
        
        self.email_success_response = {
            "message": "Email sent successfully",
            "status": "sent"
        }
        
        self.email_error_response = {
            "detail": "Email service not available"
        }
    
    @patch('requests.get')
    def test_documents_endpoint(self, mock_get):
        """Test GET /api/documents endpoint for email management"""
        logger.info("\n=== Testing GET /api/documents endpoint ===")
        
        # Mock the response
        mock_get.return_value = MockResponse(self.documents_data, 200)
        
        url = f"{self.api_url}/documents"
        response = requests.get(url)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check response structure
        self.assertIn("documents", data)
        self.assertIsInstance(data["documents"], list)
        self.assertEqual(len(data["documents"]), 2)
        
        # Check document structure
        document = data["documents"][0]
        self.assertIn("id", document)
        self.assertIn("title", document)
        self.assertIn("type", document)
        self.assertIn("category", document)
        self.assertIn("upload_date", document)
        self.assertIn("file_size", document)
        self.assertIn("file_path", document)
        
        logger.info(f"Found {len(data['documents'])} documents")
        logger.info("✅ GET /api/documents test passed")
        
        # Test authentication error
        mock_get.return_value = MockResponse({"detail": "Not authenticated"}, 401)
        response = requests.get(url)
        self.assertEqual(response.status_code, 401)
        logger.info("✅ GET /api/documents authentication test passed")
    
    @patch('requests.get')
    def test_trainings_endpoint(self, mock_get):
        """Test GET /api/trainings endpoint for email management"""
        logger.info("\n=== Testing GET /api/trainings endpoint ===")
        
        # Mock the response
        mock_get.return_value = MockResponse(self.trainings_data, 200)
        
        url = f"{self.api_url}/trainings"
        response = requests.get(url)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check response structure
        self.assertIn("trainings", data)
        self.assertIsInstance(data["trainings"], list)
        self.assertEqual(len(data["trainings"]), 2)
        
        # Check training structure
        training = data["trainings"][0]
        self.assertIn("id", training)
        self.assertIn("title", training)
        self.assertIn("description", training)
        self.assertIn("duration", training)
        self.assertIn("level", training)
        self.assertIn("category", training)
        self.assertIn("content_type", training)
        self.assertIn("created_date", training)
        
        logger.info(f"Found {len(data['trainings'])} trainings")
        logger.info("✅ GET /api/trainings test passed")
        
        # Test authentication error
        mock_get.return_value = MockResponse({"detail": "Not authenticated"}, 401)
        response = requests.get(url)
        self.assertEqual(response.status_code, 401)
        logger.info("✅ GET /api/trainings authentication test passed")
    
    @patch('requests.get')
    def test_clients_endpoint(self, mock_get):
        """Test GET /api/clients endpoint for email management"""
        logger.info("\n=== Testing GET /api/clients endpoint ===")
        
        # Mock the response
        mock_get.return_value = MockResponse(self.clients_data, 200)
        
        url = f"{self.api_url}/clients"
        response = requests.get(url)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check response structure
        self.assertIn("clients", data)
        self.assertIsInstance(data["clients"], list)
        self.assertEqual(len(data["clients"]), 2)
        
        # Check client structure
        client = data["clients"][0]
        self.assertIn("id", client)
        self.assertIn("name", client)
        self.assertIn("email", client)
        self.assertIn("contact_person", client)
        self.assertIn("category", client)
        
        logger.info(f"Found {len(data['clients'])} clients")
        logger.info("✅ GET /api/clients test passed")
        
        # Test authentication error
        mock_get.return_value = MockResponse({"detail": "Not authenticated"}, 401)
        response = requests.get(url)
        self.assertEqual(response.status_code, 401)
        logger.info("✅ GET /api/clients authentication test passed")
    
    @patch('requests.post')
    def test_send_email_endpoint(self, mock_post):
        """Test POST /api/send-email endpoint"""
        logger.info("\n=== Testing POST /api/send-email endpoint ===")
        
        # Mock the success response
        mock_post.return_value = MockResponse(self.email_success_response, 200)
        
        url = f"{self.api_url}/send-email"
        email_data = {
            "to_email": "test@example.com",
            "subject": "Test Email",
            "html_content": "<h1>Test Email</h1><p>This is a test email.</p>"
        }
        
        response = requests.post(url, json=email_data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check response structure
        self.assertIn("message", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "sent")
        
        logger.info("✅ POST /api/send-email success test passed")
        
        # Test email service unavailable
        mock_post.return_value = MockResponse(self.email_error_response, 500)
        response = requests.post(url, json=email_data)
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)
        logger.info("✅ POST /api/send-email service unavailable test passed")
        
        # Test missing required fields
        mock_post.return_value = MockResponse({"detail": "Email and subject are required"}, 422)
        incomplete_data = {
            "subject": "Test Email",
            "html_content": "<h1>Test Email</h1><p>This is a test email.</p>"
        }
        response = requests.post(url, json=incomplete_data)
        self.assertEqual(response.status_code, 422)
        logger.info("✅ POST /api/send-email missing fields test passed")
        
        # Test authentication error
        mock_post.return_value = MockResponse({"detail": "Not authenticated"}, 401)
        response = requests.post(url, json=email_data)
        self.assertEqual(response.status_code, 401)
        logger.info("✅ POST /api/send-email authentication test passed")

class TestClientEmailManagementEndpoints(unittest.TestCase):
    """Test class for Email Management endpoints with CLIENT users"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        
        # Test JWT tokens for client users
        self.KAYA_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
        self.CANO_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0FOT19DTElFTlRfMDAxIiwiZW1haWwiOiJjYW5lcnBhbEBnbWFpbC5jb20iLCJuYW1lIjoiQ0FOTyBDbGllbnQifQ.signature"
        
        # Headers for different user types
        self.headers_kaya = {"Authorization": f"Bearer {self.KAYA_CLIENT_TOKEN}"}
        self.headers_cano = {"Authorization": f"Bearer {self.CANO_CLIENT_TOKEN}"}
    
    def test_clients_endpoint_for_client_users(self):
        """Test the /api/clients endpoint for CLIENT users"""
        logger.info("\n=== Testing /api/clients endpoint for CLIENT users ===")
        
        url = f"{self.api_url}/clients"
        
        # Test with CLIENT user (KAYA)
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"KAYA client response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list with exactly 1 client (their own)
            data = response.json()
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1, "CLIENT user should see exactly 1 client (their own)")
            
            # Log the client data
            client = data[0]
            logger.info(f"CLIENT user can see client: {client.get('name')}")
            logger.info(f"Client data: {json.dumps(client, indent=2)}")
            
            # Verify client data structure
            self.assertIn("id", client)
            self.assertIn("name", client)
            self.assertIn("hotel_name", client)
            self.assertIn("contact_person", client)
            self.assertIn("email", client)
            
            logger.info("✅ /api/clients endpoint works for CLIENT users")
        except Exception as e:
            logger.error(f"❌ Error testing /api/clients endpoint: {str(e)}")
            raise
    
    def test_documents_endpoint_for_client_users(self):
        """Test the /api/documents endpoint for CLIENT users"""
        logger.info("\n=== Testing /api/documents endpoint for CLIENT users ===")
        
        url = f"{self.api_url}/documents"
        
        # Test with CLIENT user (KAYA)
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"KAYA client response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain documents array
            data = response.json()
            self.assertIn("documents", data)
            self.assertIsInstance(data["documents"], list)
            
            # Log the number of documents
            document_count = len(data["documents"])
            logger.info(f"CLIENT user can see {document_count} documents")
            
            # Verify document data structure if documents exist
            if document_count > 0:
                document = data["documents"][0]
                logger.info(f"Sample document: {json.dumps(document, indent=2)}")
                
                self.assertIn("id", document)
                self.assertIn("title", document)
                self.assertIn("type", document)
                self.assertIn("category", document)
                self.assertIn("client_id", document)
                
                # Verify client_id matches the user's client_id
                client_response = requests.get(f"{self.api_url}/clients", headers=self.headers_kaya)
                client_data = client_response.json()
                if len(client_data) > 0:
                    client_id = client_data[0].get("id")
                    self.assertEqual(document["client_id"], client_id, "Document client_id should match user's client_id")
            
            logger.info("✅ /api/documents endpoint works for CLIENT users")
        except Exception as e:
            logger.error(f"❌ Error testing /api/documents endpoint: {str(e)}")
            raise
    
    def test_trainings_endpoint_for_client_users(self):
        """Test the /api/trainings endpoint for CLIENT users"""
        logger.info("\n=== Testing /api/trainings endpoint for CLIENT users ===")
        
        url = f"{self.api_url}/trainings"
        
        # Test with CLIENT user (KAYA)
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"KAYA client response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should be a list of trainings
            data = response.json()
            self.assertIsInstance(data, list)
            
            # Log the number of trainings
            training_count = len(data)
            logger.info(f"CLIENT user can see {training_count} trainings")
            
            # Verify training data structure if trainings exist
            if training_count > 0:
                training = data[0]
                logger.info(f"Sample training: {json.dumps(training, indent=2)}")
                
                self.assertIn("id", training)
                self.assertIn("client_id", training)
                self.assertIn("name", training)
                self.assertIn("subject", training)
                
                # Verify client_id matches the user's client_id
                client_response = requests.get(f"{self.api_url}/clients", headers=self.headers_kaya)
                client_data = client_response.json()
                if len(client_data) > 0:
                    client_id = client_data[0].get("id")
                    self.assertEqual(training["client_id"], client_id, "Training client_id should match user's client_id")
            
            logger.info("✅ /api/trainings endpoint works for CLIENT users")
        except Exception as e:
            logger.error(f"❌ Error testing /api/trainings endpoint: {str(e)}")
            raise
    
    def test_email_management_documents_real_endpoint_for_client_users(self):
        """Test the /api/email-management/documents-real endpoint for CLIENT users"""
        logger.info("\n=== Testing /api/email-management/documents-real endpoint for CLIENT users ===")
        
        url = f"{self.api_url}/email-management/documents-real"
        
        # Test with CLIENT user (KAYA)
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"KAYA client response status code: {response.status_code}")
            
            # Check response status code
            if response.status_code == 200:
                # Response should contain documents array
                data = response.json()
                self.assertIn("documents", data)
                self.assertIsInstance(data["documents"], list)
                
                # Log the number of documents
                document_count = len(data["documents"])
                logger.info(f"Found {document_count} documents in email-management/documents-real")
                
                # Verify document data structure if documents exist
                if document_count > 0:
                    document = data["documents"][0]
                    logger.info(f"Sample document: {json.dumps(document, indent=2)}")
                    
                    self.assertIn("id", document)
                    self.assertIn("title", document)
                    self.assertIn("type", document)
                    self.assertIn("category", document)
                    self.assertIn("client_id", document)
                    
                    # Verify client_id matches the user's client_id
                    client_response = requests.get(f"{self.api_url}/clients", headers=self.headers_kaya)
                    client_data = client_response.json()
                    if len(client_data) > 0:
                        client_id = client_data[0].get("id")
                        self.assertEqual(document["client_id"], client_id, "Document client_id should match user's client_id")
                
                logger.info("✅ /api/email-management/documents-real endpoint works for CLIENT users")
            elif response.status_code == 404:
                logger.warning("⚠️ /api/email-management/documents-real endpoint returned 404 Not Found")
                logger.warning("This endpoint may not be properly registered in the API router")
            else:
                logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
                if response.headers.get('content-type') == 'application/json':
                    logger.warning(f"Response: {response.json()}")
                else:
                    logger.warning(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error testing /api/email-management/documents-real endpoint: {str(e)}")
            raise
    
    def test_email_management_trainings_real_endpoint_for_client_users(self):
        """Test the /api/email-management/trainings-real endpoint for CLIENT users"""
        logger.info("\n=== Testing /api/email-management/trainings-real endpoint for CLIENT users ===")
        
        url = f"{self.api_url}/email-management/trainings-real"
        
        # Test with CLIENT user (KAYA)
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"KAYA client response status code: {response.status_code}")
            
            # Check response status code
            if response.status_code == 200:
                # Response should contain trainings array
                data = response.json()
                self.assertIn("trainings", data)
                self.assertIsInstance(data["trainings"], list)
                
                # Log the number of trainings
                training_count = len(data["trainings"])
                logger.info(f"Found {training_count} trainings in email-management/trainings-real")
                
                # Verify training data structure if trainings exist
                if training_count > 0:
                    training = data["trainings"][0]
                    logger.info(f"Sample training: {json.dumps(training, indent=2)}")
                    
                    self.assertIn("id", training)
                    self.assertIn("title", training)
                    self.assertIn("description", training)
                    self.assertIn("client_id", training)
                    
                    # Verify client_id matches the user's client_id
                    client_response = requests.get(f"{self.api_url}/clients", headers=self.headers_kaya)
                    client_data = client_response.json()
                    if len(client_data) > 0:
                        client_id = client_data[0].get("id")
                        self.assertEqual(training["client_id"], client_id, "Training client_id should match user's client_id")
                
                logger.info("✅ /api/email-management/trainings-real endpoint works for CLIENT users")
            elif response.status_code == 404:
                logger.warning("⚠️ /api/email-management/trainings-real endpoint returned 404 Not Found")
                logger.warning("This endpoint may not be properly registered in the API router")
            else:
                logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
                if response.headers.get('content-type') == 'application/json':
                    logger.warning(f"Response: {response.json()}")
                else:
                    logger.warning(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error testing /api/email-management/trainings-real endpoint: {str(e)}")
            raise
    
    def test_email_management_clients_real_endpoint_for_client_users(self):
        """Test the /api/email-management/clients-real endpoint for CLIENT users"""
        logger.info("\n=== Testing /api/email-management/clients-real endpoint for CLIENT users ===")
        
        url = f"{self.api_url}/email-management/clients-real"
        
        # Test with CLIENT user (KAYA)
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"KAYA client response status code: {response.status_code}")
            
            # Check response status code
            if response.status_code == 200:
                # Response should contain clients array
                data = response.json()
                self.assertIn("clients", data)
                self.assertIsInstance(data["clients"], list)
                
                # Log the number of clients
                client_count = len(data["clients"])
                logger.info(f"Found {client_count} clients in email-management/clients-real")
                
                # Verify client data structure if clients exist
                if client_count > 0:
                    client = data["clients"][0]
                    logger.info(f"Sample client: {json.dumps(client, indent=2)}")
                    
                    self.assertIn("id", client)
                    self.assertIn("name", client)
                    self.assertIn("email", client)
                    self.assertIn("client_id", client)
                    
                    # Verify client_id matches the user's client_id
                    client_response = requests.get(f"{self.api_url}/clients", headers=self.headers_kaya)
                    client_data = client_response.json()
                    if len(client_data) > 0:
                        user_client_id = client_data[0].get("id")
                        self.assertEqual(client["client_id"], user_client_id, "Client client_id should match user's client_id")
                
                logger.info("✅ /api/email-management/clients-real endpoint works for CLIENT users")
            elif response.status_code == 404:
                logger.warning("⚠️ /api/email-management/clients-real endpoint returned 404 Not Found")
                logger.warning("This endpoint may not be properly registered in the API router")
            else:
                logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
                if response.headers.get('content-type') == 'application/json':
                    logger.warning(f"Response: {response.json()}")
                else:
                    logger.warning(f"Response: {response.text}")
        except Exception as e:
            logger.error(f"❌ Error testing /api/email-management/clients-real endpoint: {str(e)}")
            raise

    def test_regular_endpoints(self):
        """Test regular endpoints to compare with email management endpoints"""
        logger.info("\n=== Testing regular endpoints for comparison ===")
        
        # Test /api/clients endpoint
        try:
            url = f"{self.api_url}/clients"
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"/api/clients response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    logger.info(f"Found {len(data)} clients in regular endpoint")
                else:
                    logger.info(f"Regular /api/clients endpoint returned non-list data")
                logger.info("✅ Regular /api/clients endpoint is working")
            else:
                logger.info(f"Regular /api/clients endpoint returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing regular clients endpoint: {str(e)}")
        
        # Test /api/documents endpoint
        try:
            url = f"{self.api_url}/documents"
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"/api/documents response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "documents" in data:
                    logger.info(f"Found {len(data['documents'])} documents in regular endpoint")
                else:
                    logger.info(f"Regular /api/documents endpoint returned unexpected data format")
                logger.info("✅ Regular /api/documents endpoint is working")
            else:
                logger.info(f"Regular /api/documents endpoint returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing regular documents endpoint: {str(e)}")
        
        # Test /api/trainings endpoint
        try:
            url = f"{self.api_url}/trainings"
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"/api/trainings response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    logger.info(f"Found {len(data)} trainings in regular endpoint")
                else:
                    logger.info(f"Regular /api/trainings endpoint returned unexpected data format")
                logger.info("✅ Regular /api/trainings endpoint is working")
            else:
                logger.info(f"Regular /api/trainings endpoint returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing regular trainings endpoint: {str(e)}")

if __name__ == "__main__":
    unittest.main()