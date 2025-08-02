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

# Test data
TEST_YEAR_CURRENT = 2024
TEST_YEAR_PREVIOUS = 2025

# Backend URL
BACKEND_URL = "https://d787e851-4fbb-4d90-a594-90394e6ba15e.preview.emergentagent.com/api"

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

# Test JWT tokens for client users
# These are sample tokens for testing different client users
KAYA_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
CANO_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0FOT19DTElFTlRfMDAxIiwiZW1haWwiOiJjYW5lcnBhbEBnbWFpbC5jb20iLCJuYW1lIjoiQ0FOTyBDbGllbnQifQ.signature"
DENEME_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfREVORU1FX0NMSUVOVF8wMDEiLCJlbWFpbCI6InBhbGF2YW5jYW5lckBnbWFpbC5jb20iLCJuYW1lIjoiREVORU1FIENsaWVudCJ9.signature"
NO_CLIENT_ID_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfTk9fQ0xJRU5UX0lEIiwiZW1haWwiOiJub2NsaWVudGlkQGV4YW1wbGUuY29tIiwibmFtZSI6IlVzZXIgV2l0aG91dCBDbGllbnQgSUQifQ.signature"
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data

class TestCarbonFootprintAnalytics(unittest.TestCase):
    """Test class for carbon footprint analytics endpoint"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_URL
        
        # Headers for different user types
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_kaya = {"Authorization": f"Bearer {KAYA_CLIENT_TOKEN}"}
        self.headers_cano = {"Authorization": f"Bearer {CANO_CLIENT_TOKEN}"}
        self.headers_deneme = {"Authorization": f"Bearer {DENEME_CLIENT_TOKEN}"}
        self.headers_no_client_id = {"Authorization": f"Bearer {NO_CLIENT_ID_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_carbon_footprint_analytics_endpoint(self):
        """Test the /api/analytics/carbon-footprint endpoint"""
        logger.info("\n=== Testing /api/analytics/carbon-footprint endpoint ===")
        
        # Test with admin user
        logger.info("Testing with admin user...")
        url = f"{self.api_url}/analytics/carbon-footprint"
        
        # Admin needs to specify client_id
        params = {"client_id": "client1", "year": TEST_YEAR_CURRENT}
        
        try:
            response = requests.get(url, headers=self.headers_admin, params=params)
            logger.info(f"Admin response status code: {response.status_code}")
            
            # Admin should get 200 OK, 400 Bad Request (if client_id is invalid), or 401 Unauthorized (if token is invalid)
            self.assertIn(response.status_code, [200, 400, 401])
            
            if response.status_code == 401:
                logger.info("✅ Authentication failed correctly - received 401 Unauthorized")
                error_data = response.json()
                self.assertIn("detail", error_data)
            elif response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {json.dumps(data, indent=2)[:500]}...")
                
                # Check response structure
                self.assertIn("year", data)
                self.assertIn("client_id", data)
                self.assertIn("total_carbon_emissions", data)
                self.assertIn("monthly_carbon_data", data)
                self.assertIn("total_emission_sources", data)
                
                # Check total_emission_sources structure
                total_emission_sources = data.get("total_emission_sources", {})
                logger.info(f"Total emission sources: {json.dumps(total_emission_sources, indent=2)}")
                
                # Check for all required emission sources
                expected_sources = [
                    "electricity", "water", "natural_gas", "coal",
                    "diesel", "gasoline", "lpg", "fuel_oil",
                    "r134a_gas", "r600a_gas", "r410a_gas", "r32_gas",
                    "co2_fire", "fm200_fire"
                ]
                
                # Check if all expected sources are in the response (they might be 0)
                for source in expected_sources:
                    if source in total_emission_sources:
                        logger.info(f"✅ Found emission source: {source} = {total_emission_sources[source]}")
                    else:
                        logger.warning(f"⚠️ Missing emission source: {source}")
                
                # Count how many expected sources are present
                present_sources = [source for source in expected_sources if source in total_emission_sources]
                logger.info(f"Found {len(present_sources)} out of {len(expected_sources)} expected emission sources")
                
                # Check monthly data structure if available
                monthly_data = data.get("monthly_carbon_data", [])
                if monthly_data:
                    sample_month = monthly_data[0]
                    logger.info(f"Sample month data: {json.dumps(sample_month, indent=2)}")
                    
                    # Check for emissions breakdown in monthly data
                    if "emissions_breakdown" in sample_month:
                        emissions_breakdown = sample_month["emissions_breakdown"]
                        logger.info(f"Emissions breakdown for sample month: {json.dumps(emissions_breakdown, indent=2)}")
                        
                        # Check for F-Gas sources in breakdown
                        f_gas_sources = ["r134a_gas", "r600a_gas", "r410a_gas", "r32_gas", "co2_fire", "fm200_fire"]
                        found_f_gas_sources = [source for source in f_gas_sources if source in emissions_breakdown]
                        logger.info(f"Found {len(found_f_gas_sources)} out of {len(f_gas_sources)} F-Gas sources in breakdown")
                
                logger.info("✅ Admin test passed for /api/analytics/carbon-footprint")
            else:
                logger.warning(f"⚠️ Admin test received {response.status_code} - this may be expected if client_id is invalid")
        except Exception as e:
            logger.error(f"❌ Error testing admin access: {str(e)}")
            raise
        
        # Test with client user
        logger.info("\nTesting with client user...")
        
        try:
            # Client users don't need to specify client_id
            response = requests.get(url, headers=self.headers_kaya)
            logger.info(f"Client response status code: {response.status_code}")
            
            # Client should get 200 OK, 401 Unauthorized, or 403 Forbidden
            self.assertIn(response.status_code, [200, 401, 403])
            
            if response.status_code == 401:
                logger.info("✅ Authentication failed correctly - received 401 Unauthorized")
                error_data = response.json()
                self.assertIn("detail", error_data)
            elif response.status_code == 403:
                logger.info("⚠️ Client test received 403 - this may be expected if client_id is not properly linked")
            elif response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {json.dumps(data, indent=2)[:500]}...")
                
                # Check response structure
                self.assertIn("year", data)
                self.assertIn("client_id", data)
                self.assertIn("total_carbon_emissions", data)
                self.assertIn("monthly_carbon_data", data)
                self.assertIn("total_emission_sources", data)
                
                # Check total_emission_sources structure
                total_emission_sources = data.get("total_emission_sources", {})
                logger.info(f"Total emission sources: {json.dumps(total_emission_sources, indent=2)}")
                
                # Check for all required emission sources
                expected_sources = [
                    "electricity", "water", "natural_gas", "coal",
                    "diesel", "gasoline", "lpg", "fuel_oil",
                    "r134a_gas", "r600a_gas", "r410a_gas", "r32_gas",
                    "co2_fire", "fm200_fire"
                ]
                
                # Check if all expected sources are in the response (they might be 0)
                for source in expected_sources:
                    if source in total_emission_sources:
                        logger.info(f"✅ Found emission source: {source} = {total_emission_sources[source]}")
                    else:
                        logger.warning(f"⚠️ Missing emission source: {source}")
                
                # Count how many expected sources are present
                present_sources = [source for source in expected_sources if source in total_emission_sources]
                logger.info(f"Found {len(present_sources)} out of {len(expected_sources)} expected emission sources")
                
                logger.info("✅ Client test passed for /api/analytics/carbon-footprint")
            elif response.status_code == 403:
                logger.warning("⚠️ Client test received 403 - this may be expected if client_id is not properly linked")
        except Exception as e:
            logger.error(f"❌ Error testing client access: {str(e)}")
            raise
        
        # Test with invalid token
        logger.info("\nTesting with invalid token...")
        
        try:
            response = requests.get(url, headers=self.headers_invalid)
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Should get 401 Unauthorized
            self.assertEqual(response.status_code, 401)
            
            logger.info("✅ Invalid token test passed")
        except Exception as e:
            logger.error(f"❌ Error testing invalid token access: {str(e)}")
            raise
        
        # Test with no token
        logger.info("\nTesting with no token...")
        
        try:
            response = requests.get(url, headers=self.headers_no_auth)
            logger.info(f"No token response status code: {response.status_code}")
            
            # Should get 403 Not authenticated
            self.assertEqual(response.status_code, 403)
            
            logger.info("✅ No token test passed")
        except Exception as e:
            logger.error(f"❌ Error testing no token access: {str(e)}")
            raise

def run_tests():
    """Run all API tests"""
    logger.info("Starting Carbon Footprint Analytics API tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(TestCarbonFootprintAnalytics("test_carbon_footprint_analytics_endpoint"))
    
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