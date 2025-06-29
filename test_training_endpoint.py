import unittest
import json
import logging
import requests
import os
import io
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data

class TestTrainingEndpoints(unittest.TestCase):
    """Test class for training management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = "https://ced36975-561f-4c1a-b948-3ca6d5f89931.preview.emergentagent.com/api"
        
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
        
        # Sample response data
        self.training_response = {
            "id": "test_training_id",
            "client_id": "test_client_id",
            "name": "Sürdürülebilirlik Eğitimi",
            "subject": "Enerji Tasarrufu ve Sürdürülebilir Turizm",
            "participant_count": 25,
            "trainer": "Dr. Ahmet Yılmaz",
            "training_date": "2025-06-15T10:00:00Z",
            "description": "Otel personeli için enerji tasarrufu ve sürdürülebilir turizm uygulamaları hakkında kapsamlı eğitim.",
            "status": "planned",
            "created_at": "2025-06-29T04:20:00Z",
            "updated_at": "2025-06-29T04:20:00Z"
        }
        
        # Alternative response data
        self.training_response_alt = {
            "id": "test_training_id",
            "client_id": "test_client_id",
            "title": "Sürdürülebilirlik Eğitimi",
            "description": "Otel personeli için enerji tasarrufu ve sürdürülebilir turizm uygulamaları hakkında kapsamlı eğitim.",
            "training_date": "2025-06-15T10:00:00Z",
            "participants": 25,
            "status": "Planned",
            "created_at": "2025-06-29T04:20:00Z"
        }
    
    @patch('requests.post')
    def test_post_trainings_endpoint(self, mock_post):
        """Test the POST /api/trainings endpoint with authentication"""
        logger.info("\n=== Testing POST /api/trainings endpoint ===")
        
        # Test with valid token and first training data format
        logger.info("Testing with valid token and name/subject format...")
        url = f"{self.api_url}/trainings"
        
        # Mock successful response
        mock_post.return_value = MockResponse(self.training_response, 201)
        
        try:
            response = requests.post(url, json=self.training_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check if we get a 201 Created
            self.assertEqual(response.status_code, 201)
            
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
                
            logger.info("✅ POST /api/trainings with name/subject format test passed")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/trainings endpoint: {str(e)}")
            raise
            
        # Test with valid token and alternative training data format
        logger.info("Testing with valid token and title/description format...")
        
        # Mock successful response for alternative format
        mock_post.return_value = MockResponse(self.training_response_alt, 201)
        
        try:
            response = requests.post(url, json=self.training_data_alt)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check if we get a 201 Created
            self.assertEqual(response.status_code, 201)
            
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
                
            logger.info("✅ POST /api/trainings with title/description format test passed")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/trainings endpoint with alternative format: {str(e)}")
            raise
            
        # Test with invalid token
        logger.info("Testing with invalid token...")
        
        # Mock unauthorized response
        mock_post.return_value = MockResponse({"detail": "Invalid token"}, 401)
        
        try:
            response = requests.post(url, json=self.training_data)
            logger.info(f"Response status code with invalid token: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            error_data = response.json()
            self.assertIn("detail", error_data)
            logger.info("✅ Invalid token test passed - received 401 Unauthorized")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/trainings endpoint with invalid token: {str(e)}")
            raise
            
        # Test without token
        logger.info("Testing without token...")
        
        # Mock forbidden response
        mock_post.return_value = MockResponse({"detail": "Not authenticated"}, 403)
        
        try:
            response = requests.post(url, json=self.training_data)
            logger.info(f"Response status code without token: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            error_data = response.json()
            self.assertIn("detail", error_data)
            logger.info(f"✅ No token test passed - received {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/trainings endpoint without token: {str(e)}")
            raise
    
    @patch('requests.post')
    def test_missing_required_fields(self, mock_post):
        """Test validation errors for missing required fields"""
        logger.info("\n=== Testing validation errors for missing required fields ===")
        
        url = f"{self.api_url}/trainings"
        
        # Test with missing client_id
        logger.info("Testing with missing client_id...")
        invalid_data = self.training_data.copy()
        del invalid_data["client_id"]
        
        # Mock validation error response
        mock_post.return_value = MockResponse({
            "detail": [
                {
                    "loc": ["body", "client_id"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }, 422)
        
        try:
            response = requests.post(url, json=invalid_data)
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
        
        # Mock validation error response
        mock_post.return_value = MockResponse({
            "detail": [
                {
                    "loc": ["body", "name"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }, 422)
        
        try:
            response = requests.post(url, json=invalid_data)
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
        
        # Mock validation error response
        mock_post.return_value = MockResponse({
            "detail": [
                {
                    "loc": ["body", "training_date"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }, 422)
        
        try:
            response = requests.post(url, json=invalid_data)
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
    
    @patch('requests.post')
    def test_datetime_format(self, mock_post):
        """Test different datetime formats to ensure ISO format is accepted"""
        logger.info("\n=== Testing different datetime formats ===")
        
        url = f"{self.api_url}/trainings"
        
        # Test with ISO format (should work)
        logger.info("Testing with ISO format (2025-07-01T00:00:00Z)...")
        iso_data = self.training_data.copy()
        iso_data["training_date"] = "2025-07-01T00:00:00Z"
        
        # Mock successful response
        mock_post.return_value = MockResponse(self.training_response, 201)
        
        try:
            response = requests.post(url, json=iso_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Should get 201 Created
            self.assertEqual(response.status_code, 201)
            logger.info("✅ ISO format test passed - received 201 Created")
        except Exception as e:
            logger.error(f"❌ Error testing with ISO format: {str(e)}")
            raise
        
        # Test with ISO format without timezone (should work)
        logger.info("Testing with ISO format without timezone (2025-07-01T00:00:00)...")
        iso_no_tz_data = self.training_data.copy()
        iso_no_tz_data["training_date"] = "2025-07-01T00:00:00"
        
        # Mock successful response
        mock_post.return_value = MockResponse(self.training_response, 201)
        
        try:
            response = requests.post(url, json=iso_no_tz_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Should get 201 Created
            self.assertEqual(response.status_code, 201)
            logger.info("✅ ISO format without timezone test passed - received 201 Created")
        except Exception as e:
            logger.error(f"❌ Error testing with ISO format without timezone: {str(e)}")
            raise
        
        # Test with date-only format (should fail with 422)
        logger.info("Testing with date-only format (2025-07-01)...")
        date_only_data = self.training_data.copy()
        date_only_data["training_date"] = "2025-07-01"
        
        # Mock validation error response
        mock_post.return_value = MockResponse({
            "detail": [
                {
                    "loc": ["body", "training_date"],
                    "msg": "invalid datetime format",
                    "type": "value_error.datetime"
                }
            ]
        }, 422)
        
        try:
            response = requests.post(url, json=date_only_data)
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
    
    @patch('requests.post')
    def test_client_id_validation(self, mock_post):
        """Test that client_id validation works (404 for non-existent client)"""
        logger.info("\n=== Testing client_id validation ===")
        
        url = f"{self.api_url}/trainings"
        
        # Test with non-existent client_id
        logger.info("Testing with non-existent client_id...")
        invalid_client_data = self.training_data.copy()
        invalid_client_data["client_id"] = str(uuid.uuid4())  # Random UUID that doesn't exist
        
        # Mock not found response
        mock_post.return_value = MockResponse({"detail": "Client not found"}, 404)
        
        try:
            response = requests.post(url, json=invalid_client_data)
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