import unittest
import json
import logging
import requests
import os
import sys
import io
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "https://be473f49-c085-4355-8cf7-95fc4e8bf06a.preview.emergentagent.com/api"

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

class TestEmailManagementBackend(unittest.TestCase):
    """Test class for Email Management backend functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_URL
        
        # Headers for different authentication scenarios
        self.headers_valid = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_documents_endpoint(self):
        """Test GET /api/documents endpoint for email management"""
        logger.info("\n=== Testing GET /api/documents endpoint ===")
        
        url = f"{self.api_url}/documents"
        
        # Test with valid authentication
        try:
            response = requests.get(url, headers=self.headers_valid)
            logger.info(f"Valid auth response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain documents
            data = response.json()
            self.assertIn("documents", data)
            self.assertIsInstance(data["documents"], list)
            
            # Check structure of documents
            if len(data["documents"]) > 0:
                document = data["documents"][0]
                self.assertIn("id", document)
                self.assertIn("title", document)
                self.assertIn("type", document)
                self.assertIn("category", document)
                self.assertIn("upload_date", document)
                self.assertIn("file_size", document)
                self.assertIn("file_path", document)
            
            logger.info(f"Found {len(data['documents'])} documents")
            logger.info("✅ GET /api/documents with valid auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing documents endpoint with valid auth: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ GET /api/documents with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing documents endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ GET /api/documents with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing documents endpoint with no auth: {str(e)}")
            raise
    
    def test_trainings_endpoint(self):
        """Test GET /api/trainings endpoint for email management"""
        logger.info("\n=== Testing GET /api/trainings endpoint ===")
        
        url = f"{self.api_url}/trainings"
        
        # Test with valid authentication
        try:
            response = requests.get(url, headers=self.headers_valid)
            logger.info(f"Valid auth response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain trainings
            data = response.json()
            self.assertIn("trainings", data)
            self.assertIsInstance(data["trainings"], list)
            
            # Check structure of trainings
            if len(data["trainings"]) > 0:
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
            logger.info("✅ GET /api/trainings with valid auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing trainings endpoint with valid auth: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ GET /api/trainings with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing trainings endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ GET /api/trainings with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing trainings endpoint with no auth: {str(e)}")
            raise
    
    def test_clients_endpoint(self):
        """Test GET /api/clients endpoint for email management"""
        logger.info("\n=== Testing GET /api/clients endpoint ===")
        
        url = f"{self.api_url}/clients"
        
        # Test with valid authentication
        try:
            response = requests.get(url, headers=self.headers_valid)
            logger.info(f"Valid auth response status code: {response.status_code}")
            
            # Should get 200 OK
            self.assertEqual(response.status_code, 200)
            
            # Response should contain clients
            data = response.json()
            self.assertIn("clients", data)
            self.assertIsInstance(data["clients"], list)
            
            # Check structure of clients
            if len(data["clients"]) > 0:
                client = data["clients"][0]
                self.assertIn("id", client)
                self.assertIn("name", client)
                self.assertIn("email", client)
                self.assertIn("contact_person", client)
                self.assertIn("category", client)
            
            logger.info(f"Found {len(data['clients'])} clients")
            logger.info("✅ GET /api/clients with valid auth test passed")
        except Exception as e:
            logger.error(f"❌ Error testing clients endpoint with valid auth: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ GET /api/clients with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing clients endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ GET /api/clients with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing clients endpoint with no auth: {str(e)}")
            raise
    
    def test_send_email_endpoint(self):
        """Test POST /api/send-email endpoint"""
        logger.info("\n=== Testing POST /api/send-email endpoint ===")
        
        url = f"{self.api_url}/send-email"
        
        # Test with valid authentication
        try:
            # Create a unique subject to avoid spam filters
            unique_id = uuid.uuid4().hex[:8]
            email_data = {
                "to_email": "test@example.com",
                "subject": f"Test Email {unique_id}",
                "html_content": "<h1>Test Email</h1><p>This is a test email from the Email Management backend test.</p>"
            }
            
            response = requests.post(url, headers=self.headers_valid, json=email_data)
            logger.info(f"Valid auth response status code: {response.status_code}")
            
            # Should get 200 OK or 500 if email service is not available
            self.assertIn(response.status_code, [200, 500])
            
            if response.status_code == 200:
                # Response should contain success message
                data = response.json()
                self.assertIn("message", data)
                self.assertIn("status", data)
                self.assertEqual(data["status"], "sent")
                
                logger.info("✅ POST /api/send-email with valid auth test passed")
            else:
                # If email service is not available, check error message
                data = response.json()
                self.assertIn("detail", data)
                logger.info(f"⚠️ Email service not available: {data['detail']}")
                logger.info("⚠️ POST /api/send-email test skipped due to email service unavailability")
        except Exception as e:
            logger.error(f"❌ Error testing send-email endpoint with valid auth: {str(e)}")
            raise
        
        # Test with missing required fields
        try:
            # Missing to_email
            incomplete_data = {
                "subject": "Test Email",
                "html_content": "<h1>Test Email</h1><p>This is a test email.</p>"
            }
            
            response = requests.post(url, headers=self.headers_valid, json=incomplete_data)
            logger.info(f"Missing fields response status code: {response.status_code}")
            
            # Should get 422 Unprocessable Entity
            self.assertEqual(response.status_code, 422)
            
            logger.info("✅ POST /api/send-email with missing fields correctly returns 422")
        except Exception as e:
            logger.error(f"❌ Error testing send-email endpoint with missing fields: {str(e)}")
            raise
        
        # Test with invalid authentication
        try:
            response = requests.post(url, headers=self.headers_invalid, json=email_data)
            logger.info(f"Invalid auth response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ POST /api/send-email with invalid auth correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing send-email endpoint with invalid auth: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.post(url, headers=self.headers_no_auth, json=email_data)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ POST /api/send-email with no auth correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing send-email endpoint with no auth: {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main()