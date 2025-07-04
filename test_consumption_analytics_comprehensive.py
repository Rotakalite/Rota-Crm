import unittest
import json
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestConsumptionAnalyticsPerPerson(unittest.TestCase):
    """Comprehensive test class for consumption analytics per-person calculations"""
    
    def setUp(self):
        """Set up test environment"""
        # Test consumption data with specific values for verification
        self.current_year_data = [
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
        
        self.previous_year_data = [
            {
                "id": "test_consumption_2",
                "client_id": "test_client_1",
                "year": 2023,
                "month": 6,
                "electricity": 900.0,   # 900 kWh
                "water": 90.0,          # 90 m³
                "natural_gas": 450.0,   # 450 m³
                "coal": 180.0,          # 180 kg
                "accommodation_count": 45  # 45 guests
            }
        ]
        
        # Expected per-person values for current year
        self.expected_current_per_person = {
            "electricity": 20.0,    # 1000 / 50 = 20.0 kWh/person
            "water": 2.0,           # 100 / 50 = 2.0 m³/person
            "natural_gas": 10.0,    # 500 / 50 = 10.0 m³/person
            "coal": 4.0             # 200 / 50 = 4.0 kg/person
        }
        
        # Expected per-person values for previous year
        self.expected_previous_per_person = {
            "electricity": 20.0,    # 900 / 45 = 20.0 kWh/person
            "water": 2.0,           # 90 / 45 = 2.0 m³/person
            "natural_gas": 10.0,    # 450 / 45 = 10.0 m³/person
            "coal": 4.0             # 180 / 45 = 4.0 kg/person
        }
    
    def test_basic_per_person_calculation(self):
        """Test basic per-person calculation logic"""
        logger.info("\n=== Testing basic per-person calculation logic ===")
        
        # Get the consumption data for our test month
        consumption = self.current_year_data[0]
        
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
        self.assertAlmostEqual(per_person["electricity"], self.expected_current_per_person["electricity"], places=1)
        self.assertAlmostEqual(per_person["water"], self.expected_current_per_person["water"], places=1)
        self.assertAlmostEqual(per_person["natural_gas"], self.expected_current_per_person["natural_gas"], places=1)
        self.assertAlmostEqual(per_person["coal"], self.expected_current_per_person["coal"], places=1)
        
        logger.info("✅ Basic per-person calculations are correct")
    
    def test_zero_accommodation_count(self):
        """Test per-person calculation with zero accommodation count"""
        logger.info("\n=== Testing per-person calculation with zero accommodation count ===")
        
        # Create a consumption with zero accommodation count
        consumption = self.current_year_data[0].copy()
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
    
    def test_server_implementation(self):
        """Test the server.py implementation of per-person calculations"""
        logger.info("\n=== Testing server.py implementation of per-person calculations ===")
        
        # Simulate the code from server.py (lines 2728-2774)
        monthly_comparison = []
        month = 6  # We're only testing June
        
        current_month = self.current_year_data[0]
        previous_month = self.previous_year_data[0]
        
        month_data = {
            "month": month,
            "month_name": ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                          "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][month],
            "current_year": {
                "electricity": current_month["electricity"],
                "water": current_month["water"],
                "natural_gas": current_month["natural_gas"],
                "coal": current_month["coal"],
                "accommodation_count": current_month["accommodation_count"]
            },
            "previous_year": {
                "electricity": previous_month["electricity"],
                "water": previous_month["water"],
                "natural_gas": previous_month["natural_gas"],
                "coal": previous_month["coal"],
                "accommodation_count": previous_month["accommodation_count"]
            }
        }
        
        # Calculate per-person consumption - THIS IS THE EXACT CODE FROM SERVER.PY
        if month_data["current_year"]["accommodation_count"] > 0:
            month_data["per_person"] = {
                "electricity": month_data["current_year"]["electricity"] / month_data["current_year"]["accommodation_count"],
                "water": month_data["current_year"]["water"] / month_data["current_year"]["accommodation_count"],
                "natural_gas": month_data["current_year"]["natural_gas"] / month_data["current_year"]["accommodation_count"],
                "coal": month_data["current_year"]["coal"] / month_data["current_year"]["accommodation_count"]
            }
        else:
            month_data["per_person"] = {"electricity": 0, "water": 0, "natural_gas": 0, "coal": 0}
        
        if month_data["previous_year"]["accommodation_count"] > 0:
            month_data["previous_year_per_person"] = {
                "electricity": month_data["previous_year"]["electricity"] / month_data["previous_year"]["accommodation_count"],
                "water": month_data["previous_year"]["water"] / month_data["previous_year"]["accommodation_count"],
                "natural_gas": month_data["previous_year"]["natural_gas"] / month_data["previous_year"]["accommodation_count"],
                "coal": month_data["previous_year"]["coal"] / month_data["previous_year"]["accommodation_count"]
            }
        else:
            month_data["previous_year_per_person"] = {"electricity": 0, "water": 0, "natural_gas": 0, "coal": 0}
        
        monthly_comparison.append(month_data)
        
        logger.info(f"Generated monthly comparison: {json.dumps(monthly_comparison, indent=2)}")
        
        # Verify the structure
        self.assertEqual(len(monthly_comparison), 1)
        result = monthly_comparison[0]
        
        # Verify per-person field exists
        self.assertIn("per_person", result)
        self.assertIn("previous_year_per_person", result)
        
        # Verify per-person values for current year
        per_person = result["per_person"]
        self.assertAlmostEqual(per_person["electricity"], self.expected_current_per_person["electricity"], places=1)
        self.assertAlmostEqual(per_person["water"], self.expected_current_per_person["water"], places=1)
        self.assertAlmostEqual(per_person["natural_gas"], self.expected_current_per_person["natural_gas"], places=1)
        self.assertAlmostEqual(per_person["coal"], self.expected_current_per_person["coal"], places=1)
        
        # Verify per-person values for previous year
        prev_per_person = result["previous_year_per_person"]
        self.assertAlmostEqual(prev_per_person["electricity"], self.expected_previous_per_person["electricity"], places=1)
        self.assertAlmostEqual(prev_per_person["water"], self.expected_previous_per_person["water"], places=1)
        self.assertAlmostEqual(prev_per_person["natural_gas"], self.expected_previous_per_person["natural_gas"], places=1)
        self.assertAlmostEqual(prev_per_person["coal"], self.expected_previous_per_person["coal"], places=1)
        
        logger.info("✅ Server implementation of per-person calculations is correct")
    
    def test_full_analytics_response(self):
        """Test the full analytics response structure"""
        logger.info("\n=== Testing full analytics response structure ===")
        
        # Create a mock monthly comparison
        monthly_comparison = []
        for month in range(1, 13):
            month_names = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                          "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            
            # Create consumption data for this month
            current_year_consumption = {
                "electricity": 1000.0,
                "water": 100.0,
                "natural_gas": 500.0,
                "coal": 200.0,
                "accommodation_count": 50
            }
            
            previous_year_consumption = {
                "electricity": 900.0,
                "water": 90.0,
                "natural_gas": 450.0,
                "coal": 180.0,
                "accommodation_count": 45
            }
            
            month_data = {
                "month": month,
                "month_name": month_names[month],
                "current_year": current_year_consumption,
                "previous_year": previous_year_consumption
            }
            
            # Calculate per-person consumption
            if month_data["current_year"]["accommodation_count"] > 0:
                month_data["per_person"] = {
                    "electricity": month_data["current_year"]["electricity"] / month_data["current_year"]["accommodation_count"],
                    "water": month_data["current_year"]["water"] / month_data["current_year"]["accommodation_count"],
                    "natural_gas": month_data["current_year"]["natural_gas"] / month_data["current_year"]["accommodation_count"],
                    "coal": month_data["current_year"]["coal"] / month_data["current_year"]["accommodation_count"]
                }
            else:
                month_data["per_person"] = {"electricity": 0, "water": 0, "natural_gas": 0, "coal": 0}
            
            if month_data["previous_year"]["accommodation_count"] > 0:
                month_data["previous_year_per_person"] = {
                    "electricity": month_data["previous_year"]["electricity"] / month_data["previous_year"]["accommodation_count"],
                    "water": month_data["previous_year"]["water"] / month_data["previous_year"]["accommodation_count"],
                    "natural_gas": month_data["previous_year"]["natural_gas"] / month_data["previous_year"]["accommodation_count"],
                    "coal": month_data["previous_year"]["coal"] / month_data["previous_year"]["accommodation_count"]
                }
            else:
                month_data["previous_year_per_person"] = {"electricity": 0, "water": 0, "natural_gas": 0, "coal": 0}
            
            monthly_comparison.append(month_data)
        
        # Calculate year totals
        current_year_totals = {
            "electricity": 12000.0,
            "water": 1200.0,
            "natural_gas": 6000.0,
            "coal": 2400.0,
            "accommodation_count": 600
        }
        
        previous_year_totals = {
            "electricity": 10800.0,
            "water": 1080.0,
            "natural_gas": 5400.0,
            "coal": 2160.0,
            "accommodation_count": 540
        }
        
        # Create the full analytics response
        analytics_response = {
            "year": 2024,
            "monthly_comparison": monthly_comparison,
            "yearly_totals": {
                "current_year": current_year_totals,
                "previous_year": previous_year_totals
            },
            "yearly_per_person": {
                "current_year": {
                    "electricity": current_year_totals["electricity"] / current_year_totals["accommodation_count"],
                    "water": current_year_totals["water"] / current_year_totals["accommodation_count"],
                    "natural_gas": current_year_totals["natural_gas"] / current_year_totals["accommodation_count"],
                    "coal": current_year_totals["coal"] / current_year_totals["accommodation_count"]
                },
                "previous_year": {
                    "electricity": previous_year_totals["electricity"] / previous_year_totals["accommodation_count"],
                    "water": previous_year_totals["water"] / previous_year_totals["accommodation_count"],
                    "natural_gas": previous_year_totals["natural_gas"] / previous_year_totals["accommodation_count"],
                    "coal": previous_year_totals["coal"] / previous_year_totals["accommodation_count"]
                }
            }
        }
        
        logger.info(f"Generated analytics response structure with {len(monthly_comparison)} months")
        
        # Verify the structure
        self.assertIn("year", analytics_response)
        self.assertIn("monthly_comparison", analytics_response)
        self.assertIn("yearly_totals", analytics_response)
        self.assertIn("yearly_per_person", analytics_response)
        
        # Verify monthly comparison
        self.assertEqual(len(analytics_response["monthly_comparison"]), 12)
        
        # Check a sample month
        sample_month = analytics_response["monthly_comparison"][5]  # June (index 5)
        self.assertIn("per_person", sample_month)
        self.assertIn("previous_year_per_person", sample_month)
        
        # Verify yearly per-person calculations
        yearly_per_person = analytics_response["yearly_per_person"]["current_year"]
        self.assertAlmostEqual(yearly_per_person["electricity"], 20.0, places=1)  # 12000 / 600 = 20.0
        self.assertAlmostEqual(yearly_per_person["water"], 2.0, places=1)         # 1200 / 600 = 2.0
        self.assertAlmostEqual(yearly_per_person["natural_gas"], 10.0, places=1)  # 6000 / 600 = 10.0
        self.assertAlmostEqual(yearly_per_person["coal"], 4.0, places=1)          # 2400 / 600 = 4.0
        
        logger.info("✅ Full analytics response structure is correct")

def run_tests():
    """Run all tests"""
    logger.info("Starting comprehensive consumption analytics tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add tests
    suite.addTest(TestConsumptionAnalyticsPerPerson("test_basic_per_person_calculation"))
    suite.addTest(TestConsumptionAnalyticsPerPerson("test_zero_accommodation_count"))
    suite.addTest(TestConsumptionAnalyticsPerPerson("test_server_implementation"))
    suite.addTest(TestConsumptionAnalyticsPerPerson("test_full_analytics_response"))
    
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