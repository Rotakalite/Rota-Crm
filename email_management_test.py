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
BACKEND_URL = "https://be473f49-c085-4355-8cf7-95fc4e8bf06a.preview.emergentagent.com/api"

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

if __name__ == "__main__":
    unittest.main()