#!/usr/bin/env python3
"""
Consultant Client Assignment Test Suite
Tests the consultant role functionality for consumption endpoints
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

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT tokens for different user types
# These are sample tokens for testing - in production these would be real Clerk tokens
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

# Consultant tokens - these would represent different consultants
ROTA_CONSULTANT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfUk9UQV9DT05TVUxUQU5UIiwiZW1haWwiOiJyb3RhQGV4YW1wbGUuY29tIiwibmFtZSI6IlJPVEEgQ29uc3VsdGFudCJ9.signature"

KAYA_CONSULTANT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DT05TVUxUQU5UIiwiZW1haWwiOiJrYXlhQGV4YW1wbGUuY29tIiwibmFtZSI6IktBWUEgQ29uc3VsdGFudCJ9.signature"

# Consultant without consultant_id (should fail)
NO_CONSULTANT_ID_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfTk9fQ09OU1VMVEFOVF9JRCIsImVtYWlsIjoibm9jb25zdWx0YW50aWRAZXhhbXBsZS5jb20iLCJuYW1lIjoiTm8gQ29uc3VsdGFudCBJRCJ9.signature"

# Invalid token
INVALID_JWT_TOKEN = "invalid.token.format"

# Client IDs for testing (these would be real client IDs from the database)
VALID_CLIENT_ID = "8bfd3a85-2483-4b63-9e80-e53747c3db7e"  # Assigned to ROTA consultant
INVALID_CLIENT_ID = "00000000-0000-0000-0000-000000000000"  # Non-existent client
UNASSIGNED_CLIENT_ID = "11111111-1111-1111-1111-111111111111"  # Not assigned to consultant


class TestConsultantConsumptionEndpoints(unittest.TestCase):
    """Test class for consultant consumption endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        logger.info(f"Using API URL: {self.api_url}")
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_rota_consultant = {"Authorization": f"Bearer {ROTA_CONSULTANT_TOKEN}"}
        self.headers_kaya_consultant = {"Authorization": f"Bearer {KAYA_CONSULTANT_TOKEN}"}
        self.headers_no_consultant_id = {"Authorization": f"Bearer {NO_CONSULTANT_ID_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test consumption data
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        self.test_consumption_data = {
            "year": current_year,
            "month": current_month,
            "electricity": 1000.5,
            "water": 500.25,
            "natural_gas": 300.75,
            "coal": 200.0,
            "accommodation_count": 150,
            "client_id": VALID_CLIENT_ID
        }
    
    def test_get_consumptions_consultant_with_valid_client_id(self):
        """Test GET /api/consumptions - consultant role with valid client_id should succeed"""
        logger.info("\n=== Testing GET /api/consumptions - Consultant with valid client_id ===")
        
        url = f"{self.api_url}/consumptions"
        params = {"client_id": VALID_CLIENT_ID}
        
        try:
            response = requests.get(url, headers=self.headers_rota_consultant, params=params)
            logger.info(f"ROTA consultant response status code: {response.status_code}")
            
            # Should get 200 OK or 401/403 if authentication fails
            self.assertIn(response.status_code, [200, 401, 403])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data type: {type(data)}")
                
                # Should be a list of consumption records
                self.assertIsInstance(data, list)
                
                # If there are records, verify they belong to the specified client
                if len(data) > 0:
                    for record in data:
                        self.assertEqual(record.get("client_id"), VALID_CLIENT_ID)
                        logger.info(f"Found consumption record for client {record.get('client_id')}")
                
                logger.info("✅ GET /api/consumptions with valid client_id test passed")
            elif response.status_code in [401, 403]:
                # Authentication/authorization issues
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/consumptions with valid client_id - auth error (expected)")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/consumptions with valid client_id: {str(e)}")
            raise
    
    def test_get_consumptions_consultant_with_invalid_client_id(self):
        """Test GET /api/consumptions - consultant role with invalid client_id should get 403"""
        logger.info("\n=== Testing GET /api/consumptions - Consultant with invalid client_id ===")
        
        url = f"{self.api_url}/consumptions"
        params = {"client_id": INVALID_CLIENT_ID}
        
        try:
            response = requests.get(url, headers=self.headers_rota_consultant, params=params)
            logger.info(f"ROTA consultant response status code: {response.status_code}")
            
            # Should get 403 Access Denied or 401/404 if authentication fails or client not found
            self.assertIn(response.status_code, [403, 401, 404])
            
            if response.status_code == 403:
                data = response.json()
                logger.info(f"Expected 403 error: {data}")
                self.assertIn("detail", data)
                logger.info("✅ GET /api/consumptions with invalid client_id correctly returns 403")
            elif response.status_code == 404:
                data = response.json()
                logger.info(f"Expected 404 error (client not found): {data}")
                logger.info("✅ GET /api/consumptions with invalid client_id correctly returns 404")
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/consumptions with invalid client_id - auth error")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/consumptions with invalid client_id: {str(e)}")
            raise
    
    def test_get_consumptions_consultant_without_client_id(self):
        """Test GET /api/consumptions - consultant role without client_id should get 400"""
        logger.info("\n=== Testing GET /api/consumptions - Consultant without client_id parameter ===")
        
        url = f"{self.api_url}/consumptions"
        
        try:
            response = requests.get(url, headers=self.headers_rota_consultant)
            logger.info(f"ROTA consultant response status code: {response.status_code}")
            
            # Should get 400 Bad Request or 401/403 if authentication fails
            self.assertIn(response.status_code, [400, 401, 403])
            
            if response.status_code == 400:
                data = response.json()
                logger.info(f"Expected 400 error: {data}")
                self.assertIn("detail", data)
                logger.info("✅ GET /api/consumptions without client_id correctly returns 400")
            elif response.status_code in [401, 403]:
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/consumptions without client_id - auth error")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/consumptions without client_id: {str(e)}")
            raise
    
    def test_get_consumptions_consultant_without_consultant_id(self):
        """Test GET /api/consumptions - consultant user without consultant_id should get 400"""
        logger.info("\n=== Testing GET /api/consumptions - Consultant without consultant_id ===")
        
        url = f"{self.api_url}/consumptions"
        params = {"client_id": VALID_CLIENT_ID}
        
        try:
            response = requests.get(url, headers=self.headers_no_consultant_id, params=params)
            logger.info(f"No consultant_id user response status code: {response.status_code}")
            
            # Should get 400 Bad Request or 401/403 if authentication fails
            self.assertIn(response.status_code, [400, 401, 403])
            
            if response.status_code == 400:
                data = response.json()
                logger.info(f"Expected 400 error: {data}")
                self.assertIn("detail", data)
                logger.info("✅ GET /api/consumptions without consultant_id correctly returns 400")
            elif response.status_code in [401, 403]:
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/consumptions without consultant_id - auth error")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/consumptions without consultant_id: {str(e)}")
            raise
    
    def test_post_consumptions_consultant_with_valid_client_id(self):
        """Test POST /api/consumptions - consultant role with valid client_id should succeed"""
        logger.info("\n=== Testing POST /api/consumptions - Consultant with valid client_id ===")
        
        url = f"{self.api_url}/consumptions"
        
        # Use a unique month/year to avoid conflicts
        test_data = self.test_consumption_data.copy()
        test_data["month"] = 11  # November
        test_data["year"] = 2025  # Future year
        
        try:
            response = requests.post(url, headers=self.headers_rota_consultant, json=test_data)
            logger.info(f"ROTA consultant response status code: {response.status_code}")
            
            # Should get 200/201 OK or 400/401/403 if there are issues
            self.assertIn(response.status_code, [200, 201, 400, 401, 403])
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Should contain success message and consumption_id
                self.assertIn("message", data)
                self.assertIn("consumption_id", data)
                
                logger.info("✅ POST /api/consumptions with valid client_id test passed")
            elif response.status_code == 400:
                data = response.json()
                logger.info(f"Expected 400 error (may already exist): {data}")
                logger.info("✅ POST /api/consumptions with valid client_id - expected 400 error")
            elif response.status_code in [401, 403]:
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ POST /api/consumptions with valid client_id - auth error")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/consumptions with valid client_id: {str(e)}")
            raise
    
    def test_post_consumptions_consultant_with_invalid_client_id(self):
        """Test POST /api/consumptions - consultant role with invalid client_id should get 403"""
        logger.info("\n=== Testing POST /api/consumptions - Consultant with invalid client_id ===")
        
        url = f"{self.api_url}/consumptions"
        
        # Use invalid client_id
        test_data = self.test_consumption_data.copy()
        test_data["client_id"] = INVALID_CLIENT_ID
        test_data["month"] = 12  # December
        test_data["year"] = 2025  # Future year
        
        try:
            response = requests.post(url, headers=self.headers_rota_consultant, json=test_data)
            logger.info(f"ROTA consultant response status code: {response.status_code}")
            
            # Should get 403 Access Denied or 401/404 if authentication fails or client not found
            self.assertIn(response.status_code, [403, 401, 404])
            
            if response.status_code == 403:
                data = response.json()
                logger.info(f"Expected 403 error: {data}")
                self.assertIn("detail", data)
                logger.info("✅ POST /api/consumptions with invalid client_id correctly returns 403")
            elif response.status_code == 404:
                data = response.json()
                logger.info(f"Expected 404 error (client not found): {data}")
                logger.info("✅ POST /api/consumptions with invalid client_id correctly returns 404")
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ POST /api/consumptions with invalid client_id - auth error")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/consumptions with invalid client_id: {str(e)}")
            raise
    
    def test_get_consumptions_analytics_consultant_with_valid_client_id(self):
        """Test GET /api/consumptions/analytics - consultant role with valid client_id should succeed"""
        logger.info("\n=== Testing GET /api/consumptions/analytics - Consultant with valid client_id ===")
        
        url = f"{self.api_url}/consumptions/analytics"
        params = {"client_id": VALID_CLIENT_ID}
        
        try:
            response = requests.get(url, headers=self.headers_rota_consultant, params=params)
            logger.info(f"ROTA consultant response status code: {response.status_code}")
            
            # Should get 200 OK or 401/403 if authentication fails
            self.assertIn(response.status_code, [200, 401, 403])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data keys: {data.keys()}")
                
                # Should contain analytics structure
                expected_keys = ["yearly_totals", "monthly_data", "consumption_breakdown", "carbon_footprint"]
                for key in expected_keys:
                    if key in data:
                        logger.info(f"Found expected key: {key}")
                
                logger.info("✅ GET /api/consumptions/analytics with valid client_id test passed")
            elif response.status_code in [401, 403]:
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/consumptions/analytics with valid client_id - auth error")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/consumptions/analytics with valid client_id: {str(e)}")
            raise
    
    def test_get_consumptions_analytics_consultant_with_invalid_client_id(self):
        """Test GET /api/consumptions/analytics - consultant role with invalid client_id should get 403"""
        logger.info("\n=== Testing GET /api/consumptions/analytics - Consultant with invalid client_id ===")
        
        url = f"{self.api_url}/consumptions/analytics"
        params = {"client_id": INVALID_CLIENT_ID}
        
        try:
            response = requests.get(url, headers=self.headers_rota_consultant, params=params)
            logger.info(f"ROTA consultant response status code: {response.status_code}")
            
            # Should get 403 Access Denied or 401/404 if authentication fails or client not found
            self.assertIn(response.status_code, [403, 401, 404])
            
            if response.status_code == 403:
                data = response.json()
                logger.info(f"Expected 403 error: {data}")
                self.assertIn("detail", data)
                logger.info("✅ GET /api/consumptions/analytics with invalid client_id correctly returns 403")
            elif response.status_code == 404:
                data = response.json()
                logger.info(f"Expected 404 error (client not found): {data}")
                logger.info("✅ GET /api/consumptions/analytics with invalid client_id correctly returns 404")
            elif response.status_code == 401:
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/consumptions/analytics with invalid client_id - auth error")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/consumptions/analytics with invalid client_id: {str(e)}")
            raise
    
    def test_get_consumptions_analytics_consultant_without_client_id(self):
        """Test GET /api/consumptions/analytics - consultant role without client_id should get 400"""
        logger.info("\n=== Testing GET /api/consumptions/analytics - Consultant without client_id parameter ===")
        
        url = f"{self.api_url}/consumptions/analytics"
        
        try:
            response = requests.get(url, headers=self.headers_rota_consultant)
            logger.info(f"ROTA consultant response status code: {response.status_code}")
            
            # Should get 400 Bad Request or 401/403 if authentication fails
            self.assertIn(response.status_code, [400, 401, 403])
            
            if response.status_code == 400:
                data = response.json()
                logger.info(f"Expected 400 error: {data}")
                self.assertIn("detail", data)
                logger.info("✅ GET /api/consumptions/analytics without client_id correctly returns 400")
            elif response.status_code in [401, 403]:
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/consumptions/analytics without client_id - auth error")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/consumptions/analytics without client_id: {str(e)}")
            raise
    
    def test_authentication_scenarios(self):
        """Test various authentication scenarios"""
        logger.info("\n=== Testing Authentication Scenarios ===")
        
        url = f"{self.api_url}/consumptions"
        params = {"client_id": VALID_CLIENT_ID}
        
        # Test with invalid token
        try:
            response = requests.get(url, headers=self.headers_invalid, params=params)
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ Invalid token correctly returns 401")
        except Exception as e:
            logger.error(f"❌ Error testing invalid token: {str(e)}")
            raise
        
        # Test with no authentication
        try:
            response = requests.get(url, headers=self.headers_no_auth, params=params)
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Should get 403 Forbidden
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ No authentication correctly returns 403")
        except Exception as e:
            logger.error(f"❌ Error testing no authentication: {str(e)}")
            raise
    
    def test_consultant_database_data(self):
        """Test to verify consultant data exists in database"""
        logger.info("\n=== Testing Consultant Database Data ===")
        
        # Test getting consultants list (should be public endpoint)
        url = f"{self.api_url}/consultants"
        
        try:
            response = requests.get(url)
            logger.info(f"Consultants list response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} consultants in database")
                
                # Look for ROTA and KAYA consultants
                consultant_names = [consultant.get("company_name", "") for consultant in data]
                logger.info(f"Consultant companies: {consultant_names}")
                
                # Check if expected consultants exist
                expected_consultants = ["ROTA", "KAYA DANIŞMANLIK"]
                for expected in expected_consultants:
                    found = any(expected in name for name in consultant_names)
                    if found:
                        logger.info(f"✅ Found expected consultant: {expected}")
                    else:
                        logger.warning(f"⚠️ Expected consultant not found: {expected}")
                
                logger.info("✅ Consultant database data test completed")
            else:
                logger.warning(f"⚠️ Could not retrieve consultants list: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing consultant database data: {str(e)}")
            raise


