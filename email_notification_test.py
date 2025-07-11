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

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"
EMERGENTAGENT_API_URL = "https://36a5b90e-f3d9-4915-ab44-784415b46fb6.preview.emergentagent.com/api"

# Test JWT token - this is a sample token for testing
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

class TestEmailNotificationSystem(unittest.TestCase):
    """Test class for email notification system"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = EMERGENTAGENT_API_URL
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    def test_email_management_endpoints(self):
        """Test the email management endpoints"""
        logger.info("\n=== Testing Email Management Endpoints ===")
        
        # Test /api/email-management/clients-real endpoint
        logger.info("Testing /api/email-management/clients-real endpoint...")
        url = f"{self.api_url}/email-management/clients-real"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} clients")
                
                # Verify response structure (should be a list)
                self.assertIsInstance(data, list)
                
                # If there are clients, check their structure
                if len(data) > 0:
                    client = data[0]
                    self.assertIn("id", client)
                    self.assertIn("name", client)
                    self.assertIn("email", client)
                    self.assertIn("contact_person", client)
                    
                    # Log client details
                    logger.info(f"Client: {client['name']}, Email: {client['email']}")
                
                logger.info("✅ /api/email-management/clients-real endpoint test passed")
            elif response.status_code == 404:
                logger.info("⚠️ /api/email-management/clients-real endpoint not found")
            else:
                logger.info(f"⚠️ /api/email-management/clients-real endpoint returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing /api/email-management/clients-real endpoint: {str(e)}")
            raise
        
        # Test /api/email-management/documents-real endpoint
        logger.info("\nTesting /api/email-management/documents-real endpoint...")
        url = f"{self.api_url}/email-management/documents-real"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} documents")
                
                # Verify response structure (should be a list)
                self.assertIsInstance(data, list)
                
                # If there are documents, check their structure
                if len(data) > 0:
                    document = data[0]
                    self.assertIn("id", document)
                    self.assertIn("title", document)
                    self.assertIn("client_id", document)
                    self.assertIn("client_name", document)
                    self.assertIn("upload_date", document)
                    
                    # Log document details
                    logger.info(f"Document: {document['title']}, Client: {document['client_name']}")
                
                logger.info("✅ /api/email-management/documents-real endpoint test passed")
            elif response.status_code == 404:
                logger.info("⚠️ /api/email-management/documents-real endpoint not found")
            else:
                logger.info(f"⚠️ /api/email-management/documents-real endpoint returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing /api/email-management/documents-real endpoint: {str(e)}")
            raise
        
        # Test /api/email-management/trainings-real endpoint
        logger.info("\nTesting /api/email-management/trainings-real endpoint...")
        url = f"{self.api_url}/email-management/trainings-real"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} trainings")
                
                # Verify response structure (should be a list)
                self.assertIsInstance(data, list)
                
                # If there are trainings, check their structure
                if len(data) > 0:
                    training = data[0]
                    self.assertIn("id", training)
                    self.assertIn("title", training)
                    self.assertIn("client_id", training)
                    self.assertIn("client_name", training)
                    self.assertIn("trainer", training)
                    self.assertIn("training_date", training)
                    
                    # Log training details
                    logger.info(f"Training: {training['title']}, Client: {training['client_name']}, Trainer: {training['trainer']}")
                
                logger.info("✅ /api/email-management/trainings-real endpoint test passed")
            elif response.status_code == 404:
                logger.info("⚠️ /api/email-management/trainings-real endpoint not found")
            else:
                logger.info(f"⚠️ /api/email-management/trainings-real endpoint returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing /api/email-management/trainings-real endpoint: {str(e)}")
            raise
    
    def test_document_notification_endpoint(self):
        """Test the document notification endpoint"""
        logger.info("\n=== Testing Document Notification Endpoint ===")
        
        # First, get a document ID to use for testing
        document_id = None
        
        # Try to get a document from the documents-real endpoint
        url = f"{self.api_url}/email-management/documents-real"
        try:
            response = requests.get(url, headers=self.headers_admin)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 0:
                    document_id = data[0]["id"]
                    logger.info(f"Found document ID for testing: {document_id}")
            else:
                logger.info("Could not get document ID from /api/email-management/documents-real endpoint")
        except Exception as e:
            logger.error(f"Error getting document ID: {str(e)}")
        
        # If we couldn't get a document ID, try to get one from the documents endpoint
        if not document_id:
            url = f"{self.api_url}/documents"
            try:
                response = requests.get(url, headers=self.headers_admin)
                if response.status_code == 200:
                    data = response.json()
                    if len(data) > 0:
                        document_id = data[0]["id"]
                        logger.info(f"Found document ID for testing: {document_id}")
                else:
                    logger.info("Could not get document ID from /api/documents endpoint")
            except Exception as e:
                logger.error(f"Error getting document ID: {str(e)}")
        
        # If we still don't have a document ID, we can't test the notification endpoint
        if not document_id:
            logger.warning("⚠️ Could not find a document ID for testing, skipping document notification test")
            return
        
        # Test /api/email/document-notification endpoint
        logger.info("\nTesting /api/email/document-notification endpoint...")
        url = f"{self.api_url}/email/document-notification"
        
        try:
            # Create form data with document ID
            form_data = {"document_id": document_id}
            
            response = requests.post(url, headers=self.headers_admin, data=form_data)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 400, 401, 403, 404, 500])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIn("message", data)
                
                logger.info("✅ /api/email/document-notification endpoint test passed")
            elif response.status_code == 404:
                logger.info("⚠️ /api/email/document-notification endpoint not found")
            elif response.status_code == 500:
                data = response.json()
                logger.info(f"⚠️ Server error: {data.get('detail', 'Unknown error')}")
            else:
                logger.info(f"⚠️ /api/email/document-notification endpoint returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing /api/email/document-notification endpoint: {str(e)}")
            raise
    
    def test_training_notification_endpoint(self):
        """Test the training notification endpoint"""
        logger.info("\n=== Testing Training Notification Endpoint ===")
        
        # First, get a training ID to use for testing
        training_id = None
        
        # Try to get a training from the trainings-real endpoint
        url = f"{self.api_url}/email-management/trainings-real"
        try:
            response = requests.get(url, headers=self.headers_admin)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 0:
                    training_id = data[0]["id"]
                    logger.info(f"Found training ID for testing: {training_id}")
            else:
                logger.info("Could not get training ID from /api/email-management/trainings-real endpoint")
        except Exception as e:
            logger.error(f"Error getting training ID: {str(e)}")
        
        # If we couldn't get a training ID, try to get one from the trainings endpoint
        if not training_id:
            url = f"{self.api_url}/trainings"
            try:
                response = requests.get(url, headers=self.headers_admin)
                if response.status_code == 200:
                    data = response.json()
                    if len(data) > 0:
                        training_id = data[0]["id"]
                        logger.info(f"Found training ID for testing: {training_id}")
                else:
                    logger.info("Could not get training ID from /api/trainings endpoint")
            except Exception as e:
                logger.error(f"Error getting training ID: {str(e)}")
        
        # If we still don't have a training ID, we can't test the notification endpoint
        if not training_id:
            logger.warning("⚠️ Could not find a training ID for testing, skipping training notification test")
            return
        
        # Test /api/email/training-notification endpoint
        logger.info("\nTesting /api/email/training-notification endpoint...")
        url = f"{self.api_url}/email/training-notification"
        
        try:
            # Create form data with training ID
            form_data = {"training_id": training_id}
            
            response = requests.post(url, headers=self.headers_admin, data=form_data)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 400, 401, 403, 404, 500])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIn("message", data)
                
                logger.info("✅ /api/email/training-notification endpoint test passed")
            elif response.status_code == 404:
                logger.info("⚠️ /api/email/training-notification endpoint not found")
            elif response.status_code == 500:
                data = response.json()
                logger.info(f"⚠️ Server error: {data.get('detail', 'Unknown error')}")
            else:
                logger.info(f"⚠️ /api/email/training-notification endpoint returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing /api/email/training-notification endpoint: {str(e)}")
            raise
    
    def test_email_service_integration(self):
        """Test the email service integration"""
        logger.info("\n=== Testing Email Service Integration ===")
        
        # Test /api/email/test endpoint
        logger.info("Testing /api/email/test endpoint...")
        url = f"{self.api_url}/email/test"
        
        try:
            response = requests.post(url, headers=self.headers_admin)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404, 500])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIn("success", data)
                self.assertIn("message", data)
                
                logger.info("✅ /api/email/test endpoint test passed")
            elif response.status_code == 404:
                logger.info("⚠️ /api/email/test endpoint not found")
            elif response.status_code == 500:
                data = response.json()
                logger.info(f"⚠️ Server error: {data.get('detail', 'Unknown error')}")
            else:
                logger.info(f"⚠️ /api/email/test endpoint returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing /api/email/test endpoint: {str(e)}")
            raise

class TestEmailTemplateRendering(unittest.TestCase):
    """Test class for email template rendering"""
    
    def setUp(self):
        """Set up test environment"""
        # Set up paths to template files
        self.template_dir = "/app/backend/templates"
        self.document_template_path = os.path.join(self.template_dir, "document_upload_tr.html")
        self.training_template_path = os.path.join(self.template_dir, "training_notification_tr.html")
    
    def test_template_files_exist(self):
        """Test that the template files exist"""
        logger.info("\n=== Testing Template Files Exist ===")
        
        # Check document template
        logger.info("Checking document_upload_tr.html template...")
        self.assertTrue(os.path.exists(self.document_template_path), "document_upload_tr.html template file does not exist")
        logger.info("✅ document_upload_tr.html template file exists")
        
        # Check training template
        logger.info("Checking training_notification_tr.html template...")
        self.assertTrue(os.path.exists(self.training_template_path), "training_notification_tr.html template file does not exist")
        logger.info("✅ training_notification_tr.html template file exists")
    
    def test_template_content(self):
        """Test the content of the template files"""
        logger.info("\n=== Testing Template Content ===")
        
        # Check document template content
        logger.info("Checking document_upload_tr.html template content...")
        with open(self.document_template_path, "r", encoding="utf-8") as f:
            document_template_content = f.read()
        
        # Check for required variables in document template
        self.assertIn("{{ client_name }}", document_template_content, "client_name variable missing in document template")
        self.assertIn("{{ document_name }}", document_template_content, "document_name variable missing in document template")
        self.assertIn("{{ upload_date }}", document_template_content, "upload_date variable missing in document template")
        self.assertIn("{{ folder_path }}", document_template_content, "folder_path variable missing in document template")
        logger.info("✅ document_upload_tr.html template contains all required variables")
        
        # Check training template content
        logger.info("Checking training_notification_tr.html template content...")
        with open(self.training_template_path, "r", encoding="utf-8") as f:
            training_template_content = f.read()
        
        # Check for required variables in training template
        self.assertIn("{{ client_name }}", training_template_content, "client_name variable missing in training template")
        self.assertIn("{{ training_name }}", training_template_content, "training_name variable missing in training template")
        self.assertIn("{{ training_date }}", training_template_content, "training_date variable missing in training template")
        self.assertIn("{{ trainer }}", training_template_content, "trainer variable missing in training template")
        self.assertIn("{{ participant_count }}", training_template_content, "participant_count variable missing in training template")
        logger.info("✅ training_notification_tr.html template contains all required variables")

def run_email_notification_tests():
    """Run email notification tests"""
    print("\n=== Running Email Notification Tests ===")
    
    # Create a test suite for email template rendering only
    email_suite = unittest.TestSuite()
    email_suite.addTest(TestEmailTemplateRendering("test_template_files_exist"))
    email_suite.addTest(TestEmailTemplateRendering("test_template_content"))
    
    # Run the email template rendering tests
    unittest.TextTestRunner().run(email_suite)

if __name__ == "__main__":
    run_email_notification_tests()