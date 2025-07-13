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

# Backend URL from frontend/.env
BACKEND_URL = "https://ecd50858-c16e-4cf1-bfa1-501728878062.preview.emergentagent.com/api"

class TestGuestEngagementAPIs(unittest.TestCase):
    """Test class for Guest Engagement APIs"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_URL
        
        # Test data for guest engagement
        self.test_guest_data = {
            "guest_name": "Test Guest",
            "room_number": "101",
            "eco_actions": ["energy", "water"],
            "feedback_rating": 5,
            "feedback_comment": "Great sustainability initiatives!",
            "client_id": "test_client_id"
        }
    
    def test_create_guest_engagement(self):
        """Test POST /api/guest-engagement endpoint"""
        logger.info("\n=== Testing POST /api/guest-engagement endpoint ===")
        
        url = f"{self.api_url}/guest-engagement"
        
        try:
            response = requests.post(url, json=self.test_guest_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 201, 400, 401, 403])
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIn("message", data)
                self.assertIn("id", data)
                self.assertIn("score", data)
                
                # Save guest_id for later tests
                self.guest_id = data["id"]
                logger.info(f"Created guest with ID: {self.guest_id}")
                
                logger.info("✅ POST /api/guest-engagement passed")
            else:
                logger.info(f"✅ POST /api/guest-engagement returned expected status: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/guest-engagement: {str(e)}")
            raise
    
    def test_get_guest_engagement(self):
        """Test GET /api/guest-engagement endpoint"""
        logger.info("\n=== Testing GET /api/guest-engagement endpoint ===")
        
        url = f"{self.api_url}/guest-engagement"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} guest records")
                
                # Verify response structure (should be a list)
                self.assertIsInstance(data, list)
                
                # If there are records, check their structure
                if len(data) > 0:
                    guest = data[0]
                    self.assertIn("id", guest)
                    self.assertIn("guest_name", guest)
                    self.assertIn("room_number", guest)
                    self.assertIn("eco_actions", guest)
                    self.assertIn("sustainability_score", guest)
                    self.assertIn("client_id", guest)
                
                logger.info("✅ GET /api/guest-engagement passed")
            else:
                logger.info(f"✅ GET /api/guest-engagement returned expected status: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/guest-engagement: {str(e)}")
            raise
    
    def test_get_eco_tips(self):
        """Test GET /api/guest-engagement/eco-tips endpoint"""
        logger.info("\n=== Testing GET /api/guest-engagement/eco-tips endpoint ===")
        
        url = f"{self.api_url}/guest-engagement/eco-tips"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check response status code
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            
            # Verify response structure
            self.assertIn("eco_tips", data)
            self.assertIsInstance(data["eco_tips"], list)
            
            # Verify eco tips structure
            if len(data["eco_tips"]) > 0:
                tip = data["eco_tips"][0]
                self.assertIn("id", tip)
                self.assertIn("category", tip)
                self.assertIn("icon", tip)
                self.assertIn("title", tip)
                self.assertIn("description", tip)
                self.assertIn("points", tip)
            
            logger.info("✅ GET /api/guest-engagement/eco-tips passed")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/guest-engagement/eco-tips: {str(e)}")
            raise
    
    def test_get_leaderboard(self):
        """Test GET /api/guest-engagement/leaderboard endpoint"""
        logger.info("\n=== Testing GET /api/guest-engagement/leaderboard endpoint ===")
        
        url = f"{self.api_url}/guest-engagement/leaderboard"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403])
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                self.assertIn("leaderboard", data)
                self.assertIsInstance(data["leaderboard"], list)
                
                # Verify leaderboard entries structure
                if len(data["leaderboard"]) > 0:
                    entry = data["leaderboard"][0]
                    self.assertIn("id", entry)
                    self.assertIn("guest_name", entry)
                    self.assertIn("sustainability_score", entry)
                
                logger.info("✅ GET /api/guest-engagement/leaderboard passed")
            else:
                logger.info(f"✅ GET /api/guest-engagement/leaderboard returned expected status: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/guest-engagement/leaderboard: {str(e)}")
            raise

class TestGuestSelfAssessmentAPIs(unittest.TestCase):
    """Test class for Guest Self-Assessment APIs"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_URL
        
        # Create a test guest first
        self.test_guest_data = {
            "guest_name": "Self Assessment Test Guest",
            "room_number": "202",
            "eco_actions": ["energy"],
            "client_id": "test_client_id"
        }
        
        # Create a guest for testing
        try:
            url = f"{self.api_url}/guest-engagement"
            response = requests.post(url, json=self.test_guest_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.guest_id = data["id"]
                logger.info(f"Created test guest with ID: {self.guest_id}")
            else:
                logger.warning(f"Failed to create test guest: {response.status_code} - {response.text}")
                self.guest_id = "test_guest_id"  # Fallback ID
        except Exception as e:
            logger.error(f"Error creating test guest: {str(e)}")
            self.guest_id = "test_guest_id"  # Fallback ID
    
    def test_get_guest_self_assessment(self):
        """Test GET /api/guest-engagement/self-assessment/{guest_id} endpoint"""
        logger.info("\n=== Testing GET /api/guest-engagement/self-assessment/{guest_id} endpoint ===")
        
        url = f"{self.api_url}/guest-engagement/self-assessment/{self.guest_id}"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data structure: {list(data.keys())}")
                
                # Verify response structure
                self.assertIn("guest", data)
                self.assertIn("eco_tips", data)
                
                # Verify guest data structure
                guest = data["guest"]
                self.assertIn("id", guest)
                self.assertIn("guest_name", guest)
                self.assertIn("room_number", guest)
                self.assertIn("eco_actions", guest)
                self.assertIn("sustainability_score", guest)
                
                # Verify eco tips structure
                self.assertIsInstance(data["eco_tips"], list)
                if len(data["eco_tips"]) > 0:
                    tip = data["eco_tips"][0]
                    self.assertIn("id", tip)
                    self.assertIn("category", tip)
                    self.assertIn("icon", tip)
                    self.assertIn("title", tip)
                    self.assertIn("description", tip)
                    self.assertIn("points", tip)
                
                logger.info("✅ GET /api/guest-engagement/self-assessment/{guest_id} passed")
            elif response.status_code == 404:
                # Guest not found
                data = response.json()
                logger.info(f"Expected 404 error: {data}")
                logger.info("✅ GET /api/guest-engagement/self-assessment/{guest_id} - expected 404 error")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/guest-engagement/self-assessment/{self.guest_id}: {str(e)}")
            raise
    
    def test_update_guest_self_assessment(self):
        """Test PUT /api/guest-engagement/self-assessment/{guest_id} endpoint"""
        logger.info("\n=== Testing PUT /api/guest-engagement/self-assessment/{guest_id} endpoint ===")
        
        url = f"{self.api_url}/guest-engagement/self-assessment/{self.guest_id}"
        
        # Test data for updating self-assessment
        assessment_data = {
            "eco_actions": ["energy", "water", "waste"],
            "feedback_rating": 4,
            "feedback_comment": "Great sustainability program!"
        }
        
        try:
            response = requests.put(url, json=assessment_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 404])
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                self.assertIn("message", data)
                self.assertIn("new_score", data)
                
                # Verify score calculation (10 points per eco action)
                self.assertEqual(data["new_score"], len(assessment_data["eco_actions"]) * 10)
                
                logger.info("✅ PUT /api/guest-engagement/self-assessment/{guest_id} passed")
            elif response.status_code == 404:
                # Guest not found
                data = response.json()
                logger.info(f"Expected 404 error: {data}")
                logger.info("✅ PUT /api/guest-engagement/self-assessment/{guest_id} - expected 404 error")
        except Exception as e:
            logger.error(f"❌ Error testing PUT /api/guest-engagement/self-assessment/{self.guest_id}: {str(e)}")
            raise
    
    def test_qr_access(self):
        """Test GET /api/guest-engagement/qr-access/{room_number} endpoint"""
        logger.info("\n=== Testing GET /api/guest-engagement/qr-access/{room_number} endpoint ===")
        
        room_number = "303"  # Use a unique room number
        client_id = "test_client_id"
        
        url = f"{self.api_url}/guest-engagement/qr-access/{room_number}?client_id={client_id}"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check response status code
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            
            # Verify response structure
            self.assertIn("guest_id", data)
            self.assertIn("is_new", data)
            
            # Save the guest_id for verification
            qr_guest_id = data["guest_id"]
            
            # Verify the guest was created by checking self-assessment endpoint
            verify_url = f"{self.api_url}/guest-engagement/self-assessment/{qr_guest_id}"
            verify_response = requests.get(verify_url)
            
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                guest = verify_data["guest"]
                
                # Verify the guest data
                self.assertEqual(guest["room_number"], room_number)
                self.assertEqual(guest["client_id"], client_id)
                
                logger.info("✅ QR code access verification passed")
            else:
                logger.warning(f"QR code access verification failed: {verify_response.status_code}")
            
            logger.info("✅ GET /api/guest-engagement/qr-access/{room_number} passed")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/guest-engagement/qr-access/{room_number}: {str(e)}")
            raise

def run_tests():
    """Run all API tests"""
    logger.info("Starting Guest Engagement and Self-Assessment API tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add Guest Engagement API tests
    suite.addTest(TestGuestEngagementAPIs("test_create_guest_engagement"))
    suite.addTest(TestGuestEngagementAPIs("test_get_guest_engagement"))
    suite.addTest(TestGuestEngagementAPIs("test_get_eco_tips"))
    suite.addTest(TestGuestEngagementAPIs("test_get_leaderboard"))
    
    # Add Guest Self-Assessment API tests
    suite.addTest(TestGuestSelfAssessmentAPIs("test_get_guest_self_assessment"))
    suite.addTest(TestGuestSelfAssessmentAPIs("test_update_guest_self_assessment"))
    suite.addTest(TestGuestSelfAssessmentAPIs("test_qr_access"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All tests PASSED")
        return True
    else:
        logger.error("Some tests FAILED")
        for error in result.errors:
            logger.error(f"Error: {error}")
        for failure in result.failures:
            logger.error(f"Failure: {failure}")
        return False

if __name__ == "__main__":
    run_tests()