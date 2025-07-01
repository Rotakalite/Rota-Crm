import unittest
import sys
import os
import logging
from datetime import datetime

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

class TestDEFRACarbonCalculation(unittest.TestCase):
    """Test class for DEFRA carbon calculation module"""
    
    def setUp(self):
        """Set up test environment"""
        # Test consumption data with all DEFRA fuel types
        self.test_consumption = {
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
        
        # Test consumption data with F-Gas values from the review request
        self.f_gas_consumption = {
            "electricity": 1000.0,  # kWh
            "water": 500.0,         # m³
            "natural_gas": 300.0,   # kWh
            "coal": 200.0,          # kg
            "diesel": 100.0,        # litre
            "gasoline": 50.0,       # litre
            "lpg": 25.0,            # litre
            "fuel_oil": 75.0,       # litre
            # F-Gas values from the review request
            "r134a_gas": 1.5,      # kg (Klima gazı - 1430 kg CO2e/kg)
            "r600a_gas": 0.5,      # kg (Buzdolabı gazı - 3 kg CO2e/kg)
            "r410a_gas": 2.0,      # kg (Modern AC - 2088 kg CO2e/kg)
            "r32_gas": 1.0,        # kg (Yeni nesil AC - 675 kg CO2e/kg)
            "co2_fire": 10.0,      # kg (CO2 söndürücü - 1 kg CO2/kg)
            "fm200_fire": 5.0,     # kg (FM200 söndürücü - 3220 kg CO2e/kg)
            "accommodation_count": 100
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
            "fuel_oil": 2.54,        # kg CO2/litre
            # F-Gas emission factors
            "r134a_gas": 1430.0,     # kg CO2e/kg
            "r600a_gas": 3.0,        # kg CO2e/kg
            "r410a_gas": 2088.0,     # kg CO2e/kg
            "r32_gas": 675.0,        # kg CO2e/kg
            "co2_fire": 1.0,         # kg CO2e/kg
            "fm200_fire": 3220.0     # kg CO2e/kg
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
    
    def test_emission_factors(self):
        """Test that emission factors match DEFRA 2024 values"""
        logger.info("\n=== Testing DEFRA 2024 emission factors ===")
        
        # Get all emission factors
        all_factors = get_all_emission_factors()
        logger.info(f"Found {len(all_factors)} emission factors")
        
        # Check each expected factor
        for fuel_type, expected_factor in self.expected_factors.items():
            logger.info(f"Checking {fuel_type} emission factor...")
            
            # Get factor from module
            factor_data = get_emission_factor(fuel_type)
            self.assertIsNotNone(factor_data, f"Emission factor for {fuel_type} not found")
            
            # Check factor value
            actual_factor = factor_data["factor"]
            logger.info(f"{fuel_type}: expected={expected_factor}, actual={actual_factor}")
            
            # Check within 0.001% margin (essentially exact match)
            percent_diff = abs(actual_factor - expected_factor) / expected_factor * 100
            self.assertLessEqual(percent_diff, 0.001, 
                               f"{fuel_type} emission factor should match DEFRA 2024 value")
        
        logger.info("✅ All emission factors match DEFRA 2024 values")
    
    def test_carbon_calculation(self):
        """Test carbon calculation using DEFRA factors"""
        logger.info("\n=== Testing carbon calculation ===")
        
        # Calculate carbon emissions
        results = calculate_carbon_emissions(self.test_consumption)
        logger.info(f"Carbon calculation results: {results}")
        
        # Check total CO2 emissions
        calculated_co2 = results["total_co2_emissions"]
        logger.info(f"Expected CO2: {self.expected_co2:.3f} kg, Calculated CO2: {calculated_co2:.3f} kg")
        
        # Calculate percentage difference
        percent_diff = abs(calculated_co2 - self.expected_co2) / self.expected_co2 * 100
        logger.info(f"Percentage difference: {percent_diff:.6f}%")
        self.assertLessEqual(percent_diff, 0.001, "Carbon calculation should match expected value")
        
        # Check tonnes conversion
        tonnes = results["total_co2_tonnes"]
        expected_tonnes = self.expected_co2 / 1000.0
        logger.info(f"Expected tonnes: {expected_tonnes:.6f}, Calculated tonnes: {tonnes:.6f}")
        self.assertAlmostEqual(tonnes, expected_tonnes, places=6)
        
        # Check per-person calculation
        per_person = results["per_person_co2"]
        expected_per_person = self.expected_co2 / self.test_consumption["accommodation_count"]
        logger.info(f"Expected per person: {expected_per_person:.3f}, Calculated per person: {per_person:.3f}")
        self.assertAlmostEqual(per_person, expected_per_person, places=3)
        
        # Check emissions breakdown
        breakdown = results["emissions_breakdown"]
        self.assertEqual(len(breakdown), 8, "Should have 8 fuel types in breakdown")
        
        for fuel_type, emission_data in breakdown.items():
            self.assertIn("emission_factor", emission_data)
            self.assertIn("co2_emissions", emission_data)
            self.assertIn("consumption", emission_data)
            
            # Check emission factor matches expected
            if fuel_type in self.expected_factors:
                expected_factor = self.expected_factors[fuel_type]
                actual_factor = emission_data["emission_factor"]
                self.assertAlmostEqual(actual_factor, expected_factor, places=5)
        
        logger.info("✅ Carbon calculation test passed")
    
    def test_benchmark_performance(self):
        """Test carbon benchmarking against hotel industry standards"""
        logger.info("\n=== Testing carbon benchmarking ===")
        
        # Calculate carbon emissions first
        results = calculate_carbon_emissions(self.test_consumption)
        total_co2 = results["total_co2_emissions"]
        accommodation_count = self.test_consumption["accommodation_count"]
        
        # Test benchmarking with different CO2 values to get different performance levels
        test_cases = [
            # Very low emissions - should be "Excellent"
            {"co2": 50000, "accommodation": 150, "expected": "Excellent"},
            # Low emissions - should be "Good"
            {"co2": 100000, "accommodation": 150, "expected": "Good"},
            # Medium emissions - should be "Average"
            {"co2": 150000, "accommodation": 150, "expected": "Average"},
            # High emissions - should be "Poor"
            {"co2": 300000, "accommodation": 150, "expected": "Poor"}
        ]
        
        for i, test_case in enumerate(test_cases):
            logger.info(f"Test case {i+1}: CO2={test_case['co2']}, Accommodation={test_case['accommodation']}")
            
            benchmark = benchmark_performance(
                test_case["co2"],
                test_case["accommodation"]
            )
            
            logger.info(f"Benchmark result: {benchmark}")
            
            # Check performance level
            self.assertEqual(benchmark["performance_level"], test_case["expected"],
                           f"Performance level should be {test_case['expected']}")
            
            # Check CO2 per room night calculation
            expected_per_room_night = test_case["co2"] / (test_case["accommodation"] * 30)  # 30 days default
            self.assertAlmostEqual(benchmark["co2_per_room_night"], expected_per_room_night, places=3)
            
            # Check benchmarks are present
            self.assertIn("benchmarks", benchmark)
            self.assertIn("hotel_industry_average", benchmark["benchmarks"])
            self.assertIn("sustainable_target", benchmark["benchmarks"])
            self.assertIn("excellent_performance", benchmark["benchmarks"])
        
        logger.info("✅ Carbon benchmarking test passed")
    
    def test_validation(self):
        """Test consumption data validation"""
        logger.info("\n=== Testing consumption data validation ===")
        
        # Valid data
        valid, errors = validate_consumption_data(self.test_consumption)
        logger.info(f"Valid data test: valid={valid}, errors={errors}")
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)
        
        # Invalid data - negative values
        invalid_data = self.test_consumption.copy()
        invalid_data["electricity"] = -100
        valid, errors = validate_consumption_data(invalid_data)
        logger.info(f"Negative value test: valid={valid}, errors={errors}")
        self.assertFalse(valid)
        self.assertGreater(len(errors), 0)
        
        # Invalid data - non-numeric values
        invalid_data = self.test_consumption.copy()
        invalid_data["water"] = "not a number"
        valid, errors = validate_consumption_data(invalid_data)
        logger.info(f"Non-numeric value test: valid={valid}, errors={errors}")
        self.assertFalse(valid)
        self.assertGreater(len(errors), 0)
        
        logger.info("✅ Validation test passed")

def run_tests():
    """Run all DEFRA carbon calculation tests"""
    logger.info("Starting DEFRA Carbon Calculation tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(TestDEFRACarbonCalculation("test_emission_factors"))
    suite.addTest(TestDEFRACarbonCalculation("test_carbon_calculation"))
    suite.addTest(TestDEFRACarbonCalculation("test_benchmark_performance"))
    suite.addTest(TestDEFRACarbonCalculation("test_validation"))
    
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