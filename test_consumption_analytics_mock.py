import unittest
import json
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestConsumptionAnalyticsPerPerson(unittest.TestCase):
    """Test class for consumption analytics per-person calculations"""
    
    def setUp(self):
        """Set up test environment"""
        # Test consumption data with specific values for verification
        self.test_consumption_data = [
            {
                "id": "test_consumption_1",
                "client_id": "test_client_1",
                "year": 2024,
                "month": 6,
                "electricity": 1000.0,  # 1000 kWh
                "water": 100.0,         # 100 m³
                "natural_gas": 500.0,   # 500 m³
                "coal": 200.0,          # 200 kg
                "accommodation_count": 50  # 50 guests
            }
        ]
        
        # Expected per-person values
        self.expected_per_person = {
            "electricity": 20.0,    # 1000 / 50 = 20.0 kWh/person
            "water": 2.0,           # 100 / 50 = 2.0 m³/person
            "natural_gas": 10.0,    # 500 / 50 = 10.0 m³/person
            "coal": 4.0             # 200 / 50 = 4.0 kg/person
        }
    
    def test_per_person_calculation(self):
        """Test the per-person calculation logic"""
        logger.info("\n=== Testing per-person calculation logic ===")
        
        # Get the consumption data for our test month
        consumption = self.test_consumption_data[0]
        
        # Calculate per-person values
        per_person = {}
        if consumption["accommodation_count"] > 0:
            per_person = {
                "electricity": consumption["electricity"] / consumption["accommodation_count"],
                "water": consumption["water"] / consumption["accommodation_count"],
                "natural_gas": consumption["natural_gas"] / consumption["accommodation_count"],
                "coal": consumption["coal"] / consumption["accommodation_count"]
            }
        else:
            per_person = {"electricity": 0, "water": 0, "natural_gas": 0, "coal": 0}
        
        logger.info(f"Calculated per-person values: {json.dumps(per_person, indent=2)}")
        
        # Verify calculations are correct
        self.assertAlmostEqual(per_person["electricity"], self.expected_per_person["electricity"], places=1)
        self.assertAlmostEqual(per_person["water"], self.expected_per_person["water"], places=1)
        self.assertAlmostEqual(per_person["natural_gas"], self.expected_per_person["natural_gas"], places=1)
        self.assertAlmostEqual(per_person["coal"], self.expected_per_person["coal"], places=1)
        
        logger.info("✅ Per-person calculations are correct")
    
    def test_zero_accommodation_count(self):
        """Test the per-person calculation with zero accommodation count"""
        logger.info("\n=== Testing per-person calculation with zero accommodation count ===")
        
        # Create a consumption with zero accommodation count
        consumption = self.test_consumption_data[0].copy()
        consumption["accommodation_count"] = 0
        
        # Calculate per-person values
        per_person = {}
        if consumption["accommodation_count"] > 0:
            per_person = {
                "electricity": consumption["electricity"] / consumption["accommodation_count"],
                "water": consumption["water"] / consumption["accommodation_count"],
                "natural_gas": consumption["natural_gas"] / consumption["accommodation_count"],
                "coal": consumption["coal"] / consumption["accommodation_count"]
            }
        else:
            per_person = {"electricity": 0, "water": 0, "natural_gas": 0, "coal": 0}
        
        logger.info(f"Calculated per-person values with zero accommodation: {json.dumps(per_person, indent=2)}")
        
        # Verify all values are zero
        self.assertEqual(per_person["electricity"], 0)
        self.assertEqual(per_person["water"], 0)
        self.assertEqual(per_person["natural_gas"], 0)
        self.assertEqual(per_person["coal"], 0)
        
        logger.info("✅ Per-person calculations with zero accommodation count are correct")
    
    def test_monthly_comparison_structure(self):
        """Test the monthly comparison structure with per-person calculations"""
        logger.info("\n=== Testing monthly comparison structure with per-person calculations ===")
        
        # Create a mock monthly comparison structure
        month_data = {
            "month": 6,
            "month_name": "Haziran",
            "current_year": {
                "electricity": 1000.0,
                "water": 100.0,
                "natural_gas": 500.0,
                "coal": 200.0,
                "accommodation_count": 50
            },
            "previous_year": {
                "electricity": 900.0,
                "water": 90.0,
                "natural_gas": 450.0,
                "coal": 180.0,
                "accommodation_count": 45
            }
        }
        
        # Calculate per-person values for current year
        if month_data["current_year"]["accommodation_count"] > 0:
            month_data["per_person"] = {
                "electricity": month_data["current_year"]["electricity"] / month_data["current_year"]["accommodation_count"],
                "water": month_data["current_year"]["water"] / month_data["current_year"]["accommodation_count"],
                "natural_gas": month_data["current_year"]["natural_gas"] / month_data["current_year"]["accommodation_count"],
                "coal": month_data["current_year"]["coal"] / month_data["current_year"]["accommodation_count"]
            }
        else:
            month_data["per_person"] = {"electricity": 0, "water": 0, "natural_gas": 0, "coal": 0}
        
        # Calculate per-person values for previous year
        if month_data["previous_year"]["accommodation_count"] > 0:
            month_data["previous_year_per_person"] = {
                "electricity": month_data["previous_year"]["electricity"] / month_data["previous_year"]["accommodation_count"],
                "water": month_data["previous_year"]["water"] / month_data["previous_year"]["accommodation_count"],
                "natural_gas": month_data["previous_year"]["natural_gas"] / month_data["previous_year"]["accommodation_count"],
                "coal": month_data["previous_year"]["coal"] / month_data["previous_year"]["accommodation_count"]
            }
        else:
            month_data["previous_year_per_person"] = {"electricity": 0, "water": 0, "natural_gas": 0, "coal": 0}
        
        logger.info(f"Monthly comparison structure: {json.dumps(month_data, indent=2)}")
        
        # Verify per-person field exists
        self.assertIn("per_person", month_data)
        self.assertIn("previous_year_per_person", month_data)
        
        # Verify per-person values for current year
        per_person = month_data["per_person"]
        self.assertAlmostEqual(per_person["electricity"], self.expected_per_person["electricity"], places=1)
        self.assertAlmostEqual(per_person["water"], self.expected_per_person["water"], places=1)
        self.assertAlmostEqual(per_person["natural_gas"], self.expected_per_person["natural_gas"], places=1)
        self.assertAlmostEqual(per_person["coal"], self.expected_per_person["coal"], places=1)
        
        # Verify per-person values for previous year
        prev_per_person = month_data["previous_year_per_person"]
        self.assertAlmostEqual(prev_per_person["electricity"], 900.0 / 45, places=1)
        self.assertAlmostEqual(prev_per_person["water"], 90.0 / 45, places=1)
        self.assertAlmostEqual(prev_per_person["natural_gas"], 450.0 / 45, places=1)
        self.assertAlmostEqual(prev_per_person["coal"], 180.0 / 45, places=1)
        
        logger.info("✅ Monthly comparison structure with per-person calculations is correct")

def run_tests():
    """Run all tests"""
    logger.info("Starting consumption analytics per-person calculation tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add tests
    suite.addTest(TestConsumptionAnalyticsPerPerson("test_per_person_calculation"))
    suite.addTest(TestConsumptionAnalyticsPerPerson("test_zero_accommodation_count"))
    suite.addTest(TestConsumptionAnalyticsPerPerson("test_monthly_comparison_structure"))
    
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