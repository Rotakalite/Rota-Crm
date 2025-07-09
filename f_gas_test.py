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

# Test data
TEST_YEAR = 2024
TEST_MONTH = 6  # June

# Backend URL
BACKEND_URL = "https://539ffbd1-9de6-4314-8bdd-a94fe4106807.preview.emergentagent.com/api"

# Test JWT token - this is a sample token for testing
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

# Test client IDs
KAYA_CLIENT_ID = "KAYA_CLIENT_001"
CANO_CLIENT_ID = "CANO_CLIENT_001"

class TestFGasCarbon(unittest.TestCase):
    """Test class for F-Gas carbon calculation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = BACKEND_URL
        self.headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        
        # Generate unique test data to avoid conflicts
        self.test_month = (datetime.now().month % 12) + 1
        self.test_year = datetime.now().year
        
        # F-Gas test data with values from the review request
        self.f_gas_consumption_data = {
            "client_id": KAYA_CLIENT_ID,
            "year": self.test_year,
            "month": self.test_month,
            "electricity": 1000.0,
            "water": 500.0,
            "natural_gas": 300.0,
            "coal": 200.0,
            "diesel": 100.0,
            "gasoline": 50.0,
            "lpg": 25.0,
            "fuel_oil": 75.0,
            # F-Gas values from the review request
            "r134a_gas": 1.5,      # kg (Klima gazı - 1430 kg CO2e/kg)
            "r600a_gas": 0.5,      # kg (Buzdolabı gazı - 3 kg CO2e/kg)
            "r410a_gas": 2.0,      # kg (Modern AC - 2088 kg CO2e/kg)
            "r32_gas": 1.0,        # kg (Yeni nesil AC - 675 kg CO2e/kg)
            "co2_fire": 10.0,      # kg (CO2 söndürücü - 1 kg CO2/kg)
            "fm200_fire": 5.0,     # kg (FM200 söndürücü - 3220 kg CO2e/kg)
            "accommodation_count": 100
        }
        
        # Expected CO2 emissions from F-Gases based on emission factors
        self.expected_f_gas_emissions = {
            "r134a_gas": 1.5 * 1430.0,    # 2,145 kg CO2e
            "r600a_gas": 0.5 * 3.0,       # 1.5 kg CO2e
            "r410a_gas": 2.0 * 2088.0,    # 4,176 kg CO2e
            "r32_gas": 1.0 * 675.0,       # 675 kg CO2e
            "co2_fire": 10.0 * 1.0,       # 10 kg CO2e
            "fm200_fire": 5.0 * 3220.0    # 16,100 kg CO2e
        }
        
        # Total expected CO2 from F-Gases: ~23,107.5 kg CO2e
        self.expected_total_f_gas_co2 = sum(self.expected_f_gas_emissions.values())
        
        # Expected total CO2 including regular consumption (rough estimate)
        # Regular consumption: ~1000 kg CO2e
        # F-Gases: ~23,107.5 kg CO2e
        # Total: ~24,107.5 kg CO2e
        self.expected_total_co2 = 24000  # Approximate value for validation
    
    def test_post_consumption_with_f_gas(self):
        """Test creating consumption data with F-Gas values"""
        logger.info("\n=== Testing POST /api/consumptions with F-Gas values ===")
        
        url = f"{self.api_url}/consumptions"
        
        # First, delete any existing consumption for this month/year to avoid conflicts
        self.cleanup_test_consumption()
        
        try:
            # Create consumption with F-Gas values
            response = requests.post(url, headers=self.headers, json=self.f_gas_consumption_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            self.assertEqual(response.status_code, 200, "POST request should succeed")
            
            data = response.json()
            self.assertIn("message", data, "Response should contain a message")
            self.assertIn("consumption_id", data, "Response should contain the consumption_id")
            
            # Store consumption ID for later tests
            self.consumption_id = data["consumption_id"]
            logger.info(f"Created consumption with ID: {self.consumption_id}")
            
            # Verify the consumption was created with F-Gas values
            self.verify_consumption_data()
            
            logger.info("✅ POST /api/consumptions with F-Gas values test passed")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/consumptions: {str(e)}")
            raise
    
    def verify_consumption_data(self):
        """Verify the consumption data was saved correctly with F-Gas values"""
        logger.info("Verifying consumption data...")
        
        url = f"{self.api_url}/consumptions"
        params = {
            "client_id": KAYA_CLIENT_ID,
            "year": self.test_year
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        self.assertEqual(response.status_code, 200, "GET request should succeed")
        
        consumptions = response.json()
        self.assertIsInstance(consumptions, list, "Response should be a list")
        
        # Find our test consumption
        test_consumption = None
        for consumption in consumptions:
            if consumption.get("month") == self.test_month and consumption.get("year") == self.test_year:
                test_consumption = consumption
                break
        
        self.assertIsNotNone(test_consumption, "Test consumption should exist")
        
        # Verify F-Gas values
        self.assertEqual(test_consumption.get("r134a_gas"), self.f_gas_consumption_data["r134a_gas"], "r134a_gas value should match")
        self.assertEqual(test_consumption.get("r600a_gas"), self.f_gas_consumption_data["r600a_gas"], "r600a_gas value should match")
        self.assertEqual(test_consumption.get("r410a_gas"), self.f_gas_consumption_data["r410a_gas"], "r410a_gas value should match")
        self.assertEqual(test_consumption.get("r32_gas"), self.f_gas_consumption_data["r32_gas"], "r32_gas value should match")
        self.assertEqual(test_consumption.get("co2_fire"), self.f_gas_consumption_data["co2_fire"], "co2_fire value should match")
        self.assertEqual(test_consumption.get("fm200_fire"), self.f_gas_consumption_data["fm200_fire"], "fm200_fire value should match")
        
        # Verify carbon calculation fields
        self.assertIn("total_co2_emissions", test_consumption, "total_co2_emissions field should exist")
        self.assertIn("total_co2_tonnes", test_consumption, "total_co2_tonnes field should exist")
        self.assertIn("per_person_co2", test_consumption, "per_person_co2 field should exist")
        
        # Verify total CO2 is high due to F-Gas emissions
        total_co2 = test_consumption.get("total_co2_emissions", 0)
        logger.info(f"Total CO2 emissions: {total_co2} kg CO2e")
        
        # The total should be at least 20,000 kg CO2e due to F-Gas emissions
        self.assertGreater(total_co2, 20000, "Total CO2 should be high due to F-Gas emissions")
        
        # Verify CO2 tonnes is correctly calculated
        co2_tonnes = test_consumption.get("total_co2_tonnes", 0)
        expected_tonnes = total_co2 / 1000.0
        self.assertAlmostEqual(co2_tonnes, expected_tonnes, places=3, msg="CO2 tonnes should be total CO2 / 1000")
        
        logger.info("✅ Consumption data verification passed")
    
    def test_put_consumption_with_f_gas(self):
        """Test updating consumption data with F-Gas values"""
        logger.info("\n=== Testing PUT /api/consumptions/{id} with F-Gas values ===")
        
        # First, ensure we have a consumption to update
        if not hasattr(self, 'consumption_id'):
            self.test_post_consumption_with_f_gas()
        
        url = f"{self.api_url}/consumptions/{self.consumption_id}"
        
        # Update data with different F-Gas values
        update_data = self.f_gas_consumption_data.copy()
        update_data["r134a_gas"] = 2.0  # Increase from 1.5 to 2.0
        update_data["r600a_gas"] = 1.0  # Increase from 0.5 to 1.0
        update_data["r410a_gas"] = 3.0  # Increase from 2.0 to 3.0
        
        try:
            # Update consumption
            response = requests.put(url, headers=self.headers, json=update_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            self.assertEqual(response.status_code, 200, "PUT request should succeed")
            
            data = response.json()
            self.assertIn("message", data, "Response should contain a message")
            
            # Verify the consumption was updated with new F-Gas values
            self.verify_updated_consumption(update_data)
            
            logger.info("✅ PUT /api/consumptions/{id} with F-Gas values test passed")
        except Exception as e:
            logger.error(f"❌ Error testing PUT /api/consumptions/{self.consumption_id}: {str(e)}")
            raise
    
    def verify_updated_consumption(self, update_data):
        """Verify the consumption data was updated correctly with new F-Gas values"""
        logger.info("Verifying updated consumption data...")
        
        url = f"{self.api_url}/consumptions"
        params = {
            "client_id": KAYA_CLIENT_ID,
            "year": self.test_year
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        self.assertEqual(response.status_code, 200, "GET request should succeed")
        
        consumptions = response.json()
        
        # Find our test consumption
        test_consumption = None
        for consumption in consumptions:
            if consumption.get("id") == self.consumption_id:
                test_consumption = consumption
                break
        
        self.assertIsNotNone(test_consumption, "Test consumption should exist")
        
        # Verify updated F-Gas values
        self.assertEqual(test_consumption.get("r134a_gas"), update_data["r134a_gas"], "r134a_gas value should be updated")
        self.assertEqual(test_consumption.get("r600a_gas"), update_data["r600a_gas"], "r600a_gas value should be updated")
        self.assertEqual(test_consumption.get("r410a_gas"), update_data["r410a_gas"], "r410a_gas value should be updated")
        
        # Verify carbon calculation was updated
        total_co2 = test_consumption.get("total_co2_emissions", 0)
        logger.info(f"Updated total CO2 emissions: {total_co2} kg CO2e")
        
        # The total should be higher than before due to increased F-Gas values
        self.assertGreater(total_co2, 25000, "Total CO2 should be higher after increasing F-Gas values")
        
        logger.info("✅ Updated consumption data verification passed")
    
    def test_carbon_footprint_analytics(self):
        """Test the carbon footprint analytics endpoint with F-Gas data"""
        logger.info("\n=== Testing GET /api/analytics/carbon-footprint with F-Gas data ===")
        
        # First, ensure we have consumption data with F-Gas values
        if not hasattr(self, 'consumption_id'):
            self.test_post_consumption_with_f_gas()
        
        url = f"{self.api_url}/analytics/carbon-footprint"
        params = {
            "client_id": KAYA_CLIENT_ID,
            "year": self.test_year
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            logger.info(f"Response status code: {response.status_code}")
            
            self.assertEqual(response.status_code, 200, "GET request should succeed")
            
            data = response.json()
            logger.info(f"Carbon footprint data: {json.dumps(data, indent=2)[:500]}...")
            
            # Verify the response structure
            self.assertIn("year", data, "Response should contain year")
            self.assertIn("client_id", data, "Response should contain client_id")
            self.assertIn("total_carbon_emissions", data, "Response should contain total_carbon_emissions")
            self.assertIn("total_carbon_tonnes", data, "Response should contain total_carbon_tonnes")
            self.assertIn("monthly_carbon_data", data, "Response should contain monthly_carbon_data")
            
            # Verify monthly carbon data includes our test month
            monthly_data = data["monthly_carbon_data"]
            self.assertIsInstance(monthly_data, list, "monthly_carbon_data should be a list")
            
            test_month_data = None
            for month_data in monthly_data:
                if month_data.get("month") == self.test_month:
                    test_month_data = month_data
                    break
            
            self.assertIsNotNone(test_month_data, f"Carbon data for test month {self.test_month} should exist")
            
            # Verify emissions breakdown includes F-Gas emissions
            self.assertIn("emissions_breakdown", test_month_data, "Month data should contain emissions_breakdown")
            emissions_breakdown = test_month_data["emissions_breakdown"]
            
            # Check for F-Gas emissions in the breakdown
            f_gas_found = False
            for gas_type in ["r134a_gas", "r600a_gas", "r410a_gas", "r32_gas", "co2_fire", "fm200_fire"]:
                if gas_type in emissions_breakdown:
                    f_gas_found = True
                    gas_data = emissions_breakdown[gas_type]
                    logger.info(f"{gas_type} emissions: {gas_data.get('co2_emissions', 0)} kg CO2e")
                    self.assertIn("co2_emissions", gas_data, f"{gas_type} data should contain co2_emissions")
                    self.assertIn("category", gas_data, f"{gas_type} data should contain category")
                    
                    # Verify category is correct
                    if gas_type in ["r134a_gas", "r600a_gas", "r410a_gas", "r32_gas"]:
                        self.assertEqual(gas_data["category"], "refrigerant", f"{gas_type} should be categorized as refrigerant")
                    elif gas_type in ["co2_fire", "fm200_fire"]:
                        self.assertEqual(gas_data["category"], "fire_suppressant", f"{gas_type} should be categorized as fire_suppressant")
            
            self.assertTrue(f_gas_found, "At least one F-Gas should be in the emissions breakdown")
            
            # Verify total carbon emissions is high due to F-Gas
            total_co2 = data["total_carbon_emissions"]
            logger.info(f"Total carbon emissions for the year: {total_co2} kg CO2e")
            self.assertGreater(total_co2, 20000, "Total carbon emissions should be high due to F-Gas")
            
            # Verify carbon tonnes is correctly calculated
            carbon_tonnes = data["total_carbon_tonnes"]
            expected_tonnes = total_co2 / 1000.0
            self.assertAlmostEqual(carbon_tonnes, expected_tonnes, places=3, msg="Carbon tonnes should be total CO2 / 1000")
            
            logger.info("✅ GET /api/analytics/carbon-footprint with F-Gas data test passed")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/analytics/carbon-footprint: {str(e)}")
            raise
    
    def cleanup_test_consumption(self):
        """Clean up test consumption data to avoid conflicts"""
        logger.info("Cleaning up test consumption data...")
        
        url = f"{self.api_url}/consumptions"
        params = {
            "client_id": KAYA_CLIENT_ID,
            "year": self.test_year
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            consumptions = response.json()
            
            for consumption in consumptions:
                if consumption.get("month") == self.test_month and consumption.get("year") == self.test_year:
                    consumption_id = consumption.get("id")
                    delete_url = f"{self.api_url}/consumptions/{consumption_id}"
                    
                    delete_response = requests.delete(delete_url, headers=self.headers)
                    if delete_response.status_code == 200:
                        logger.info(f"Deleted existing consumption for {self.test_year}-{self.test_month}")
                    else:
                        logger.warning(f"Failed to delete consumption: {delete_response.status_code}")

def run_tests():
    """Run all F-Gas carbon tests"""
    logger.info("Starting F-Gas carbon tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(TestFGasCarbon("test_post_consumption_with_f_gas"))
    suite.addTest(TestFGasCarbon("test_put_consumption_with_f_gas"))
    suite.addTest(TestFGasCarbon("test_carbon_footprint_analytics"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All F-Gas carbon tests PASSED")
        return True
    else:
        logger.error("Some F-Gas carbon tests FAILED")
        for error in result.errors:
            logger.error(f"Error: {error[1]}")
        for failure in result.failures:
            logger.error(f"Failure: {failure[1]}")
        return False

if __name__ == "__main__":
    run_tests()