import unittest
import json
import logging
import sys
import os
from datetime import datetime

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

class TestDEFRAFGasCarbon(unittest.TestCase):
    """Test class for DEFRA F-Gas carbon calculation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # F-Gas test data with values from the review request
        self.f_gas_consumption_data = {
            "year": 2024,
            "month": 6,
            "client_id": "KAYA_CLIENT_001",
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
        
        # Expected total CO2 including regular consumption (rough estimate)
        # Regular consumption: ~1,500 kg CO2e
        # F-Gases: ~23,107.5 kg CO2e
        # Total: ~24,607.5 kg CO2e
        self.expected_total_co2 = 24500  # Approximate value for validation
    
    def test_emission_factors(self):
        """Test that emission factors match the expected values"""
        logger.info("\n=== Testing DEFRA F-Gas emission factors ===")
        
        # Test F-Gas emission factors
        r134a_factor = DEFRA_EMISSION_FACTORS["r134a_gas"]["factor"]
        self.assertAlmostEqual(r134a_factor, 1430.0, places=1, 
                              msg="R134a emission factor should be 1430 kg CO2e/kg")
        logger.info(f"✅ R134a emission factor: {r134a_factor} kg CO2e/kg")
        
        r600a_factor = DEFRA_EMISSION_FACTORS["r600a_gas"]["factor"]
        self.assertAlmostEqual(r600a_factor, 3.0, places=1, 
                              msg="R600a emission factor should be 3 kg CO2e/kg")
        logger.info(f"✅ R600a emission factor: {r600a_factor} kg CO2e/kg")
        
        r410a_factor = DEFRA_EMISSION_FACTORS["r410a_gas"]["factor"]
        self.assertAlmostEqual(r410a_factor, 2088.0, places=1, 
                              msg="R410a emission factor should be 2088 kg CO2e/kg")
        logger.info(f"✅ R410a emission factor: {r410a_factor} kg CO2e/kg")
        
        r32_factor = DEFRA_EMISSION_FACTORS["r32_gas"]["factor"]
        self.assertAlmostEqual(r32_factor, 675.0, places=1, 
                              msg="R32 emission factor should be 675 kg CO2e/kg")
        logger.info(f"✅ R32 emission factor: {r32_factor} kg CO2e/kg")
        
        co2_fire_factor = DEFRA_EMISSION_FACTORS["co2_fire"]["factor"]
        self.assertAlmostEqual(co2_fire_factor, 1.0, places=1, 
                              msg="CO2 fire extinguisher emission factor should be 1 kg CO2e/kg")
        logger.info(f"✅ CO2 fire extinguisher emission factor: {co2_fire_factor} kg CO2e/kg")
        
        fm200_fire_factor = DEFRA_EMISSION_FACTORS["fm200_fire"]["factor"]
        self.assertAlmostEqual(fm200_fire_factor, 3220.0, places=1, 
                              msg="FM200 fire suppressant emission factor should be 3220 kg CO2e/kg")
        logger.info(f"✅ FM200 fire suppressant emission factor: {fm200_fire_factor} kg CO2e/kg")
        
        logger.info("✅ All F-Gas emission factors match expected values")
    
    def test_carbon_calculation_with_f_gas(self):
        """Test carbon calculation with F-Gas values"""
        logger.info("\n=== Testing carbon calculation with F-Gas values ===")
        
        # Calculate carbon emissions
        carbon_results = calculate_carbon_emissions(self.f_gas_consumption_data)
        
        # Print the results for debugging
        logger.info(f"Carbon calculation results: {json.dumps(carbon_results, indent=2)}")
        
        # Verify total CO2 emissions
        total_co2 = carbon_results["total_co2_emissions"]
        logger.info(f"Total CO2 emissions: {total_co2} kg CO2e")
        
        # The total should be high due to F-Gas emissions (around 24,000 kg CO2e)
        self.assertGreater(total_co2, 20000, "Total CO2 should be high due to F-Gas emissions")
        
        # Verify CO2 tonnes is correctly calculated
        co2_tonnes = carbon_results["total_co2_tonnes"]
        expected_tonnes = total_co2 / 1000.0
        self.assertAlmostEqual(co2_tonnes, expected_tonnes, places=3, 
                              msg="CO2 tonnes should be total CO2 / 1000")
        
        # Verify per-person CO2 is correctly calculated
        per_person_co2 = carbon_results["per_person_co2"]
        expected_per_person = total_co2 / self.f_gas_consumption_data["accommodation_count"]
        self.assertAlmostEqual(per_person_co2, expected_per_person, places=3, 
                              msg="Per-person CO2 should be total CO2 / accommodation_count")
        
        # Verify emissions breakdown includes F-Gas emissions
        emissions_breakdown = carbon_results["emissions_breakdown"]
        
        # Check each F-Gas emission
        for gas_type in ["r134a_gas", "r600a_gas", "r410a_gas", "r32_gas", "co2_fire", "fm200_fire"]:
            self.assertIn(gas_type, emissions_breakdown, f"{gas_type} should be in emissions breakdown")
            
            gas_data = emissions_breakdown[gas_type]
            self.assertIn("co2_emissions", gas_data, f"{gas_type} data should contain co2_emissions")
            
            # Verify the CO2 emissions match expected values
            gas_co2 = gas_data["co2_emissions"]
            expected_co2 = self.expected_f_gas_emissions[gas_type]
            logger.info(f"{gas_type} emissions: {gas_co2} kg CO2e (expected: {expected_co2})")
            
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
        
        logger.info("✅ Carbon calculation with F-Gas values test passed")
    
    def test_consumption_model_structure(self):
        """Test that the Consumption model includes F-Gas fields"""
        logger.info("\n=== Testing Consumption model structure ===")
        
        # Import the Consumption model from backend/server.py
        try:
            from server import Consumption, ConsumptionInput
            logger.info("✅ Successfully imported Consumption models")
            
            # Check that Consumption model includes F-Gas fields
            consumption = Consumption(
                id="test_id",
                client_id="test_client_id",
                year=2024,
                month=6,
                electricity=1000.0,
                water=500.0,
                natural_gas=300.0,
                coal=200.0,
                r134a_gas=1.5,
                r600a_gas=0.5,
                r410a_gas=2.0,
                r32_gas=1.0,
                co2_fire=10.0,
                fm200_fire=5.0,
                accommodation_count=100
            )
            
            # Verify F-Gas fields exist in the model
            self.assertEqual(consumption.r134a_gas, 1.5, "r134a_gas field should exist in Consumption model")
            self.assertEqual(consumption.r600a_gas, 0.5, "r600a_gas field should exist in Consumption model")
            self.assertEqual(consumption.r410a_gas, 2.0, "r410a_gas field should exist in Consumption model")
            self.assertEqual(consumption.r32_gas, 1.0, "r32_gas field should exist in Consumption model")
            self.assertEqual(consumption.co2_fire, 10.0, "co2_fire field should exist in Consumption model")
            self.assertEqual(consumption.fm200_fire, 5.0, "fm200_fire field should exist in Consumption model")
            
            # Check that ConsumptionInput model includes F-Gas fields
            consumption_input = ConsumptionInput(
                year=2024,
                month=6,
                electricity=1000.0,
                water=500.0,
                natural_gas=300.0,
                coal=200.0,
                r134a_gas=1.5,
                r600a_gas=0.5,
                r410a_gas=2.0,
                r32_gas=1.0,
                co2_fire=10.0,
                fm200_fire=5.0,
                accommodation_count=100
            )
            
            # Verify F-Gas fields exist in the model
            self.assertEqual(consumption_input.r134a_gas, 1.5, "r134a_gas field should exist in ConsumptionInput model")
            self.assertEqual(consumption_input.r600a_gas, 0.5, "r600a_gas field should exist in ConsumptionInput model")
            self.assertEqual(consumption_input.r410a_gas, 2.0, "r410a_gas field should exist in ConsumptionInput model")
            self.assertEqual(consumption_input.r32_gas, 1.0, "r32_gas field should exist in ConsumptionInput model")
            self.assertEqual(consumption_input.co2_fire, 10.0, "co2_fire field should exist in ConsumptionInput model")
            self.assertEqual(consumption_input.fm200_fire, 5.0, "fm200_fire field should exist in ConsumptionInput model")
            
            logger.info("✅ Consumption models include F-Gas fields")
        except ImportError as e:
            logger.error(f"❌ Failed to import Consumption models: {e}")
            self.skipTest("Could not import Consumption models")
        except Exception as e:
            logger.error(f"❌ Error testing Consumption model structure: {e}")
            raise

def run_tests():
    """Run all DEFRA F-Gas tests"""
    logger.info("Starting DEFRA F-Gas tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(TestDEFRAFGasCarbon("test_emission_factors"))
    suite.addTest(TestDEFRAFGasCarbon("test_carbon_calculation_with_f_gas"))
    suite.addTest(TestDEFRAFGasCarbon("test_consumption_model_structure"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All DEFRA F-Gas tests PASSED")
        return True
    else:
        logger.error("Some DEFRA F-Gas tests FAILED")
        for error in result.errors:
            logger.error(f"Error: {error[1]}")
        for failure in result.failures:
            logger.error(f"Failure: {failure[1]}")
        return False

if __name__ == "__main__":
    run_tests()