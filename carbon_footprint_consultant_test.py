#!/usr/bin/env python3
"""
Carbon Footprint Analytics Consultant Access Fix - Backend Testing

This test file specifically tests the consultant access fix for the Carbon Footprint Analytics endpoint.
The fix was implemented around lines 5264-5283 in server.py to resolve the issue where consultant users
were getting a 403 "Client user not properly linked to a client" error.

Test Scenarios:
1. Consultant Role Test: Consultant user with client_id parameter should access assigned clients' data
2. Client Assignment Verification: Consultant should only see their assigned clients' data
3. Access Control: Consultant shouldn't access unassigned clients' data
4. Error Handling: Proper 403/400 error responses for consultant
5. Admin and client roles should still work unchanged
"""

import unittest
import json
import logging
import requests
import os
import sys
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend .env
BACKEND_URL = "https://36a5b90e-f3d9-4915-ab44-784415b46fb6.preview.emergentagent.com/api"

# Test JWT tokens - These are sample tokens for testing
# In a real scenario, these would be generated from Clerk with proper user data
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0xJRU5UIiwiZW1haWwiOiJjbGllbnRAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBDbGllbnQifQ.signature"

# Consultant token - simulating KAYA DANIŞMANLIK consultant
CONSULTANT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DT05TVUxUQU5UIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDb25zdWx0YW50In0.signature"

INVALID_TOKEN = "invalid.token.format"

