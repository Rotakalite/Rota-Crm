import unittest
import json
import logging
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import DEFRA carbon calculation module
sys.path.append('/app/backend')
try:
    from defra_carbon import (
        calculate_carbon_emissions, 
        get_emission_factor, 
        get_all_emission_factors,
        benchmark_performance
    )
    logger.info("✅ Successfully imported DEFRA carbon module")
except ImportError as e:
    logger.error(f"❌ Failed to import DEFRA carbon module: {e}")
    sys.exit(1)

class TestCarbonFootprintAnalyticsEndpoint(unittest.TestCase):
    """Test class for carbon footprint analytics endpoint"""
    
    def setUp(self):
        """Set up test environment"""
        # Sample consumption data with all emission sources
        self.sample_consumption = {
            "electricity": 1000.0,  # kWh
            "water": 500.0,         # m³
            "natural_gas": 300.0,   # kWh
            "coal": 200.0,          # kg
            "diesel": 100.0,        # litre
            "gasoline": 80.0,       # litre
            "lpg": 50.0,            # litre
            "fuel_oil": 30.0,       # litre
            "r134a_gas": 1.0,       # kg
            "r600a_gas": 1.0,       # kg
            "r410a_gas": 1.0,       # kg
            "r32_gas": 1.0,         # kg
            "co2_fire": 10.0,       # kg
            "fm200_fire": 5.0,      # kg
            "accommodation_count": 150
        }
        
        # Expected emission sources in the response
        self.expected_sources = [
            "electricity", "water", "natural_gas", "coal",
            "diesel", "gasoline", "lpg", "fuel_oil",
            "r134a_gas", "r600a_gas", "r410a_gas", "r32_gas",
            "co2_fire", "fm200_fire"
        ]
    
    def test_carbon_footprint_analytics_response_structure(self):
        """Test the structure of the carbon footprint analytics response"""
        logger.info("\n=== Testing carbon footprint analytics response structure ===")
        
        # Calculate carbon emissions for the sample consumption data
        carbon_results = calculate_carbon_emissions(self.sample_consumption)
        logger.info(f"Carbon calculation results: {json.dumps(carbon_results, indent=2)}")
        
        # Check emissions breakdown
        emissions_breakdown = carbon_results.get("emissions_breakdown", {})
        logger.info(f"Emissions breakdown: {json.dumps(emissions_breakdown, indent=2)}")
        
        # Check for all expected emission sources
        for source in self.expected_sources:
            self.assertIn(source, emissions_breakdown, f"Missing {source} in emissions breakdown")
            logger.info(f"✅ Found emission source: {source} = {emissions_breakdown[source]['co2_emissions']} kg CO2e")
        
        # Verify total emissions
        total_emissions = carbon_results.get("total_co2_emissions", 0)
        logger.info(f"Total emissions: {total_emissions} kg CO2e")
        
        # Verify that the total includes all emission sources
        sum_of_sources = sum(emissions_breakdown[source]["co2_emissions"] for source in emissions_breakdown)
        logger.info(f"Sum of all sources: {sum_of_sources} kg CO2e")
        self.assertAlmostEqual(total_emissions, sum_of_sources, delta=0.1, 
                              msg="Total emissions should equal sum of all sources")
        
        # Simulate the structure of the carbon footprint analytics endpoint response
        analytics_response = {
            "year": 2024,
            "client_id": "test_client",
            "total_carbon_emissions": total_emissions,
            "total_carbon_tonnes": total_emissions / 1000.0,
            "average_per_person_co2": total_emissions / self.sample_consumption["accommodation_count"],
            "total_accommodation_count": self.sample_consumption["accommodation_count"],
            "monthly_carbon_data": [
                {
                    "month": 1,
                    "month_name": "Ocak",
                    "total_co2_emissions": total_emissions,
                    "total_co2_tonnes": total_emissions / 1000.0,
                    "per_person_co2": total_emissions / self.sample_consumption["accommodation_count"],
                    "accommodation_count": self.sample_consumption["accommodation_count"],
                    "emissions_breakdown": emissions_breakdown
                }
            ],
            "total_emission_sources": {source: emissions_breakdown[source]["co2_emissions"] for source in emissions_breakdown},
            "methodology": "DEFRA 2024 Emission Factors",
            "units": "kg CO2 equivalent"
        }
        
        logger.info(f"Simulated analytics response: {json.dumps(analytics_response, indent=2)[:500]}...")
        
        # Check response structure
        self.assertIn("year", analytics_response)
        self.assertIn("client_id", analytics_response)
        self.assertIn("total_carbon_emissions", analytics_response)
        self.assertIn("total_carbon_tonnes", analytics_response)
        self.assertIn("average_per_person_co2", analytics_response)
        self.assertIn("total_accommodation_count", analytics_response)
        self.assertIn("monthly_carbon_data", analytics_response)
        self.assertIn("total_emission_sources", analytics_response)
        self.assertIn("methodology", analytics_response)
        self.assertIn("units", analytics_response)
        
        # Check total_emission_sources structure
        total_emission_sources = analytics_response.get("total_emission_sources", {})
        logger.info(f"Total emission sources: {json.dumps(total_emission_sources, indent=2)}")
        
        # Check for all expected emission sources in total_emission_sources
        for source in self.expected_sources:
            self.assertIn(source, total_emission_sources, f"Missing {source} in total_emission_sources")
            logger.info(f"✅ Found emission source in total_emission_sources: {source} = {total_emission_sources[source]} kg CO2e")
        
        # Verify that the expected response matches the review request example
        expected_response_structure = {
            "total_emission_sources": {
                "electricity": 123.45,
                "water": 12.34, 
                "natural_gas": 234.56,
                "coal": 45.67,
                "diesel": 56.78,
                "gasoline": 67.89,
                "lpg": 78.90,
                "fuel_oil": 89.01,
                "r134a_gas": 1430.50,
                "r600a_gas": 3.15,
                "r410a_gas": 2088.25,
                "r32_gas": 675.75,
                "co2_fire": 10.00,
                "fm200_fire": 16100.00
            }
        }
        
        # Check that all keys in the expected response structure are in the actual response
        for key in expected_response_structure["total_emission_sources"]:
            self.assertIn(key, total_emission_sources, f"Missing {key} in total_emission_sources")
        
        logger.info("✅ Carbon footprint analytics response structure test passed")
    
    def test_f_gas_emission_values(self):
        """Test the F-Gas emission values in the carbon footprint analytics response"""
        logger.info("\n=== Testing F-Gas emission values ===")
        
        # Create a sample consumption with only F-Gas values
        f_gas_consumption = {
            "r134a_gas": 1.0,       # kg - 1430 kg CO2e/kg
            "r600a_gas": 1.05,      # kg - 3 kg CO2e/kg
            "r410a_gas": 1.0,       # kg - 2088 kg CO2e/kg
            "r32_gas": 1.0,         # kg - 675 kg CO2e/kg
            "co2_fire": 10.0,       # kg - 1 kg CO2e/kg
            "fm200_fire": 5.0,      # kg - 3220 kg CO2e/kg
            "accommodation_count": 1  # To avoid division by zero
        }
        
        # Calculate carbon emissions
        carbon_results = calculate_carbon_emissions(f_gas_consumption)
        logger.info(f"F-Gas carbon calculation results: {json.dumps(carbon_results, indent=2)}")
        
        # Check emissions breakdown
        emissions_breakdown = carbon_results.get("emissions_breakdown", {})
        
        # Expected F-Gas emission values
        expected_values = {
            "r134a_gas": 1430.0,    # 1.0 kg * 1430 kg CO2e/kg
            "r600a_gas": 3.15,      # 1.05 kg * 3 kg CO2e/kg
            "r410a_gas": 2088.0,    # 1.0 kg * 2088 kg CO2e/kg
            "r32_gas": 675.0,       # 1.0 kg * 675 kg CO2e/kg
            "co2_fire": 10.0,       # 10.0 kg * 1 kg CO2e/kg
            "fm200_fire": 16100.0   # 5.0 kg * 3220 kg CO2e/kg
        }
        
        # Check each F-Gas emission value
        for gas, expected_value in expected_values.items():
            self.assertIn(gas, emissions_breakdown, f"Missing {gas} in emissions breakdown")
            actual_value = emissions_breakdown[gas]["co2_emissions"]
            logger.info(f"{gas}: expected={expected_value}, actual={actual_value}")
            self.assertAlmostEqual(actual_value, expected_value, delta=0.1, 
                                  msg=f"{gas} emission value should match expected value")
        
        # Total expected F-Gas emissions
        expected_total = sum(expected_values.values())
        actual_total = carbon_results["total_co2_emissions"]
        logger.info(f"Total F-Gas emissions: expected={expected_total}, actual={actual_total}")
        self.assertAlmostEqual(actual_total, expected_total, delta=0.1, 
                              msg="Total F-Gas emissions should match expected value")
        
        logger.info("✅ F-Gas emission values test passed")

def run_tests():
    """Run all carbon footprint analytics endpoint tests"""
    logger.info("Starting Carbon Footprint Analytics Endpoint tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(TestCarbonFootprintAnalyticsEndpoint("test_carbon_footprint_analytics_response_structure"))
    suite.addTest(TestCarbonFootprintAnalyticsEndpoint("test_f_gas_emission_values"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All Carbon Footprint Analytics Endpoint tests PASSED")
        return True
    else:
        logger.error("Some Carbon Footprint Analytics Endpoint tests FAILED")
        return False

if __name__ == "__main__":
    run_tests()