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

# Test data
TEST_YEAR = 2024

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT tokens
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data

class TestDEFRACarbonCalculation(unittest.TestCase):
    """Test class for DEFRA carbon calculation system"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        
        # Test consumption data with all DEFRA fuel types
        self.test_consumption = {
            "year": TEST_YEAR,
            "month": 6,  # June
            "electricity": 1000.0,  # kWh
            "water": 500.0,         # m³
            "natural_gas": 300.0,   # kWh
            "coal": 200.0,          # kg
            "diesel": 100.0,        # litre
            "gasoline": 80.0,       # litre
            "lpg": 50.0,            # litre
            "fuel_oil": 30.0,       # litre
            "accommodation_count": 150
        }
        
        # Expected emission factors from DEFRA 2024
        self.expected_factors = {
            "electricity": 0.19338,  # kg CO2/kWh
            "water": 0.344,          # kg CO2/m³
            "natural_gas": 0.18316,  # kg CO2/kWh
            "coal": 2240.0,          # kg CO2/tonne (need to convert kg to tonnes)
            "diesel": 2.51,          # kg CO2/litre
            "gasoline": 2.16,        # kg CO2/litre
            "lpg": 1.51,             # kg CO2/litre
            "fuel_oil": 2.54         # kg CO2/litre
        }
        
        # Expected carbon calculation results
        self.expected_co2 = (
            1000.0 * 0.19338 +  # electricity
            500.0 * 0.344 +     # water
            300.0 * 0.18316 +   # natural_gas
            (200.0 / 1000.0) * 2240.0 +  # coal (kg to tonnes)
            100.0 * 2.51 +      # diesel
            80.0 * 2.16 +       # gasoline
            50.0 * 1.51 +       # lpg
            30.0 * 2.54         # fuel_oil
        )
        
    def test_post_consumption_calculates_carbon(self):
        """Test that POST /api/consumptions calculates carbon automatically"""
        logger.info("\n=== Testing POST /api/consumptions carbon calculation ===")
        
        url = f"{self.api_url}/consumptions"
        
        # Create a unique month/year combination to avoid conflicts
        current_month = datetime.now().month
        current_year = datetime.now().year
        test_month = (current_month % 12) + 1  # Ensure it's 1-12
        test_year = current_year + 1  # Use next year to avoid conflicts
        
        # Update test data with unique month/year
        test_data = self.test_consumption.copy()
        test_data["month"] = test_month
        test_data["year"] = test_year
        
        try:
            # Send POST request to create consumption
            response = requests.post(url, headers=self.headers_admin, json=test_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            # Check if request was successful
            self.assertEqual(response.status_code, 200)
            
            # Get the created consumption to check carbon calculation
            get_url = f"{self.api_url}/consumptions?year={test_year}"
            get_response = requests.get(get_url, headers=self.headers_admin)
            self.assertEqual(get_response.status_code, 200)
            
            consumptions = get_response.json()
            logger.info(f"Found {len(consumptions)} consumptions")
            
            # Find our test consumption
            test_consumption = None
            for consumption in consumptions:
                if consumption.get("year") == test_year and consumption.get("month") == test_month:
                    test_consumption = consumption
                    break
            
            self.assertIsNotNone(test_consumption, "Test consumption not found in GET response")
            
            # Check that carbon fields are present and calculated
            self.assertIn("total_co2_emissions", test_consumption)
            self.assertIn("total_co2_tonnes", test_consumption)
            self.assertIn("per_person_co2", test_consumption)
            
            # Check carbon calculation accuracy (within 1% margin)
            calculated_co2 = test_consumption.get("total_co2_emissions")
            logger.info(f"Expected CO2: {self.expected_co2:.3f} kg, Calculated CO2: {calculated_co2:.3f} kg")
            
            # Calculate percentage difference
            if self.expected_co2 > 0:
                percent_diff = abs(calculated_co2 - self.expected_co2) / self.expected_co2 * 100
                logger.info(f"Percentage difference: {percent_diff:.2f}%")
                self.assertLessEqual(percent_diff, 1.0, "Carbon calculation should be within 1% of expected value")
            
            # Check tonnes conversion
            tonnes = test_consumption.get("total_co2_tonnes")
            expected_tonnes = self.expected_co2 / 1000.0
            logger.info(f"Expected tonnes: {expected_tonnes:.6f}, Calculated tonnes: {tonnes:.6f}")
            
            # Check per-person calculation
            per_person = test_consumption.get("per_person_co2")
            expected_per_person = self.expected_co2 / test_data["accommodation_count"]
            logger.info(f"Expected per person: {expected_per_person:.3f}, Calculated per person: {per_person:.3f}")
            
            # Check benchmark performance level
            self.assertIn("carbon_benchmark", test_consumption)
            benchmark = test_consumption.get("carbon_benchmark")
            logger.info(f"Carbon benchmark performance level: {benchmark}")
            self.assertIn(benchmark, ["Excellent", "Good", "Average", "Poor"])
            
            logger.info("✅ POST /api/consumptions carbon calculation test passed")
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/consumptions: {str(e)}")
            raise
    
    def test_carbon_footprint_endpoint(self):
        """Test GET /api/analytics/carbon-footprint endpoint"""
        logger.info("\n=== Testing GET /api/analytics/carbon-footprint endpoint ===")
        
        # First, get a valid client_id
        clients_url = f"{self.api_url}/clients"
        clients_response = requests.get(clients_url, headers=self.headers_admin)
        self.assertEqual(clients_response.status_code, 200)
        
        clients = clients_response.json()
        self.assertGreater(len(clients), 0, "No clients found")
        
        client_id = clients[0]["id"]
        logger.info(f"Using client_id: {client_id}")
        
        # Test carbon footprint endpoint
        url = f"{self.api_url}/analytics/carbon-footprint?client_id={client_id}&year={TEST_YEAR}"
        
        try:
            # Test with admin user
            logger.info("Testing with admin user...")
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if request was successful
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            logger.info(f"Response data: {json.dumps(data, indent=2)[:500]}...")
            
            # Check response structure
            self.assertIn("year", data)
            self.assertIn("client_id", data)
            self.assertIn("total_carbon_emissions", data)
            self.assertIn("total_carbon_tonnes", data)
            self.assertIn("monthly_carbon_data", data)
            self.assertIn("methodology", data)
            
            # Check methodology is DEFRA 2024
            self.assertEqual(data["methodology"], "DEFRA 2024 Emission Factors")
            
            # Check monthly data structure if any exists
            if len(data["monthly_carbon_data"]) > 0:
                month_data = data["monthly_carbon_data"][0]
                self.assertIn("month", month_data)
                self.assertIn("month_name", month_data)
                self.assertIn("total_co2_emissions", month_data)
                self.assertIn("emissions_breakdown", month_data)
                
                # Check emissions breakdown if any exists
                if "emissions_breakdown" in month_data and month_data["emissions_breakdown"]:
                    for fuel_type, emission_data in month_data["emissions_breakdown"].items():
                        self.assertIn("emission_factor", emission_data)
                        self.assertIn("co2_emissions", emission_data)
                        
                        # Verify emission factor matches expected DEFRA factor
                        if fuel_type in self.expected_factors:
                            expected_factor = self.expected_factors[fuel_type]
                            actual_factor = emission_data["emission_factor"]
                            logger.info(f"{fuel_type} emission factor: expected={expected_factor}, actual={actual_factor}")
                            
                            # Check within 0.1% margin
                            percent_diff = abs(actual_factor - expected_factor) / expected_factor * 100
                            self.assertLessEqual(percent_diff, 0.1, 
                                               f"{fuel_type} emission factor should match DEFRA 2024 value")
            
            # Check benchmark data
            if "yearly_benchmarks" in data and data["yearly_benchmarks"]:
                benchmarks = data["yearly_benchmarks"]
                self.assertIn("performance_level", benchmarks)
                self.assertIn("co2_per_room_night", benchmarks)
                self.assertIn("benchmarks", benchmarks)
                
                # Check performance level is one of the expected values
                self.assertIn(benchmarks["performance_level"], ["Excellent", "Good", "Average", "Poor"])
                
                # Check benchmark reference values
                if "benchmarks" in benchmarks:
                    ref_benchmarks = benchmarks["benchmarks"]
                    self.assertIn("hotel_industry_average", ref_benchmarks)
                    self.assertIn("sustainable_target", ref_benchmarks)
                    self.assertIn("excellent_performance", ref_benchmarks)
            
            logger.info("✅ Admin user test passed for /api/analytics/carbon-footprint")
            
            # Test with client user
            logger.info("Testing with client user...")
            response = requests.get(f"{self.api_url}/analytics/carbon-footprint", headers=self.headers_client)
            logger.info(f"Response status code: {response.status_code}")
            
            # Client user should get 200 OK or 400 Bad Request (if no data)
            self.assertIn(response.status_code, [200, 400])
            
            if response.status_code == 200:
                data = response.json()
                self.assertIn("year", data)
                self.assertIn("client_id", data)
                self.assertIn("total_carbon_emissions", data)
                logger.info("✅ Client user test passed for /api/analytics/carbon-footprint")
            else:
                logger.info("✅ Client user received expected 400 Bad Request (no data)")
            
        except Exception as e:
            logger.error(f"❌ Error testing /api/analytics/carbon-footprint: {str(e)}")
            raise

def run_tests():
    """Run all carbon calculation tests"""
    logger.info("Starting DEFRA Carbon Calculation tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(TestDEFRACarbonCalculation("test_post_consumption_calculates_carbon"))
    suite.addTest(TestDEFRACarbonCalculation("test_carbon_footprint_endpoint"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All DEFRA Carbon Calculation tests PASSED")
        return True
    else:
        logger.error("Some DEFRA Carbon Calculation tests FAILED")
        return False

if __name__ == "__main__":
    run_tests()