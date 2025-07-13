import unittest
import logging
import requests
import uuid
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"
EMERGENTAGENT_API_URL = "https://ecd50858-c16e-4cf1-bfa1-501728878062.preview.emergentagent.com/api"

# MongoDB connection
MONGO_URL = "mongodb://mongo:LbwPeZMoFflpreeQGSoEnUATtNpFRXRG@turntable.proxy.rlwy.net:14941"
DB_NAME = "rotacrm"

# Test JWT tokens
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
INVALID_TOKEN = "invalid.token.format"

class TestDocumentDownloadEndpoint(unittest.TestCase):
    """Test class for document download endpoint"""
    
    def setUp(self):
        """Set up test environment"""
        # Use both API URLs for testing
        self.railway_api_url = RAILWAY_API_URL
        self.emergentagent_api_url = EMERGENTAGENT_API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # Connect to MongoDB to get a valid document ID for testing
        try:
            mongo_client = MongoClient(MONGO_URL)
            db = mongo_client[DB_NAME]
            document = db.documents.find_one({})
            if document:
                self.valid_document_id = document.get("id")
                self.client_id = document.get("client_id")
                logger.info(f"Found valid document ID: {self.valid_document_id} for client: {self.client_id}")
            else:
                self.valid_document_id = "non_existent_id"
                self.client_id = "non_existent_client_id"
                logger.warning("No documents found in database, using dummy ID for tests")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            self.valid_document_id = "non_existent_id"
            self.client_id = "non_existent_client_id"
        
        # Invalid document ID for testing error cases
        self.invalid_document_id = "invalid_document_id_" + str(uuid.uuid4())
    
    def test_download_document_with_admin(self):
        """Test document download with admin authentication"""
        logger.info("\n=== Testing /api/documents/{id}/download with admin authentication ===")
        
        # Test with Railway API URL
        url = f"{self.railway_api_url}/documents/{self.valid_document_id}/download"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code (Railway): {response.status_code}")
            
            # Check if the document exists in the database
            if self.valid_document_id == "non_existent_id":
                # If we couldn't find a document in setup, expect 404
                self.assertEqual(response.status_code, 404)
                logger.info("✅ Admin correctly gets 404 for non-existent document (Railway)")
            else:
                # Should get 200 OK or 404 Not Found (if document doesn't exist)
                self.assertIn(response.status_code, [200, 404])
                
                if response.status_code == 200:
                    # Check Content-Type header
                    self.assertIn("application/pdf", response.headers.get("Content-Type", ""))
                    
                    # Check Content-Disposition header
                    self.assertIn("attachment", response.headers.get("Content-Disposition", ""))
                    
                    # Check Content-Length header
                    self.assertIsNotNone(response.headers.get("Content-Length"))
                    self.assertGreater(int(response.headers.get("Content-Length", "0")), 0)
                    
                    # Check response content
                    self.assertGreater(len(response.content), 0)
                    
                    logger.info("✅ Admin can download document successfully (Railway)")
                elif response.status_code == 404:
                    logger.info("⚠️ Document not found in Railway database")
        except Exception as e:
            logger.error(f"❌ Error testing document download with admin (Railway): {str(e)}")
            raise
        
        # Test with EmergentAgent API URL
        url = f"{self.emergentagent_api_url}/documents/{self.valid_document_id}/download"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code (EmergentAgent): {response.status_code}")
            
            # Check if the document exists in the database
            if self.valid_document_id == "non_existent_id":
                # If we couldn't find a document in setup, expect 404
                self.assertEqual(response.status_code, 404)
                logger.info("✅ Admin correctly gets 404 for non-existent document (EmergentAgent)")
            else:
                # Should get 200 OK or 404 Not Found (if document doesn't exist)
                self.assertIn(response.status_code, [200, 404])
                
                if response.status_code == 200:
                    # Check Content-Type header
                    self.assertIn("application/pdf", response.headers.get("Content-Type", ""))
                    
                    # Check Content-Disposition header
                    self.assertIn("attachment", response.headers.get("Content-Disposition", ""))
                    
                    # Check Content-Length header
                    self.assertIsNotNone(response.headers.get("Content-Length"))
                    self.assertGreater(int(response.headers.get("Content-Length", "0")), 0)
                    
                    # Check response content
                    self.assertGreater(len(response.content), 0)
                    
                    logger.info("✅ Admin can download document successfully (EmergentAgent)")
                elif response.status_code == 404:
                    logger.info("⚠️ Document not found in EmergentAgent database")
        except Exception as e:
            logger.error(f"❌ Error testing document download with admin (EmergentAgent): {str(e)}")
            raise
    
    def test_download_document_with_client(self):
        """Test document download with client authentication"""
        logger.info("\n=== Testing /api/documents/{id}/download with client authentication ===")
        
        # Test with Railway API URL
        url = f"{self.railway_api_url}/documents/{self.valid_document_id}/download"
        
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status code (Railway): {response.status_code}")
            
            # Check if the document exists in the database
            if self.valid_document_id == "non_existent_id":
                # If we couldn't find a document in setup, expect 404
                self.assertEqual(response.status_code, 404)
                logger.info("✅ Client correctly gets 404 for non-existent document (Railway)")
            else:
                # If document exists but doesn't belong to this client, expect 403
                # If document belongs to this client, expect 200
                self.assertIn(response.status_code, [200, 403, 404])
                
                if response.status_code == 200:
                    # Check Content-Type header
                    self.assertIn("application/pdf", response.headers.get("Content-Type", ""))
                    
                    # Check Content-Disposition header
                    self.assertIn("attachment", response.headers.get("Content-Disposition", ""))
                    
                    # Check Content-Length header
                    self.assertIsNotNone(response.headers.get("Content-Length"))
                    self.assertGreater(int(response.headers.get("Content-Length", "0")), 0)
                    
                    # Check response content
                    self.assertGreater(len(response.content), 0)
                    
                    logger.info("✅ Client can download their own document successfully (Railway)")
                elif response.status_code == 403:
                    # If 403, document doesn't belong to this client
                    logger.info("✅ Client correctly gets 403 for document they don't own (Railway)")
                elif response.status_code == 404:
                    logger.info("⚠️ Document not found in Railway database")
        except Exception as e:
            logger.error(f"❌ Error testing document download with client (Railway): {str(e)}")
            raise
        
        # Test with EmergentAgent API URL
        url = f"{self.emergentagent_api_url}/documents/{self.valid_document_id}/download"
        
        try:
            response = requests.get(url, headers=self.headers_client)
            logger.info(f"Client response status code (EmergentAgent): {response.status_code}")
            
            # Check if the document exists in the database
            if self.valid_document_id == "non_existent_id":
                # If we couldn't find a document in setup, expect 404
                self.assertEqual(response.status_code, 404)
                logger.info("✅ Client correctly gets 404 for non-existent document (EmergentAgent)")
            else:
                # If document exists but doesn't belong to this client, expect 403
                # If document belongs to this client, expect 200
                self.assertIn(response.status_code, [200, 403, 404])
                
                if response.status_code == 200:
                    # Check Content-Type header
                    self.assertIn("application/pdf", response.headers.get("Content-Type", ""))
                    
                    # Check Content-Disposition header
                    self.assertIn("attachment", response.headers.get("Content-Disposition", ""))
                    
                    # Check Content-Length header
                    self.assertIsNotNone(response.headers.get("Content-Length"))
                    self.assertGreater(int(response.headers.get("Content-Length", "0")), 0)
                    
                    # Check response content
                    self.assertGreater(len(response.content), 0)
                    
                    logger.info("✅ Client can download their own document successfully (EmergentAgent)")
                elif response.status_code == 403:
                    # If 403, document doesn't belong to this client
                    logger.info("✅ Client correctly gets 403 for document they don't own (EmergentAgent)")
                elif response.status_code == 404:
                    logger.info("⚠️ Document not found in EmergentAgent database")
        except Exception as e:
            logger.error(f"❌ Error testing document download with client (EmergentAgent): {str(e)}")
            raise
    
    def test_download_document_with_invalid_id(self):
        """Test document download with invalid document ID"""
        logger.info("\n=== Testing /api/documents/{id}/download with invalid document ID ===")
        
        # Test with Railway API URL
        url = f"{self.railway_api_url}/documents/{self.invalid_document_id}/download"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Invalid ID response status code (Railway): {response.status_code}")
            
            # Should get 404 Not Found
            self.assertEqual(response.status_code, 404)
            
            # Check error message
            error_data = response.json()
            self.assertIn("detail", error_data)
            self.assertEqual(error_data["detail"], "Document not found")
            
            logger.info("✅ Invalid document ID correctly returns 404 (Railway)")
        except Exception as e:
            logger.error(f"❌ Error testing document download with invalid ID (Railway): {str(e)}")
            raise
        
        # Test with EmergentAgent API URL
        url = f"{self.emergentagent_api_url}/documents/{self.invalid_document_id}/download"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Invalid ID response status code (EmergentAgent): {response.status_code}")
            
            # Should get 404 Not Found
            self.assertEqual(response.status_code, 404)
            
            # Check error message
            error_data = response.json()
            self.assertIn("detail", error_data)
            self.assertEqual(error_data["detail"], "Document not found")
            
            logger.info("✅ Invalid document ID correctly returns 404 (EmergentAgent)")
        except Exception as e:
            logger.error(f"❌ Error testing document download with invalid ID (EmergentAgent): {str(e)}")
            raise
    
    def test_download_document_with_invalid_token(self):
        """Test document download with invalid authentication token"""
        logger.info("\n=== Testing /api/documents/{id}/download with invalid token ===")
        
        # Test with Railway API URL
        url = f"{self.railway_api_url}/documents/{self.valid_document_id}/download"
        
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status code (Railway): {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ Invalid token correctly returns 401 (Railway)")
        except Exception as e:
            logger.error(f"❌ Error testing document download with invalid token (Railway): {str(e)}")
            raise
        
        # Test with EmergentAgent API URL
        url = f"{self.emergentagent_api_url}/documents/{self.valid_document_id}/download"
        
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status code (EmergentAgent): {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ Invalid token correctly returns 401 (EmergentAgent)")
        except Exception as e:
            logger.error(f"❌ Error testing document download with invalid token (EmergentAgent): {str(e)}")
            raise
    
    def test_download_document_with_no_auth(self):
        """Test document download with no authentication"""
        logger.info("\n=== Testing /api/documents/{id}/download with no authentication ===")
        
        # Test with Railway API URL
        url = f"{self.railway_api_url}/documents/{self.valid_document_id}/download"
        
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code (Railway): {response.status_code}")
            
            # Should get 403 Not authenticated
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ No authentication correctly returns 403 (Railway)")
        except Exception as e:
            logger.error(f"❌ Error testing document download with no auth (Railway): {str(e)}")
            raise
        
        # Test with EmergentAgent API URL
        url = f"{self.emergentagent_api_url}/documents/{self.valid_document_id}/download"
        
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No auth response status code (EmergentAgent): {response.status_code}")
            
            # Should get 403 Not authenticated
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ No authentication correctly returns 403 (EmergentAgent)")
        except Exception as e:
            logger.error(f"❌ Error testing document download with no auth (EmergentAgent): {str(e)}")
            raise

if __name__ == "__main__":
    unittest.main()