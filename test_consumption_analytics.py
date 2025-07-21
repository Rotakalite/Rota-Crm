import unittest
import json
import logging
import requests
import os
import sys
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test data
TEST_YEAR = 2024
TEST_MONTH = 6  # June

# Backend URL
BACKEND_URL = "https://22f0c157-e8c8-48be-b2c9-2be7c8880541.preview.emergentagent.com/api"

# Test JWT token for admin user
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

class TestConsumptionAnalytics(unittest.TestCase):
    """Test class for consumption analytics per-person calculations"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_URL
        self.headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        
        # Generate a unique client ID for testing
        self.test_client_id = f"test_client_{uuid.uuid4().hex[:8]}"
        
        # Test consumption data with specific values for verification
        self.test_consumption_data = {
            "year": TEST_YEAR,
            "month": TEST_MONTH,
            "electricity": 1000.0,  # 1000 kWh
            "water": 100.0,         # 100 m³
            "natural_gas": 500.0,   # 500 m³
            "coal": 200.0,          # 200 kg
            "diesel": 0.0,
            "gasoline": 0.0,
            "lpg": 0.0,
            "fuel_oil": 0.0,
            "r134a_gas": 0.0,
            "r600a_gas": 0.0,
            "r410a_gas": 0.0,
            "r32_gas": 0.0,
            "co2_fire": 0.0,
            "fm200_fire": 0.0,
            "accommodation_count": 50,  # 50 guests
            "client_id": self.test_client_id
        }
        
        # Expected per-person values
        self.expected_per_person = {
            "electricity": 20.0,    # 1000 / 50 = 20.0 kWh/person
            "water": 2.0,           # 100 / 50 = 2.0 m³/person
            "natural_gas": 10.0,    # 500 / 50 = 10.0 m³/person
            "coal": 4.0             # 200 / 50 = 4.0 kg/person
        }
    
    def test_create_consumption_record(self):
        """Create a test consumption record"""
        logger.info("\n=== Creating test consumption record ===")
        
        url = f"{self.api_url}/consumptions"
        
        try:
            response = requests.post(url, headers=self.headers, json=self.test_consumption_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            # Check if we get a 200 OK or 400 (if record already exists)
            self.assertIn(response.status_code, [200, 400])
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn("message", data)
                self.assertIn("consumption_id", data)
                logger.info(f"✅ Created consumption record with ID: {data['consumption_id']}")
                self.consumption_id = data["consumption_id"]
            elif response.status_code == 400:
                # This could happen if record already exists for this month/year
                data = response.json()
                logger.info(f"⚠️ Expected 400 error: {data}")
                
                # Try to get the existing record
                self.get_existing_consumption_record()
            
        except Exception as e:
            logger.error(f"❌ Error creating consumption record: {str(e)}")
            raise
    
    def get_existing_consumption_record(self):
        """Get existing consumption record for the test client"""
        logger.info("\n=== Getting existing consumption records ===")
        
        url = f"{self.api_url}/consumptions"
        params = {
            "client_id": self.test_client_id,
            "year": TEST_YEAR
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            logger.info(f"Response status code: {response.status_code}")
            
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            logger.info(f"Found {len(data)} consumption records")
            
            # Find the record for our test month
            test_record = next((r for r in data if r["month"] == TEST_MONTH), None)
            
            if test_record:
                logger.info(f"✅ Found existing consumption record for month {TEST_MONTH}")
                self.consumption_id = test_record["id"]
            else:
                logger.warning(f"⚠️ No existing record found for month {TEST_MONTH}")
                
        except Exception as e:
            logger.error(f"❌ Error getting consumption records: {str(e)}")
            raise
    
    def test_consumption_analytics_per_person(self):
        """Test the per-person calculations in consumption analytics"""
        logger.info("\n=== Testing consumption analytics per-person calculations ===")
        
        url = f"{self.api_url}/consumptions/analytics"
        params = {
            "client_id": self.test_client_id,
            "year": TEST_YEAR
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            logger.info(f"Response status code: {response.status_code}")
            
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn("monthly_comparison", data)
            
            # Find the data for our test month
            test_month_data = next((m for m in data["monthly_comparison"] if m["month"] == TEST_MONTH), None)
            
            if not test_month_data:
                logger.warning(f"⚠️ No data found for month {TEST_MONTH}")
                self.skipTest(f"No data found for month {TEST_MONTH}")
            
            logger.info(f"Month data: {json.dumps(test_month_data, indent=2)}")
            
            # Verify per-person field exists
            self.assertIn("per_person", test_month_data)
            
            per_person = test_month_data["per_person"]
            logger.info(f"Per-person data: {json.dumps(per_person, indent=2)}")
            
            # Verify per-person values
            self.assertIn("electricity", per_person)
            self.assertIn("water", per_person)
            self.assertIn("natural_gas", per_person)
            self.assertIn("coal", per_person)
            
            # Check if values are non-zero
            self.assertGreater(per_person["electricity"], 0)
            self.assertGreater(per_person["water"], 0)
            self.assertGreater(per_person["natural_gas"], 0)
            self.assertGreater(per_person["coal"], 0)
            
            # Verify calculations are correct
            self.assertAlmostEqual(per_person["electricity"], self.expected_per_person["electricity"], places=1)
            self.assertAlmostEqual(per_person["water"], self.expected_per_person["water"], places=1)
            self.assertAlmostEqual(per_person["natural_gas"], self.expected_per_person["natural_gas"], places=1)
            self.assertAlmostEqual(per_person["coal"], self.expected_per_person["coal"], places=1)
            
            logger.info("✅ Per-person calculations are correct")
            
        except Exception as e:
            logger.error(f"❌ Error testing consumption analytics: {str(e)}")
            raise

def run_tests():
    """Run all tests"""
    logger.info("Starting consumption analytics tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add tests in order
    test_case = TestConsumptionAnalytics()
    suite.addTest(TestConsumptionAnalytics("test_create_consumption_record"))
    suite.addTest(TestConsumptionAnalytics("test_consumption_analytics_per_person"))
    
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