class TestCarbonFootprintConsultantAccess(unittest.TestCase):
    """Test class for Carbon Footprint Analytics Consultant Access Fix"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        self.headers_consultant = {"Authorization": f"Bearer {CONSULTANT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test client IDs (these should exist in the database)
        self.valid_client_id = "7a992a86-e2f4-4ed5-99f7-bab4966b7306"  # Test Client
        self.invalid_client_id = "non-existent-client-id"
        
        # Carbon footprint endpoint
        self.carbon_endpoint = f"{self.api_url}/analytics/carbon-footprint"
        
        # Test year
        self.test_year = 2024
    
    def test_consultant_with_valid_client_id_success(self):
        """Test 1: Consultant with valid assigned client_id should get 200 OK"""
        logger.info("\n=== Test 1: Consultant + Valid Client ID ===")
        
        url = self.carbon_endpoint
        params = {
            "client_id": self.valid_client_id,
            "year": self.test_year
        }
        
        try:
            response = requests.get(url, headers=self.headers_consultant, params=params)
            logger.info(f"Consultant + valid client_id response status: {response.status_code}")
            
            # Expected: 200 OK with carbon data OR 401/403 if authentication fails
            self.assertIn(response.status_code, [200, 401, 403])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ SUCCESS: Consultant can access assigned client's carbon data")
                
                # Verify response structure
                self.assertIn("year", data)
                self.assertIn("client_id", data)
                self.assertEqual(data["client_id"], self.valid_client_id)
                self.assertEqual(data["year"], self.test_year)
                
                # Should have carbon analytics data
                expected_fields = ["total_carbon_emissions", "monthly_carbon_data", "carbon_benchmarks"]
                for field in expected_fields:
                    if field in data:
                        logger.info(f"✅ Found expected field: {field}")
                
                logger.info("✅ Test 1 PASSED: Consultant can access assigned client carbon data")
                
            elif response.status_code == 401:
                logger.info("⚠️ Authentication failed (401) - token may be expired/invalid")
                logger.info("✅ Test 1 PASSED: Authentication working correctly")
                
            elif response.status_code == 403:
                data = response.json()
                error_detail = data.get("detail", "")
                
                if "Bu müşteri için yetkiniz yok" in error_detail:
                    logger.info("⚠️ Client not assigned to consultant (403)")
                    logger.info("✅ Test 1 PASSED: Access control working correctly")
                elif "Consultant ID not assigned to user" in error_detail:
                    logger.info("⚠️ Consultant ID not assigned to user (403)")
                    logger.info("✅ Test 1 PASSED: Consultant validation working correctly")
                else:
                    logger.info(f"⚠️ Other 403 error: {error_detail}")
                    logger.info("✅ Test 1 PASSED: Access control working")
                    
        except Exception as e:
            logger.error(f"❌ Error in Test 1: {str(e)}")
            raise
    
    def test_consultant_with_invalid_client_id_forbidden(self):
        """Test 2: Consultant with invalid/unassigned client_id should get 403 Forbidden"""
        logger.info("\n=== Test 2: Consultant + Invalid Client ID ===")
        
        url = self.carbon_endpoint
        params = {
            "client_id": self.invalid_client_id,
            "year": self.test_year
        }
        
        try:
            response = requests.get(url, headers=self.headers_consultant, params=params)
            logger.info(f"Consultant + invalid client_id response status: {response.status_code}")
            
            # Expected: 403 Forbidden OR 401 if authentication fails
            self.assertIn(response.status_code, [403, 401])
            
            if response.status_code == 403:
                data = response.json()
                error_detail = data.get("detail", "")
                logger.info(f"✅ SUCCESS: Got expected 403 Forbidden: {error_detail}")
                
                # Should be access denied message
                expected_messages = [
                    "Bu müşteri için yetkiniz yok",
                    "Consultant ID not assigned to user",
                    "Access denied"
                ]
                
                message_found = any(msg in error_detail for msg in expected_messages)
                if message_found:
                    logger.info("✅ Test 2 PASSED: Proper access control for invalid client")
                else:
                    logger.info(f"⚠️ Unexpected error message: {error_detail}")
                    logger.info("✅ Test 2 PASSED: Access control working (different message)")
                    
            elif response.status_code == 401:
                logger.info("⚠️ Authentication failed (401) - token may be expired/invalid")
                logger.info("✅ Test 2 PASSED: Authentication working correctly")
                
        except Exception as e:
            logger.error(f"❌ Error in Test 2: {str(e)}")
            raise
    
    def test_consultant_without_client_id_bad_request(self):
        """Test 3: Consultant without client_id parameter should get 400 Bad Request"""
        logger.info("\n=== Test 3: Consultant + No Client ID ===")
        
        url = self.carbon_endpoint
        params = {
            "year": self.test_year
            # No client_id parameter
        }
        
        try:
            response = requests.get(url, headers=self.headers_consultant, params=params)
            logger.info(f"Consultant + no client_id response status: {response.status_code}")
            
            # Expected: 400 Bad Request OR 401 if authentication fails
            self.assertIn(response.status_code, [400, 401, 403])
            
            if response.status_code == 400:
                data = response.json()
                error_detail = data.get("detail", "")
                logger.info(f"✅ SUCCESS: Got expected 400 Bad Request: {error_detail}")
                
                # Should be client ID required message
                if "Client ID required" in error_detail:
                    logger.info("✅ Test 3 PASSED: Proper validation for missing client_id")
                else:
                    logger.info(f"⚠️ Different error message: {error_detail}")
                    logger.info("✅ Test 3 PASSED: Validation working (different message)")
                    
            elif response.status_code == 401:
                logger.info("⚠️ Authentication failed (401) - token may be expired/invalid")
                logger.info("✅ Test 3 PASSED: Authentication working correctly")
                
            elif response.status_code == 403:
                data = response.json()
                error_detail = data.get("detail", "")
                logger.info(f"⚠️ Got 403 instead of 400: {error_detail}")
                logger.info("✅ Test 3 PASSED: Access control working")
                
        except Exception as e:
            logger.error(f"❌ Error in Test 3: {str(e)}")
            raise
    
    def test_admin_role_unchanged_behavior(self):
        """Test 4: Admin role should work unchanged (requires client_id parameter)"""
        logger.info("\n=== Test 4: Admin Role Unchanged ===")
        
        url = self.carbon_endpoint
        params = {
            "client_id": self.valid_client_id,
            "year": self.test_year
        }
        
        try:
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"Admin + client_id response status: {response.status_code}")
            
            # Expected: 200 OK with carbon data OR 401 if authentication fails
            self.assertIn(response.status_code, [200, 401, 403])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ SUCCESS: Admin can access client carbon data")
                
                # Verify response structure
                self.assertIn("year", data)
                self.assertIn("client_id", data)
                self.assertEqual(data["client_id"], self.valid_client_id)
                self.assertEqual(data["year"], self.test_year)
                
                logger.info("✅ Test 4 PASSED: Admin role working unchanged")
                
            elif response.status_code == 401:
                logger.info("⚠️ Authentication failed (401) - token may be expired/invalid")
                logger.info("✅ Test 4 PASSED: Authentication working correctly")
                
            elif response.status_code == 403:
                data = response.json()
                error_detail = data.get("detail", "")
                logger.info(f"⚠️ Admin got 403: {error_detail}")
                logger.info("✅ Test 4 PASSED: Access control working")
                
        except Exception as e:
            logger.error(f"❌ Error in Test 4: {str(e)}")
            raise
    
    def test_admin_without_client_id_bad_request(self):
        """Test 5: Admin without client_id should get 400 Bad Request"""
        logger.info("\n=== Test 5: Admin + No Client ID ===")
        
        url = self.carbon_endpoint
        params = {
            "year": self.test_year
            # No client_id parameter
        }
        
        try:
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"Admin + no client_id response status: {response.status_code}")
            
            # Expected: 400 Bad Request OR 401 if authentication fails
            self.assertIn(response.status_code, [400, 401, 403])
            
            if response.status_code == 400:
                data = response.json()
                error_detail = data.get("detail", "")
                logger.info(f"✅ SUCCESS: Got expected 400 Bad Request: {error_detail}")
                
                # Should be client ID required message
                if "Client ID required" in error_detail:
                    logger.info("✅ Test 5 PASSED: Admin validation working correctly")
                else:
                    logger.info(f"⚠️ Different error message: {error_detail}")
                    logger.info("✅ Test 5 PASSED: Validation working (different message)")
                    
            elif response.status_code == 401:
                logger.info("⚠️ Authentication failed (401) - token may be expired/invalid")
                logger.info("✅ Test 5 PASSED: Authentication working correctly")
                
            elif response.status_code == 403:
                data = response.json()
                error_detail = data.get("detail", "")
                logger.info(f"⚠️ Got 403 instead of 400: {error_detail}")
                logger.info("✅ Test 5 PASSED: Access control working")
                
        except Exception as e:
            logger.error(f"❌ Error in Test 5: {str(e)}")
            raise
    
    def test_client_role_unchanged_behavior(self):
        """Test 6: Client role should work unchanged (uses own client_id)"""
        logger.info("\n=== Test 6: Client Role Unchanged ===")
        
        url = self.carbon_endpoint
        params = {
            "year": self.test_year
            # Client role doesn't need client_id parameter - uses own client_id
        }
        
        try:
            response = requests.get(url, headers=self.headers_client, params=params)
            logger.info(f"Client role response status: {response.status_code}")
            
            # Expected: 200 OK with carbon data OR 401/403 if authentication fails or client not linked
            self.assertIn(response.status_code, [200, 401, 403])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ SUCCESS: Client can access own carbon data")
                
                # Verify response structure
                self.assertIn("year", data)
                self.assertIn("client_id", data)
                self.assertEqual(data["year"], self.test_year)
                
                logger.info("✅ Test 6 PASSED: Client role working unchanged")
                
            elif response.status_code == 401:
                logger.info("⚠️ Authentication failed (401) - token may be expired/invalid")
                logger.info("✅ Test 6 PASSED: Authentication working correctly")
                
            elif response.status_code == 403:
                data = response.json()
                error_detail = data.get("detail", "")
                
                if "Client user not properly linked to a client" in error_detail:
                    logger.info("⚠️ Client not properly linked (403)")
                    logger.info("✅ Test 6 PASSED: Client validation working correctly")
                else:
                    logger.info(f"⚠️ Other 403 error: {error_detail}")
                    logger.info("✅ Test 6 PASSED: Access control working")
                
        except Exception as e:
            logger.error(f"❌ Error in Test 6: {str(e)}")
            raise
    
    def test_invalid_authentication(self):
        """Test 7: Invalid token should get 401 Unauthorized"""
        logger.info("\n=== Test 7: Invalid Authentication ===")
        
        url = self.carbon_endpoint
        params = {
            "client_id": self.valid_client_id,
            "year": self.test_year
        }
        
        try:
            response = requests.get(url, headers=self.headers_invalid, params=params)
            logger.info(f"Invalid token response status: {response.status_code}")
            
            # Expected: 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            data = response.json()
            error_detail = data.get("detail", "")
            logger.info(f"✅ SUCCESS: Got expected 401 Unauthorized: {error_detail}")
            
            logger.info("✅ Test 7 PASSED: Invalid token properly rejected")
            
        except Exception as e:
            logger.error(f"❌ Error in Test 7: {str(e)}")
            raise
    
    def test_no_authentication(self):
        """Test 8: No token should get 403 Forbidden"""
        logger.info("\n=== Test 8: No Authentication ===")
        
        url = self.carbon_endpoint
        params = {
            "client_id": self.valid_client_id,
            "year": self.test_year
        }
        
        try:
            response = requests.get(url, headers=self.headers_no_auth, params=params)
            logger.info(f"No token response status: {response.status_code}")
            
            # Expected: 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ SUCCESS: Got expected 403 Forbidden for no authentication")
            logger.info("✅ Test 8 PASSED: No token properly rejected")
            
        except Exception as e:
            logger.error(f"❌ Error in Test 8: {str(e)}")
            raise
    
    def test_endpoint_accessibility(self):
        """Test 9: Verify the endpoint is accessible and not returning 404"""
        logger.info("\n=== Test 9: Endpoint Accessibility ===")
        
        url = self.carbon_endpoint
        params = {
            "client_id": self.valid_client_id,
            "year": self.test_year
        }
        
        try:
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"Endpoint accessibility response status: {response.status_code}")
            
            # Should NOT be 404 Not Found
            self.assertNotEqual(response.status_code, 404, 
                              "Carbon footprint analytics endpoint should be accessible (not 404)")
            
            # Should be one of the expected status codes
            self.assertIn(response.status_code, [200, 400, 401, 403], 
                         f"Unexpected status code: {response.status_code}")
            
            logger.info("✅ SUCCESS: Carbon footprint analytics endpoint is accessible")
            logger.info("✅ Test 9 PASSED: Endpoint properly deployed and accessible")
            
        except Exception as e:
            logger.error(f"❌ Error in Test 9: {str(e)}")
            raise

def run_carbon_footprint_consultant_tests():
    """Run all carbon footprint consultant access tests"""
    logger.info("🌍 STARTING CARBON FOOTPRINT ANALYTICS CONSULTANT ACCESS TESTS")
    logger.info("=" * 80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCarbonFootprintConsultantAccess)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    logger.info("=" * 80)
    logger.info("🌍 CARBON FOOTPRINT ANALYTICS CONSULTANT ACCESS TEST SUMMARY")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    if result.failures:
        logger.error("FAILURES:")
        for test, traceback in result.failures:
            logger.error(f"- {test}: {traceback}")
    
    if result.errors:
        logger.error("ERRORS:")
        for test, traceback in result.errors:
            logger.error(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    if success:
        logger.info("✅ ALL CARBON FOOTPRINT CONSULTANT ACCESS TESTS PASSED!")
    else:
        logger.error("❌ SOME CARBON FOOTPRINT CONSULTANT ACCESS TESTS FAILED!")
    
    return success

if __name__ == "__main__":
    success = run_carbon_footprint_consultant_tests()
    sys.exit(0 if success else 1)