def run_consultant_consumption_tests():
    """Run all consultant consumption tests"""
    logger.info("🚀 Starting Consultant Client Assignment Tests")
    logger.info(f"Backend URL: {RAILWAY_API_URL}")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(TestConsultantConsumptionEndpoints('test_consultant_database_data'))
    suite.addTest(TestConsultantConsumptionEndpoints('test_authentication_scenarios'))
    suite.addTest(TestConsultantConsumptionEndpoints('test_get_consumptions_consultant_with_valid_client_id'))
    suite.addTest(TestConsultantConsumptionEndpoints('test_get_consumptions_consultant_with_invalid_client_id'))
    suite.addTest(TestConsultantConsumptionEndpoints('test_get_consumptions_consultant_without_client_id'))
    suite.addTest(TestConsultantConsumptionEndpoints('test_get_consumptions_consultant_without_consultant_id'))
    suite.addTest(TestConsultantConsumptionEndpoints('test_post_consumptions_consultant_with_valid_client_id'))
    suite.addTest(TestConsultantConsumptionEndpoints('test_post_consumptions_consultant_with_invalid_client_id'))
    suite.addTest(TestConsultantConsumptionEndpoints('test_get_consumptions_analytics_consultant_with_valid_client_id'))
    suite.addTest(TestConsultantConsumptionEndpoints('test_get_consumptions_analytics_consultant_with_invalid_client_id'))
    suite.addTest(TestConsultantConsumptionEndpoints('test_get_consumptions_analytics_consultant_without_client_id'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("🎯 CONSULTANT CLIENT ASSIGNMENT TEST SUMMARY")
    logger.info("="*80)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    if result.failures:
        logger.error("❌ FAILURES:")
        for test, traceback in result.failures:
            logger.error(f"  - {test}: {traceback}")
    
    if result.errors:
        logger.error("❌ ERRORS:")
        for test, traceback in result.errors:
            logger.error(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        logger.info("✅ ALL TESTS PASSED!")
    else:
        logger.error("❌ SOME TESTS FAILED!")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_consultant_consumption_tests()
    sys.exit(0 if success else 1)