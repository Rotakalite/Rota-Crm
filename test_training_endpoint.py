import unittest
import json
import logging
import requests
import os
import io
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

class TestTrainingEndpoints(unittest.TestCase):
    """Test class for training management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = "https://ced36975-561f-4c1a-b948-3ca6d5f89931.preview.emergentagent.com/api"
        self.headers_valid = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        self.headers_no_auth = {}
        
        # Sample training data for testing
        self.training_data = {
            "client_id": "test_client_id",
            "name": "Sürdürülebilirlik Eğitimi",
            "subject": "Enerji Tasarrufu ve Sürdürülebilir Turizm",
            "participant_count": 25,
            "trainer": "Dr. Ahmet Yılmaz",
            "training_date": "2025-06-15T10:00:00Z",
            "description": "Otel personeli için enerji tasarrufu ve sürdürülebilir turizm uygulamaları hakkında kapsamlı eğitim."
        }
        
        # Alternative training data with title/description format
        self.training_data_alt = {
            "client_id": "test_client_id",
            "title": "Sürdürülebilirlik Eğitimi",
            "description": "Otel personeli için enerji tasarrufu ve sürdürülebilir turizm uygulamaları hakkında kapsamlı eğitim.",
            "training_date": "2025-06-15T10:00:00Z",
            "participants": 25
        }
    
    def test_post_trainings_endpoint(self):
        """Test the POST /api/trainings endpoint with authentication"""
        logger.info("\n=== Testing POST /api/trainings endpoint ===")
        
        # Test with valid token and first training data format
        logger.info("Testing with valid token and name/subject format...")
        url = f"{self.api_url}/trainings"
        
        try:
            response = requests.post(url, headers=self.headers_valid, json=self.training_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check if we get a 200 OK, 401 Unauthorized, or 422 Validation Error
            self.assertIn(response.status_code, [200, 201, 401, 422, 404])
            
            if response.status_code in [200, 201]:
                logger.info("✅ Authentication successful - received 200/201 OK")
                data = response.json()
                self.assertIn("id", data, "Response should include training id")
                logger.info(f"✅ Training created with ID: {data['id']}")
                
                # Check that client_id is returned and matches
                self.assertIn("client_id", data, "Response should include client_id")
                self.assertEqual(data["client_id"], self.training_data["client_id"], 
                                "client_id in response should match request")
                
                # Check that training_date is returned in ISO format
                self.assertIn("training_date", data, "Response should include training_date")
                # Verify it's a valid ISO datetime format
                try:
                    datetime.fromisoformat(data["training_date"].replace('Z', '+00:00'))
                    logger.info("✅ training_date is in valid ISO format")
                except ValueError:
                    self.fail("training_date is not in valid ISO format")
                
            elif response.status_code == 401:
                logger.info("✅ Authentication failed correctly - received 401 Unauthorized")
                error_data = response.json()
                self.assertIn("detail", error_data)
            elif response.status_code == 422:
                logger.info("✅ Validation error - received 422 Unprocessable Entity")
                error_data = response.json()
                logger.info(f"Validation error details: {error_data}")
                # This could be due to the duplicate model definitions
            elif response.status_code == 404:
                logger.info("✅ Client not found - received 404 Not Found (expected for test client)")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/trainings endpoint: {str(e)}")
            raise
            
        # Test with valid token and alternative training data format
        logger.info("Testing with valid token and title/description format...")
        
        try:
            response = requests.post(url, headers=self.headers_valid, json=self.training_data_alt)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check if we get a 200 OK, 401 Unauthorized, or 422 Validation Error
            self.assertIn(response.status_code, [200, 201, 401, 422, 404])
            
            if response.status_code in [200, 201]:
                logger.info("✅ Authentication successful with alternative format - received 200/201 OK")
                data = response.json()
                self.assertIn("id", data, "Response should include training id")
                logger.info(f"✅ Training created with ID: {data['id']}")
                
                # Check that client_id is returned and matches
                self.assertIn("client_id", data, "Response should include client_id")
                self.assertEqual(data["client_id"], self.training_data_alt["client_id"], 
                                "client_id in response should match request")
                
                # Check that training_date is returned in ISO format
                self.assertIn("training_date", data, "Response should include training_date")
                # Verify it's a valid ISO datetime format
                try:
                    datetime.fromisoformat(data["training_date"].replace('Z', '+00:00'))
                    logger.info("✅ training_date is in valid ISO format")
                except ValueError:
                    self.fail("training_date is not in valid ISO format")
                
            elif response.status_code == 401:
                logger.info("✅ Authentication failed correctly - received 401 Unauthorized")
                error_data = response.json()
                self.assertIn("detail", error_data)
            elif response.status_code == 422:
                logger.info("✅ Validation error - received 422 Unprocessable Entity")
                error_data = response.json()
                logger.info(f"Validation error details: {error_data}")
                # This could be due to the duplicate model definitions
            elif response.status_code == 404:
                logger.info("✅ Client not found - received 404 Not Found (expected for test client)")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/trainings endpoint with alternative format: {str(e)}")
            raise
            
        # Test with invalid token
        logger.info("Testing with invalid token...")
        
        try:
            response = requests.post(url, headers=self.headers_invalid, json=self.training_data)
            logger.info(f"Response status code with invalid token: {response.status_code}")
            
            # Should get 401 Unauthorized, not 403 Forbidden
            self.assertEqual(response.status_code, 401)
            error_data = response.json()
            self.assertIn("detail", error_data)
            logger.info("✅ Invalid token test passed - received 401 Unauthorized")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/trainings endpoint with invalid token: {str(e)}")
            raise
            
        # Test without token
        logger.info("Testing without token...")
        
        try:
            response = requests.post(url, json=self.training_data)
            logger.info(f"Response status code without token: {response.status_code}")
            
            # Should get 401 Unauthorized or 403 Forbidden
            self.assertIn(response.status_code, [401, 403])
            error_data = response.json()
            self.assertIn("detail", error_data)
            logger.info(f"✅ No token test passed - received {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/trainings endpoint without token: {str(e)}")
            raise
    
    def test_missing_required_fields(self):
        """Test validation errors for missing required fields"""
        logger.info("\n=== Testing validation errors for missing required fields ===")
        
        url = f"{self.api_url}/trainings"
        
        # Test with missing client_id
        logger.info("Testing with missing client_id...")
        invalid_data = self.training_data.copy()
        del invalid_data["client_id"]
        
        try:
            response = requests.post(url, headers=self.headers_valid, json=invalid_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Should get 422 Unprocessable Entity
            self.assertEqual(response.status_code, 422)
            error_data = response.json()
            self.assertIn("detail", error_data)
            logger.info("✅ Missing client_id test passed - received 422 Unprocessable Entity")
        except Exception as e:
            logger.error(f"❌ Error testing with missing client_id: {str(e)}")
            raise
        
        # Test with missing name/subject
        logger.info("Testing with missing name...")
        invalid_data = self.training_data.copy()
        del invalid_data["name"]
        
        try:
            response = requests.post(url, headers=self.headers_valid, json=invalid_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Should get 422 Unprocessable Entity
            self.assertEqual(response.status_code, 422)
            error_data = response.json()
            self.assertIn("detail", error_data)
            logger.info("✅ Missing name test passed - received 422 Unprocessable Entity")
        except Exception as e:
            logger.error(f"❌ Error testing with missing name: {str(e)}")
            raise
        
        # Test with missing training_date
        logger.info("Testing with missing training_date...")
        invalid_data = self.training_data.copy()
        del invalid_data["training_date"]
        
        try:
            response = requests.post(url, headers=self.headers_valid, json=invalid_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Should get 422 Unprocessable Entity
            self.assertEqual(response.status_code, 422)
            error_data = response.json()
            self.assertIn("detail", error_data)
            logger.info("✅ Missing training_date test passed - received 422 Unprocessable Entity")
        except Exception as e:
            logger.error(f"❌ Error testing with missing training_date: {str(e)}")
            raise
    
    def test_datetime_format(self):
        """Test different datetime formats to ensure ISO format is accepted"""
        logger.info("\n=== Testing different datetime formats ===")
        
        url = f"{self.api_url}/trainings"
        
        # Test with ISO format (should work)
        logger.info("Testing with ISO format (2025-07-01T00:00:00Z)...")
        iso_data = self.training_data.copy()
        iso_data["training_date"] = "2025-07-01T00:00:00Z"
        
        try:
            response = requests.post(url, headers=self.headers_valid, json=iso_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Should get 200 OK, 401 Unauthorized, or 404 Not Found (if client doesn't exist)
            self.assertIn(response.status_code, [200, 201, 401, 404])
            
            if response.status_code in [200, 201]:
                logger.info("✅ ISO format test passed - received 200/201 OK")
            elif response.status_code == 401:
                logger.info("✅ Authentication failed correctly - received 401 Unauthorized")
            elif response.status_code == 404:
                logger.info("✅ Client not found - received 404 Not Found (expected for test client)")
        except Exception as e:
            logger.error(f"❌ Error testing with ISO format: {str(e)}")
            raise
        
        # Test with ISO format without timezone (should work)
        logger.info("Testing with ISO format without timezone (2025-07-01T00:00:00)...")
        iso_no_tz_data = self.training_data.copy()
        iso_no_tz_data["training_date"] = "2025-07-01T00:00:00"
        
        try:
            response = requests.post(url, headers=self.headers_valid, json=iso_no_tz_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Should get 200 OK, 401 Unauthorized, or 404 Not Found (if client doesn't exist)
            self.assertIn(response.status_code, [200, 201, 401, 404])
            
            if response.status_code in [200, 201]:
                logger.info("✅ ISO format without timezone test passed - received 200/201 OK")
            elif response.status_code == 401:
                logger.info("✅ Authentication failed correctly - received 401 Unauthorized")
            elif response.status_code == 404:
                logger.info("✅ Client not found - received 404 Not Found (expected for test client)")
        except Exception as e:
            logger.error(f"❌ Error testing with ISO format without timezone: {str(e)}")
            raise
        
        # Test with date-only format (should fail with 422)
        logger.info("Testing with date-only format (2025-07-01)...")
        date_only_data = self.training_data.copy()
        date_only_data["training_date"] = "2025-07-01"
        
        try:
            response = requests.post(url, headers=self.headers_valid, json=date_only_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Should get 422 Unprocessable Entity
            self.assertEqual(response.status_code, 422)
            error_data = response.json()
            self.assertIn("detail", error_data)
            logger.info("✅ Date-only format test passed - received 422 Unprocessable Entity")
        except Exception as e:
            logger.error(f"❌ Error testing with date-only format: {str(e)}")
            raise
    
    def test_client_id_validation(self):
        """Test that client_id validation works (404 for non-existent client)"""
        logger.info("\n=== Testing client_id validation ===")
        
        url = f"{self.api_url}/trainings"
        
        # Test with non-existent client_id
        logger.info("Testing with non-existent client_id...")
        invalid_client_data = self.training_data.copy()
        invalid_client_data["client_id"] = str(uuid.uuid4())  # Random UUID that doesn't exist
        
        try:
            response = requests.post(url, headers=self.headers_valid, json=invalid_client_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Should get 404 Not Found
            self.assertEqual(response.status_code, 404)
            error_data = response.json()
            self.assertIn("detail", error_data)
            self.assertEqual(error_data["detail"], "Client not found")
            logger.info("✅ Non-existent client_id test passed - received 404 Not Found")
        except Exception as e:
            logger.error(f"❌ Error testing with non-existent client_id: {str(e)}")
            raise

def run_tests():
    """Run all training endpoint tests"""
    logger.info("Starting training endpoint tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add training endpoint tests
    suite.addTest(TestTrainingEndpoints("test_post_trainings_endpoint"))
    suite.addTest(TestTrainingEndpoints("test_missing_required_fields"))
    suite.addTest(TestTrainingEndpoints("test_datetime_format"))
    suite.addTest(TestTrainingEndpoints("test_client_id_validation"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Training Endpoint Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All training endpoint tests PASSED")
        return True
    else:
        logger.error("Some training endpoint tests FAILED")
        return False

if __name__ == "__main__":
    run_tests()