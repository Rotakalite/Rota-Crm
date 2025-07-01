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

# Add backend directory to path to import modules
sys.path.append('/app/backend')

# Import the DEFRA carbon calculation module
try:
    from defra_carbon import (
        calculate_carbon_emissions, 
        get_emission_factor, 
        benchmark_performance,
        DEFRA_EMISSION_FACTORS
    )
    logger.info("✅ Successfully imported DEFRA carbon module")
except ImportError as e:
    logger.error(f"❌ Failed to import DEFRA carbon module: {e}")
    sys.exit(1)

class TestFGasAPI(unittest.TestCase):
    """Test class for F-Gas API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        # Test data with F-Gas values from the review request
        self.f_gas_consumption_data = {
            "year": 2024,
            "month": 6,  # June
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
        
        # Expected CO2 emissions from F-Gases
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
        
        # Calculate expected total CO2 including regular consumption
        # Regular consumption: ~1,500 kg CO2e
        # F-Gases: ~23,107.5 kg CO2e
        # Total: ~24,607.5 kg CO2e
        self.expected_total_co2 = 24500  # Approximate value for validation
    
    def test_f_gas_carbon_calculation(self):
        """Test carbon calculation with F-Gas values"""
        logger.info("\n=== Testing carbon calculation with F-Gas values ===")
        
        # Calculate carbon emissions with F-Gas values
        results = calculate_carbon_emissions(self.f_gas_consumption_data)
        logger.info(f"F-Gas carbon calculation results: {json.dumps(results, indent=2)}")
        
        # Check emissions breakdown includes F-Gas emissions
        breakdown = results["emissions_breakdown"]
        
        # Check each F-Gas emission
        for gas_type, expected_co2 in self.expected_f_gas_emissions.items():
            self.assertIn(gas_type, breakdown, f"{gas_type} should be in emissions breakdown")
            
            gas_data = breakdown[gas_type]
            self.assertIn("co2_emissions", gas_data, f"{gas_type} data should contain co2_emissions")
            
            # Verify the CO2 emissions match expected values
            gas_co2 = gas_data["co2_emissions"]
            logger.info(f"{gas_type} emissions: {gas_co2:.1f} kg CO2e (expected: {expected_co2:.1f})")
            
            # Allow for small rounding differences
            self.assertAlmostEqual(gas_co2, expected_co2, delta=1.0, 
                                  msg=f"{gas_type} emissions should be close to expected value")
            
            # Verify category is correct
            self.assertIn("category", gas_data, f"{gas_type} data should contain category")
            if gas_type in ["r134a_gas", "r600a_gas", "r410a_gas", "r32_gas"]:
                self.assertEqual(gas_data["category"], "refrigerant", 
                                f"{gas_type} should be categorized as refrigerant")
            elif gas_type in ["co2_fire", "fm200_fire"]:
                self.assertEqual(gas_data["category"], "fire_suppressant", 
                                f"{gas_type} should be categorized as fire_suppressant")
        
        # Verify total CO2 is high due to F-Gas emissions
        total_co2 = results["total_co2_emissions"]
        logger.info(f"Total CO2 emissions: {total_co2:.1f} kg CO2e")
        
        # The total should be high due to F-Gas emissions (around 24,000 kg CO2e)
        self.assertGreater(total_co2, 20000, "Total CO2 should be high due to F-Gas emissions")
        
        # Verify CO2 tonnes is correctly calculated
        co2_tonnes = results["total_co2_tonnes"]
        expected_tonnes = total_co2 / 1000.0
        self.assertAlmostEqual(co2_tonnes, expected_tonnes, places=3, 
                              msg="CO2 tonnes should be total CO2 / 1000")
        
        # Verify per-person CO2 is correctly calculated
        per_person_co2 = results["per_person_co2"]
        expected_per_person = total_co2 / self.f_gas_consumption_data["accommodation_count"]
        self.assertAlmostEqual(per_person_co2, expected_per_person, places=3, 
                              msg="Per-person CO2 should be total CO2 / accommodation_count")
        
        logger.info("✅ F-Gas carbon calculation test passed")
    
    def test_benchmark_with_f_gas(self):
        """Test benchmark performance with F-Gas emissions"""
        logger.info("\n=== Testing benchmark performance with F-Gas emissions ===")
        
        # Calculate carbon emissions with F-Gas values
        results = calculate_carbon_emissions(self.f_gas_consumption_data)
        total_co2 = results["total_co2_emissions"]
        accommodation_count = self.f_gas_consumption_data["accommodation_count"]
        
        # Calculate benchmark performance
        benchmark_result = benchmark_performance(total_co2, accommodation_count)
        logger.info(f"Benchmark result: {json.dumps(benchmark_result, indent=2)}")
        
        # Verify benchmark result structure
        self.assertIn("co2_per_room_night", benchmark_result, "Benchmark result should contain co2_per_room_night")
        self.assertIn("performance_level", benchmark_result, "Benchmark result should contain performance_level")
        self.assertIn("benchmarks", benchmark_result, "Benchmark result should contain benchmarks")
        
        # Verify CO2 per room night calculation
        co2_per_room_night = benchmark_result["co2_per_room_night"]
        expected_per_room_night = total_co2 / (accommodation_count * 30)  # 30 days default
        self.assertAlmostEqual(co2_per_room_night, expected_per_room_night, places=3, 
                              msg="CO2 per room night should be total CO2 / (accommodation_count * nights)")
        
        # With 100 accommodation count over 30 days (3000 room nights), the CO2 per room night
        # is actually quite low despite the high total CO2, so the performance level is "Excellent"
        performance_level = benchmark_result["performance_level"]
        logger.info(f"Performance level: {performance_level}")
        self.assertEqual(performance_level, "Excellent", 
                        "Performance level should be 'Excellent' with the current accommodation count")
        
        # Test with a much lower accommodation count to get "Poor" performance
        low_accommodation_benchmark = benchmark_performance(total_co2, 10)  # Only 10 rooms
        logger.info(f"Low accommodation benchmark: {json.dumps(low_accommodation_benchmark, indent=2)}")
        self.assertEqual(low_accommodation_benchmark["performance_level"], "Poor", 
                        "Performance level should be 'Poor' with low accommodation count")
        
        logger.info("✅ Benchmark performance with F-Gas emissions test passed")

def run_tests():
    """Run all F-Gas API tests"""
    logger.info("Starting F-Gas API tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(TestFGasAPI("test_f_gas_carbon_calculation"))
    suite.addTest(TestFGasAPI("test_benchmark_with_f_gas"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All F-Gas API tests PASSED")
        return True
    else:
        logger.error("Some F-Gas API tests FAILED")
        for error in result.errors:
            logger.error(f"Error: {error[1]}")
        for failure in result.failures:
            logger.error(f"Failure: {failure[1]}")
        return False

if __name__ == "__main__":
    run_tests()