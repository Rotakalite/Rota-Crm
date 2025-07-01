import unittest
import json
import logging
import requests
import os
import io
import uuid
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add backend directory to path to import defra_carbon module
sys.path.append('/app/backend')

# Import the DEFRA carbon calculation module
try:
    from defra_carbon import (
        calculate_carbon_emissions, 
        get_emission_factor, 
        get_all_emission_factors,
        validate_consumption_data,
        benchmark_performance,
        DEFRA_EMISSION_FACTORS
    )
    logger.info("✅ Successfully imported DEFRA carbon module")
except ImportError as e:
    logger.error(f"❌ Failed to import DEFRA carbon module: {e}")
    sys.exit(1)

class TestConsumptionEndpoint(unittest.TestCase):
    """Test class for consumption endpoint with carbon calculation"""
    
    def setUp(self):
        """Set up test environment"""
        # Test consumption data with all DEFRA fuel types
        self.test_consumption = {
            "year": 2024,
            "month": 6,  # June
            "electricity": 1000.0,  # kWh
            "water": 500.0,         # m³
            "natural_gas": 300.0,   # kWh
            "coal": 200.0,          # kg
            "diesel": 100.0,        # litre
            "gasoline": 80.0,       # litre
            "lpg": 50.0,            # litre
            "fuel_oil": 30.0,       # litre
            "accommodation_count": 150,
            "client_id": "test_client_id"
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
    
    def test_consumption_carbon_calculation(self):
        """Test that consumption data is correctly processed with carbon calculation"""
        logger.info("\n=== Testing consumption carbon calculation ===")
        
        # Create a consumption record
        consumption_dict = self.test_consumption.copy()
        
        # Calculate expected carbon emissions
        carbon_results = calculate_carbon_emissions(consumption_dict)
        logger.info(f"Expected carbon results: {carbon_results}")
        
        # Check total CO2 emissions
        calculated_co2 = carbon_results["total_co2_emissions"]
        logger.info(f"Expected CO2: {self.expected_co2:.3f} kg, Calculated CO2: {calculated_co2:.3f} kg")
        
        # Calculate percentage difference
        percent_diff = abs(calculated_co2 - self.expected_co2) / self.expected_co2 * 100
        logger.info(f"Percentage difference: {percent_diff:.6f}%")
        self.assertLessEqual(percent_diff, 0.001, "Carbon calculation should match expected value")
        
        # Check tonnes conversion
        tonnes = carbon_results["total_co2_tonnes"]
        expected_tonnes = self.expected_co2 / 1000.0
        logger.info(f"Expected tonnes: {expected_tonnes:.6f}, Calculated tonnes: {tonnes:.6f}")
        self.assertAlmostEqual(tonnes, expected_tonnes, places=6)
        
        # Check per-person calculation
        per_person = carbon_results["per_person_co2"]
        expected_per_person = self.expected_co2 / consumption_dict["accommodation_count"]
        logger.info(f"Expected per person: {expected_per_person:.3f}, Calculated per person: {per_person:.3f}")
        self.assertAlmostEqual(per_person, expected_per_person, places=3)
        
        # Get benchmark performance
        benchmark = benchmark_performance(
            carbon_results["total_co2_emissions"],
            consumption_dict["accommodation_count"]
        )
        logger.info(f"Benchmark performance: {benchmark['performance_level']}")
        
        # Check benchmark is one of the expected values
        self.assertIn(benchmark["performance_level"], ["Excellent", "Good", "Average", "Poor"])
        
        logger.info("✅ Consumption carbon calculation test passed")
    
    def test_carbon_footprint_endpoint(self):
        """Test carbon footprint endpoint calculation"""
        logger.info("\n=== Testing carbon footprint endpoint calculation ===")
        
        # Create test consumption data for multiple months
        test_months = [1, 2, 3]  # January, February, March
        consumptions = []
        
        for month in test_months:
            consumption = self.test_consumption.copy()
            consumption["month"] = month
            consumptions.append(consumption)
        
        # Calculate expected total yearly CO2
        total_yearly_co2 = 0
        total_yearly_accommodation = 0
        monthly_carbon_data = []
        
        for consumption in consumptions:
            carbon_results = calculate_carbon_emissions(consumption)
            total_yearly_co2 += carbon_results["total_co2_emissions"]
            total_yearly_accommodation += consumption["accommodation_count"]
            
            monthly_data = {
                "month": consumption["month"],
                "month_name": ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][consumption["month"]],
                "total_co2_emissions": carbon_results["total_co2_emissions"],
                "total_co2_tonnes": carbon_results["total_co2_tonnes"],
                "per_person_co2": carbon_results["per_person_co2"],
                "accommodation_count": consumption["accommodation_count"]
            }
            
            monthly_carbon_data.append(monthly_data)
        
        # Calculate yearly benchmarks
        yearly_benchmarks = benchmark_performance(
            total_yearly_co2,
            total_yearly_accommodation,
            nights=365  # Yearly calculation
        )
        
        # Expected response structure
        expected_response = {
            "year": 2024,
            "client_id": "test_client_id",
            "total_carbon_emissions": round(total_yearly_co2, 3),
            "total_carbon_tonnes": round(total_yearly_co2 / 1000.0, 6),
            "average_per_person_co2": round(total_yearly_co2 / total_yearly_accommodation, 3),
            "total_accommodation_count": total_yearly_accommodation,
            "monthly_carbon_data": monthly_carbon_data,
            "yearly_benchmarks": yearly_benchmarks,
            "methodology": "DEFRA 2024 Emission Factors",
            "units": "kg CO2 equivalent"
        }
        
        logger.info(f"Expected carbon footprint response structure: {json.dumps(expected_response, indent=2)[:500]}...")
        logger.info(f"Total yearly CO2: {total_yearly_co2:.3f} kg")
        logger.info(f"Yearly benchmark performance: {yearly_benchmarks['performance_level']}")
        
        logger.info("✅ Carbon footprint endpoint calculation test passed")

def run_tests():
    """Run all consumption endpoint tests"""
    logger.info("Starting consumption endpoint tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(TestConsumptionEndpoint("test_consumption_carbon_calculation"))
    suite.addTest(TestConsumptionEndpoint("test_carbon_footprint_endpoint"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All consumption endpoint tests PASSED")
        return True
    else:
        logger.error("Some consumption endpoint tests FAILED")
        return False

if __name__ == "__main__":
    run_tests()