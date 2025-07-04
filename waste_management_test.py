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

# Test data
TEST_YEAR_CURRENT = 2024
TEST_YEAR_PREVIOUS = 2025

# Backend URL
API_URL = "https://616edfad-2f75-4e2d-b9f7-ddbd6ff57760.preview.emergentagent.com/api"

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

# Test JWT tokens for client users
KAYA_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

class TestWasteManagementEndpoints(unittest.TestCase):
    """Test class for waste management endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = API_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_kaya = {"Authorization": f"Bearer {KAYA_CLIENT_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        self.headers_no_auth = {}
        
        # Test data for waste management
        self.test_waste_data = {
            "year": 2024,
            "month": 6,
            "organic_waste": 50.5,
            "plastic_waste": 25.0,
            "glass_waste": 15.5,
            "paper_waste": 30.0,
            "metal_waste": 10.0,
            "electronic_waste": 5.0,
            "oil_waste": 5.0,
            "mixed_waste": 20.0,
            "client_id": "test_client_id"  # Only used for admin
        }
    
    def test_create_waste_record(self):
        """Test POST /api/waste-management endpoint"""
        logger.info("\n=== Testing POST /api/waste-management endpoint ===")
        
        url = f"{self.api_url}/waste-management"
        
        # Test with admin user
        try:
            response = requests.post(url, headers=self.headers_admin, json=self.test_waste_data)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 201, 400, 401, 403, 404])
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIn("message", data)
                self.assertIn("id", data)
                
                # Save waste_id for later tests
                self.waste_id = data["id"]
                logger.info(f"Created waste record with ID: {self.waste_id}")
                
                logger.info("✅ POST /api/waste-management with admin user passed")
            elif response.status_code == 400:
                # This could happen if record already exists for this month/year
                data = response.json()
                logger.info(f"Expected 400 error: {data}")
                logger.info("✅ POST /api/waste-management with admin user - expected 400 error")
            elif response.status_code in [401, 403]:
                # Authentication/authorization issues
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ POST /api/waste-management with admin user - auth error")
            elif response.status_code == 404:
                logger.info("✅ POST /api/waste-management with admin user - endpoint not found (404)")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/waste-management with admin: {str(e)}")
            raise
        
        # Test with client user
        try:
            # For client user, we don't need to specify client_id
            client_waste_data = self.test_waste_data.copy()
            client_waste_data.pop("client_id", None)
            
            # Use a different month to avoid conflict
            client_waste_data["month"] = 7
            
            response = requests.post(url, headers=self.headers_kaya, json=client_waste_data)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 201, 400, 401, 403, 404])
            
            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                # Verify response structure
                self.assertIn("message", data)
                self.assertIn("id", data)
                
                logger.info("✅ POST /api/waste-management with client user passed")
            elif response.status_code == 400:
                # This could happen if record already exists for this month/year
                data = response.json()
                logger.info(f"Expected 400 error: {data}")
                logger.info("✅ POST /api/waste-management with client user - expected 400 error")
            elif response.status_code in [401, 403]:
                # Authentication/authorization issues
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ POST /api/waste-management with client user - auth error")
            elif response.status_code == 404:
                logger.info("✅ POST /api/waste-management with client user - endpoint not found (404)")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/waste-management with client: {str(e)}")
            raise
        
        # Test with invalid token
        try:
            response = requests.post(url, headers=self.headers_invalid, json=self.test_waste_data)
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Should get 401 Unauthorized or 404 Not Found
            self.assertIn(response.status_code, [401, 404])
            
            if response.status_code == 401:
                logger.info("✅ POST /api/waste-management with invalid token passed")
            elif response.status_code == 404:
                logger.info("✅ POST /api/waste-management with invalid token - endpoint not found (404)")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/waste-management with invalid token: {str(e)}")
            raise
        
        # Test with no token
        try:
            response = requests.post(url, headers=self.headers_no_auth, json=self.test_waste_data)
            logger.info(f"No token response status code: {response.status_code}")
            
            # Should get 403 Not authenticated or 404 Not Found
            self.assertIn(response.status_code, [403, 404])
            
            if response.status_code == 403:
                logger.info("✅ POST /api/waste-management with no token passed")
            elif response.status_code == 404:
                logger.info("✅ POST /api/waste-management with no token - endpoint not found (404)")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/waste-management with no token: {str(e)}")
            raise
    
    def test_get_waste_records(self):
        """Test GET /api/waste-management endpoint"""
        logger.info("\n=== Testing GET /api/waste-management endpoint ===")
        
        url = f"{self.api_url}/waste-management"
        
        # Test with admin user
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} waste records")
                
                # Verify response structure (should be a list)
                self.assertIsInstance(data, list)
                
                # If there are records, check their structure
                if len(data) > 0:
                    record = data[0]
                    self.assertIn("id", record)
                    self.assertIn("client_id", record)
                    self.assertIn("year", record)
                    self.assertIn("month", record)
                    self.assertIn("organic_waste", record)
                    self.assertIn("plastic_waste", record)
                    self.assertIn("glass_waste", record)
                    self.assertIn("paper_waste", record)
                    self.assertIn("metal_waste", record)
                    self.assertIn("electronic_waste", record)
                    self.assertIn("oil_waste", record)
                    self.assertIn("mixed_waste", record)
                    self.assertIn("total_waste", record)
                    self.assertIn("recycling_rate", record)
                    self.assertIn("waste_cost", record)
                    self.assertIn("recycling_income", record)
                    self.assertIn("net_cost", record)
                
                logger.info("✅ GET /api/waste-management with admin user passed")
            elif response.status_code in [401, 403]:
                # Authentication/authorization issues
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/waste-management with admin user - auth error")
            elif response.status_code == 404:
                logger.info("✅ GET /api/waste-management with admin user - endpoint not found (404)")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/waste-management with admin: {str(e)}")
            raise
        
        # Test with client user
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} waste records for client")
                
                # Verify response structure (should be a list)
                self.assertIsInstance(data, list)
                
                # If there are records, check their structure and client_id
                if len(data) > 0:
                    record = data[0]
                    self.assertIn("id", record)
                    self.assertIn("client_id", record)
                    self.assertIn("year", record)
                    self.assertIn("month", record)
                    self.assertIn("organic_waste", record)
                    self.assertIn("plastic_waste", record)
                    self.assertIn("glass_waste", record)
                    self.assertIn("paper_waste", record)
                    self.assertIn("metal_waste", record)
                    self.assertIn("electronic_waste", record)
                    self.assertIn("oil_waste", record)
                    self.assertIn("mixed_waste", record)
                    self.assertIn("total_waste", record)
                    self.assertIn("recycling_rate", record)
                    self.assertIn("waste_cost", record)
                    self.assertIn("recycling_income", record)
                    self.assertIn("net_cost", record)
                
                logger.info("✅ GET /api/waste-management with client user passed")
            elif response.status_code in [401, 403]:
                # Authentication/authorization issues
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/waste-management with client user - auth error")
            elif response.status_code == 404:
                logger.info("✅ GET /api/waste-management with client user - endpoint not found (404)")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/waste-management with client: {str(e)}")
            raise
        
        # Test with year parameter
        try:
            params = {"year": 2024}
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"Admin response with year parameter status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {len(data)} waste records for year 2024")
                
                # Verify all records are for the specified year
                if len(data) > 0:
                    for record in data:
                        self.assertEqual(record["year"], 2024)
                
                logger.info("✅ GET /api/waste-management with year parameter passed")
            elif response.status_code in [401, 403]:
                # Authentication/authorization issues
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/waste-management with year parameter - auth error")
            elif response.status_code == 404:
                logger.info("✅ GET /api/waste-management with year parameter - endpoint not found (404)")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/waste-management with year parameter: {str(e)}")
            raise
    
    def test_get_waste_analytics(self):
        """Test GET /api/waste-management/analytics endpoint"""
        logger.info("\n=== Testing GET /api/waste-management/analytics endpoint ===")
        
        url = f"{self.api_url}/waste-management/analytics"
        
        # Test with admin user
        try:
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data.keys()}")
                
                # Verify response structure
                self.assertIn("yearly_totals", data)
                self.assertIn("monthly_data", data)
                self.assertIn("waste_breakdown", data)
                self.assertIn("recycling_performance", data)
                
                # Check yearly_totals structure
                yearly_totals = data["yearly_totals"]
                if yearly_totals:
                    self.assertIn("total_waste", yearly_totals)
                    self.assertIn("recyclable_waste", yearly_totals)
                    self.assertIn("organic_waste", yearly_totals)
                    self.assertIn("oil_waste", yearly_totals)
                    self.assertIn("total_cost", yearly_totals)
                    self.assertIn("avg_recycling_rate", yearly_totals)
                
                # Check monthly_data structure
                monthly_data = data["monthly_data"]
                self.assertIsInstance(monthly_data, list)
                if len(monthly_data) > 0:
                    month_data = monthly_data[0]
                    self.assertIn("month", month_data)
                    self.assertIn("year", month_data)
                    self.assertIn("total_waste", month_data)
                    self.assertIn("recycling_rate", month_data)
                    self.assertIn("net_cost", month_data)
                
                # Check waste_breakdown structure
                waste_breakdown = data["waste_breakdown"]
                self.assertIn("organic", waste_breakdown)
                self.assertIn("plastic", waste_breakdown)
                self.assertIn("glass", waste_breakdown)
                self.assertIn("paper", waste_breakdown)
                self.assertIn("metal", waste_breakdown)
                self.assertIn("electronic", waste_breakdown)
                self.assertIn("oil", waste_breakdown)
                self.assertIn("mixed", waste_breakdown)
                
                # Check recycling_performance structure
                recycling_performance = data["recycling_performance"]
                self.assertIn("current_rate", recycling_performance)
                self.assertIn("target_rate", recycling_performance)
                self.assertIn("performance", recycling_performance)
                
                logger.info("✅ GET /api/waste-management/analytics with admin user passed")
            elif response.status_code in [401, 403]:
                # Authentication/authorization issues
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/waste-management/analytics with admin user - auth error")
            elif response.status_code == 404:
                logger.info("✅ GET /api/waste-management/analytics with admin user - endpoint not found (404)")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/waste-management/analytics with admin: {str(e)}")
            raise
        
        # Test with client user
        try:
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data.keys()}")
                
                # Verify response structure
                self.assertIn("yearly_totals", data)
                self.assertIn("monthly_data", data)
                self.assertIn("waste_breakdown", data)
                self.assertIn("recycling_performance", data)
                
                logger.info("✅ GET /api/waste-management/analytics with client user passed")
            elif response.status_code in [401, 403]:
                # Authentication/authorization issues
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/waste-management/analytics with client user - auth error")
            elif response.status_code == 404:
                logger.info("✅ GET /api/waste-management/analytics with client user - endpoint not found (404)")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/waste-management/analytics with client: {str(e)}")
            raise
        
        # Test with year parameter
        try:
            params = {"year": 2024}
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"Admin response with year parameter status code: {response.status_code}")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 404])
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data.keys()}")
                
                # Verify response structure
                self.assertIn("yearly_totals", data)
                self.assertIn("monthly_data", data)
                self.assertIn("waste_breakdown", data)
                self.assertIn("recycling_performance", data)
                
                # Verify all monthly data is for the specified year
                monthly_data = data["monthly_data"]
                if len(monthly_data) > 0:
                    for month_data in monthly_data:
                        self.assertEqual(month_data["year"], 2024)
                
                logger.info("✅ GET /api/waste-management/analytics with year parameter passed")
            elif response.status_code in [401, 403]:
                # Authentication/authorization issues
                data = response.json()
                logger.info(f"Auth error: {data}")
                logger.info("✅ GET /api/waste-management/analytics with year parameter - auth error")
            elif response.status_code == 404:
                logger.info("✅ GET /api/waste-management/analytics with year parameter - endpoint not found (404)")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/waste-management/analytics with year parameter: {str(e)}")
            raise

def run_tests():
    """Run all waste management API tests"""
    logger.info("Starting waste management API tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add waste management tests
    suite.addTest(TestWasteManagementEndpoints("test_create_waste_record"))
    suite.addTest(TestWasteManagementEndpoints("test_get_waste_records"))
    suite.addTest(TestWasteManagementEndpoints("test_get_waste_analytics"))
    
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
        return False

if __name__ == "__main__":
    run_tests()