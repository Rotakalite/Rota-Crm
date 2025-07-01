import unittest
import json
import logging
import requests
import os
import io
import uuid
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT token - this is a sample token for testing
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

class TestDEFRAFuelTypes(unittest.TestCase):
    """Test class for expanded consumption system with new DEFRA fuel types"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        
        # Generate unique test data to avoid conflicts
        self.test_month = datetime.now().month % 12 + 1  # Ensure it's 1-12
        self.test_year = datetime.now().year + 1  # Use next year to avoid conflicts
        
        # Test data with new DEFRA fuel types
        self.consumption_data = {
            "year": self.test_year,
            "month": self.test_month,
            "electricity": 1000.5,
            "water": 500.25,
            "natural_gas": 300.75,
            "coal": 200.0,
            "diesel": 150.5,        # New DEFRA fuel type
            "gasoline": 120.75,     # New DEFRA fuel type
            "lpg": 80.25,           # New DEFRA fuel type
            "fuel_oil": 90.5,       # New DEFRA fuel type
            "accommodation_count": 150,
            "client_id": "client1"  # This will be overridden in tests if needed
        }
    
    def test_post_consumption_with_defra_fuel_types(self):
        """Test POST /api/consumptions with new DEFRA fuel types"""
        logger.info("\n=== Testing POST /api/consumptions with new DEFRA fuel types ===")
        
        url = f"{self.api_url}/consumptions"
        
        try:
            # Make the POST request
            response = requests.post(url, headers=self.headers_admin, json=self.consumption_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            # Check if we get a 200 OK or 400 (if record already exists)
            self.assertIn(response.status_code, [200, 400])
            
            if response.status_code == 200:
                # Success case
                data = response.json()
                self.assertIn("message", data)
                self.assertIn("consumption_id", data)
                logger.info(f"✅ Successfully created consumption record with DEFRA fuel types: {data['consumption_id']}")
                
                # Store the consumption ID for later tests
                self.consumption_id = data["consumption_id"]
                
                # Test GET to verify the record was created with all fields
                self.test_get_consumption_with_defra_fuel_types(self.consumption_id)
                
                # Test PUT to update the record
                self.test_put_consumption_with_defra_fuel_types(self.consumption_id)
                
                # Clean up - delete the test record
                self.test_delete_consumption(self.consumption_id)
            elif response.status_code == 400:
                # Record might already exist
                data = response.json()
                self.assertIn("detail", data)
                logger.info(f"⚠️ Could not create new record: {data['detail']}")
                
                # Try to find an existing record to test with
                self.find_existing_consumption_record()
        except Exception as e:
            logger.error(f"❌ Error testing POST /api/consumptions: {str(e)}")
            raise
    
    def find_existing_consumption_record(self):
        """Find an existing consumption record to test with"""
        logger.info("\n=== Finding existing consumption record ===")
        
        url = f"{self.api_url}/consumptions"
        
        try:
            response = requests.get(url, headers=self.headers_admin)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            if data and len(data) > 0:
                # Use the first record for testing
                self.consumption_id = data[0]["id"]
                logger.info(f"✅ Found existing consumption record: {self.consumption_id}")
                
                # Test PUT to update the record
                self.test_put_consumption_with_defra_fuel_types(self.consumption_id)
            else:
                logger.warning("⚠️ No existing consumption records found")
        except Exception as e:
            logger.error(f"❌ Error finding existing consumption record: {str(e)}")
            raise
    
    def test_get_consumption_with_defra_fuel_types(self, consumption_id=None):
        """Test GET /api/consumptions returns new DEFRA fuel types"""
        logger.info("\n=== Testing GET /api/consumptions with new DEFRA fuel types ===")
        
        url = f"{self.api_url}/consumptions"
        
        try:
            # Make the GET request
            response = requests.get(url, headers=self.headers_admin)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if we get a 200 OK
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIsInstance(data, list)
            logger.info(f"Found {len(data)} consumption records")
            
            # If we're looking for a specific record
            if consumption_id:
                record = next((r for r in data if r["id"] == consumption_id), None)
                if record:
                    logger.info(f"✅ Found specific consumption record: {consumption_id}")
                    
                    # Verify all fields including new DEFRA fuel types
                    self.assertIn("electricity", record)
                    self.assertIn("water", record)
                    self.assertIn("natural_gas", record)
                    self.assertIn("coal", record)
                    
                    # Check new DEFRA fuel types
                    self.assertIn("diesel", record)
                    self.assertIn("gasoline", record)
                    self.assertIn("lpg", record)
                    self.assertIn("fuel_oil", record)
                    
                    logger.info("✅ Record contains all expected fields including new DEFRA fuel types")
                    
                    # Verify values match what we sent (if it's our test record)
                    if record["year"] == self.test_year and record["month"] == self.test_month:
                        self.assertEqual(record["diesel"], self.consumption_data["diesel"])
                        self.assertEqual(record["gasoline"], self.consumption_data["gasoline"])
                        self.assertEqual(record["lpg"], self.consumption_data["lpg"])
                        self.assertEqual(record["fuel_oil"], self.consumption_data["fuel_oil"])
                        logger.info("✅ DEFRA fuel type values match what we sent")
                else:
                    logger.warning(f"⚠️ Could not find consumption record with ID: {consumption_id}")
            else:
                # Check if any records have the new DEFRA fuel types
                defra_fields_present = False
                for record in data:
                    if all(field in record for field in ["diesel", "gasoline", "lpg", "fuel_oil"]):
                        defra_fields_present = True
                        logger.info(f"✅ Found record with DEFRA fuel types: {record['id']}")
                        break
                
                if not defra_fields_present and data:
                    logger.warning("⚠️ No records found with all DEFRA fuel types")
                    
                    # Check if records have at least some of the fields (backward compatibility)
                    if all(field in data[0] for field in ["electricity", "water", "natural_gas", "coal"]):
                        logger.info("✅ Records have basic consumption fields (backward compatibility)")
                    else:
                        logger.error("❌ Records missing basic consumption fields")
        except Exception as e:
            logger.error(f"❌ Error testing GET /api/consumptions: {str(e)}")
            raise
    
    def test_put_consumption_with_defra_fuel_types(self, consumption_id):
        """Test PUT /api/consumptions/{consumption_id} updates new DEFRA fuel types"""
        logger.info(f"\n=== Testing PUT /api/consumptions/{consumption_id} with new DEFRA fuel types ===")
        
        url = f"{self.api_url}/consumptions/{consumption_id}"
        
        # Create updated data with different values for DEFRA fuel types
        updated_data = {
            "year": self.test_year,
            "month": self.test_month,
            "electricity": 1100.5,
            "water": 550.25,
            "natural_gas": 330.75,
            "coal": 220.0,
            "diesel": 165.5,        # Updated DEFRA fuel type
            "gasoline": 135.75,     # Updated DEFRA fuel type
            "lpg": 95.25,           # Updated DEFRA fuel type
            "fuel_oil": 105.5,      # Updated DEFRA fuel type
            "accommodation_count": 160
        }
        
        try:
            # Make the PUT request
            response = requests.put(url, headers=self.headers_admin, json=updated_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            # Check if we get a 200 OK
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn("message", data)
            logger.info(f"✅ Successfully updated consumption record: {data['message']}")
            
            # Verify the update by getting the record
            self.verify_consumption_update(consumption_id, updated_data)
        except Exception as e:
            logger.error(f"❌ Error testing PUT /api/consumptions/{consumption_id}: {str(e)}")
            raise
    
    def verify_consumption_update(self, consumption_id, updated_data):
        """Verify that the consumption record was updated correctly"""
        logger.info(f"\n=== Verifying update of consumption record {consumption_id} ===")
        
        url = f"{self.api_url}/consumptions"
        
        try:
            # Make the GET request
            response = requests.get(url, headers=self.headers_admin)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            record = next((r for r in data if r["id"] == consumption_id), None)
            
            if record:
                logger.info(f"✅ Found updated consumption record: {consumption_id}")
                
                # Verify updated values for DEFRA fuel types
                self.assertEqual(record["diesel"], updated_data["diesel"])
                self.assertEqual(record["gasoline"], updated_data["gasoline"])
                self.assertEqual(record["lpg"], updated_data["lpg"])
                self.assertEqual(record["fuel_oil"], updated_data["fuel_oil"])
                
                logger.info("✅ DEFRA fuel type values were updated correctly")
            else:
                logger.warning(f"⚠️ Could not find updated consumption record with ID: {consumption_id}")
        except Exception as e:
            logger.error(f"❌ Error verifying consumption update: {str(e)}")
            raise
    
    def test_delete_consumption(self, consumption_id):
        """Delete the test consumption record"""
        logger.info(f"\n=== Deleting test consumption record {consumption_id} ===")
        
        url = f"{self.api_url}/consumptions/{consumption_id}"
        
        try:
            # Make the DELETE request
            response = requests.delete(url, headers=self.headers_admin)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if we get a 200 OK
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn("message", data)
            logger.info(f"✅ Successfully deleted consumption record: {data['message']}")
        except Exception as e:
            logger.error(f"❌ Error deleting consumption record: {str(e)}")
            # Don't raise here, as this is just cleanup
    
    def test_backward_compatibility(self):
        """Test backward compatibility with old consumption records"""
        logger.info("\n=== Testing backward compatibility with old consumption records ===")
        
        url = f"{self.api_url}/consumptions"
        
        # Create a consumption record without the new DEFRA fuel types
        old_format_data = {
            "year": self.test_year,
            "month": (self.test_month % 12) + 1,  # Use a different month
            "electricity": 1000.5,
            "water": 500.25,
            "natural_gas": 300.75,
            "coal": 200.0,
            "accommodation_count": 150,
            "client_id": "client1"
        }
        
        try:
            # Make the POST request
            response = requests.post(url, headers=self.headers_admin, json=old_format_data)
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if we get a 200 OK or 400 (if record already exists)
            self.assertIn(response.status_code, [200, 400])
            
            if response.status_code == 200:
                # Success case
                data = response.json()
                self.assertIn("consumption_id", data)
                old_record_id = data["consumption_id"]
                logger.info(f"✅ Successfully created old-format consumption record: {old_record_id}")
                
                # Get the record to verify
                get_response = requests.get(url, headers=self.headers_admin)
                self.assertEqual(get_response.status_code, 200)
                
                get_data = get_response.json()
                old_record = next((r for r in get_data if r["id"] == old_record_id), None)
                
                if old_record:
                    logger.info(f"✅ Found old-format consumption record: {old_record_id}")
                    
                    # Verify it has the basic fields
                    self.assertIn("electricity", old_record)
                    self.assertIn("water", old_record)
                    self.assertIn("natural_gas", old_record)
                    self.assertIn("coal", old_record)
                    
                    # Verify it has the new DEFRA fields with default values
                    self.assertIn("diesel", old_record)
                    self.assertIn("gasoline", old_record)
                    self.assertIn("lpg", old_record)
                    self.assertIn("fuel_oil", old_record)
                    
                    # Check that the new fields have default values (0.0)
                    self.assertEqual(old_record["diesel"], 0.0)
                    self.assertEqual(old_record["gasoline"], 0.0)
                    self.assertEqual(old_record["lpg"], 0.0)
                    self.assertEqual(old_record["fuel_oil"], 0.0)
                    
                    logger.info("✅ Old-format record has new DEFRA fields with default values")
                    
                    # Clean up
                    self.test_delete_consumption(old_record_id)
                else:
                    logger.warning(f"⚠️ Could not find old-format consumption record with ID: {old_record_id}")
            elif response.status_code == 400:
                # Record might already exist
                data = response.json()
                logger.info(f"⚠️ Could not create old-format record: {data['detail']}")
                
                # Test with existing records instead
                self.test_get_consumption_with_defra_fuel_types()
        except Exception as e:
            logger.error(f"❌ Error testing backward compatibility: {str(e)}")
            raise

def run_defra_fuel_types_tests():
    """Run tests for expanded consumption system with new DEFRA fuel types"""
    logger.info("Starting DEFRA fuel types tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add tests
    suite.addTest(TestDEFRAFuelTypes("test_post_consumption_with_defra_fuel_types"))
    suite.addTest(TestDEFRAFuelTypes("test_get_consumption_with_defra_fuel_types"))
    suite.addTest(TestDEFRAFuelTypes("test_backward_compatibility"))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Summary
    logger.info("\n=== DEFRA Fuel Types Test Summary ===")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        logger.info("All DEFRA fuel types tests PASSED")
        return True
    else:
        logger.error("Some DEFRA fuel types tests FAILED")
        return False

if __name__ == "__main__":
    run_defra_fuel_types_tests()