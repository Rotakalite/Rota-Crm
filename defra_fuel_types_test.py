import unittest
import json
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data

class TestDEFRAFuelTypes(unittest.TestCase):
    """Test class for expanded consumption system with new DEFRA fuel types"""
    
    def setUp(self):
        """Set up test environment"""
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
        
        # Sample consumption record with DEFRA fuel types
        self.sample_consumption = {
            "id": "test_consumption_id",
            "client_id": "client1",
            "year": self.test_year,
            "month": self.test_month,
            "electricity": 1000.5,
            "water": 500.25,
            "natural_gas": 300.75,
            "coal": 200.0,
            "diesel": 150.5,
            "gasoline": 120.75,
            "lpg": 80.25,
            "fuel_oil": 90.5,
            "accommodation_count": 150,
            "created_at": "2025-07-01T12:00:00.000Z",
            "updated_at": "2025-07-01T12:00:00.000Z"
        }
        
        # Sample consumption record without DEFRA fuel types (for backward compatibility)
        self.old_format_consumption = {
            "id": "old_format_id",
            "client_id": "client1",
            "year": self.test_year,
            "month": (self.test_month % 12) + 1,
            "electricity": 1000.5,
            "water": 500.25,
            "natural_gas": 300.75,
            "coal": 200.0,
            "accommodation_count": 150,
            "created_at": "2025-07-01T12:00:00.000Z",
            "updated_at": "2025-07-01T12:00:00.000Z",
            "diesel": 0.0,
            "gasoline": 0.0,
            "lpg": 0.0,
            "fuel_oil": 0.0
        }
    
    @patch('requests.post')
    def test_post_consumption_with_defra_fuel_types(self, mock_post):
        """Test POST /api/consumptions with new DEFRA fuel types"""
        logger.info("\n=== Testing POST /api/consumptions with new DEFRA fuel types ===")
        
        # Mock the response
        mock_post.return_value = MockResponse({
            "message": "Tüketim verisi başarıyla kaydedildi",
            "consumption_id": "test_consumption_id"
        }, 200)
        
        # Test the POST endpoint
        from requests import post
        response = post("https://example.com/api/consumptions", json=self.consumption_data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("consumption_id", data)
        
        # Verify the request
        args, kwargs = mock_post.call_args
        sent_data = kwargs.get('json', {})
        
        # Check that all DEFRA fuel types were included in the request
        self.assertIn("diesel", sent_data)
        self.assertIn("gasoline", sent_data)
        self.assertIn("lpg", sent_data)
        self.assertIn("fuel_oil", sent_data)
        
        # Check the values
        self.assertEqual(sent_data["diesel"], self.consumption_data["diesel"])
        self.assertEqual(sent_data["gasoline"], self.consumption_data["gasoline"])
        self.assertEqual(sent_data["lpg"], self.consumption_data["lpg"])
        self.assertEqual(sent_data["fuel_oil"], self.consumption_data["fuel_oil"])
        
        logger.info("✅ POST /api/consumptions correctly includes new DEFRA fuel types")
    
    @patch('requests.get')
    def test_get_consumption_with_defra_fuel_types(self, mock_get):
        """Test GET /api/consumptions returns new DEFRA fuel types"""
        logger.info("\n=== Testing GET /api/consumptions with new DEFRA fuel types ===")
        
        # Mock the response with a consumption record that includes DEFRA fuel types
        mock_get.return_value = MockResponse([self.sample_consumption], 200)
        
        # Test the GET endpoint
        from requests import get
        response = get("https://example.com/api/consumptions")
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        
        # Check the first record
        record = data[0]
        
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
        
        # Verify values match what we expect
        self.assertEqual(record["diesel"], self.sample_consumption["diesel"])
        self.assertEqual(record["gasoline"], self.sample_consumption["gasoline"])
        self.assertEqual(record["lpg"], self.sample_consumption["lpg"])
        self.assertEqual(record["fuel_oil"], self.sample_consumption["fuel_oil"])
        
        logger.info("✅ GET /api/consumptions correctly returns new DEFRA fuel types")
    
    @patch('requests.put')
    def test_put_consumption_with_defra_fuel_types(self, mock_put):
        """Test PUT /api/consumptions/{consumption_id} updates new DEFRA fuel types"""
        logger.info("\n=== Testing PUT /api/consumptions/{consumption_id} with new DEFRA fuel types ===")
        
        # Mock the response
        mock_put.return_value = MockResponse({
            "message": "Tüketim verisi başarıyla güncellendi"
        }, 200)
        
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
        
        # Test the PUT endpoint
        from requests import put
        response = put("https://example.com/api/consumptions/test_consumption_id", json=updated_data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        
        # Verify the request
        args, kwargs = mock_put.call_args
        sent_data = kwargs.get('json', {})
        
        # Check that all DEFRA fuel types were included in the request
        self.assertIn("diesel", sent_data)
        self.assertIn("gasoline", sent_data)
        self.assertIn("lpg", sent_data)
        self.assertIn("fuel_oil", sent_data)
        
        # Check the values
        self.assertEqual(sent_data["diesel"], updated_data["diesel"])
        self.assertEqual(sent_data["gasoline"], updated_data["gasoline"])
        self.assertEqual(sent_data["lpg"], updated_data["lpg"])
        self.assertEqual(sent_data["fuel_oil"], updated_data["fuel_oil"])
        
        logger.info("✅ PUT /api/consumptions/{consumption_id} correctly updates new DEFRA fuel types")
    
    @patch('requests.post')
    @patch('requests.get')
    def test_backward_compatibility(self, mock_get, mock_post):
        """Test backward compatibility with old consumption records"""
        logger.info("\n=== Testing backward compatibility with old consumption records ===")
        
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
        
        # Mock the POST response
        mock_post.return_value = MockResponse({
            "message": "Tüketim verisi başarıyla kaydedildi",
            "consumption_id": "old_format_id"
        }, 200)
        
        # Test the POST endpoint with old format data
        from requests import post
        response = post("https://example.com/api/consumptions", json=old_format_data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("consumption_id", data)
        
        # Mock the GET response with the old format record that has default values for DEFRA fields
        mock_get.return_value = MockResponse([self.old_format_consumption], 200)
        
        # Test the GET endpoint
        from requests import get
        response = get("https://example.com/api/consumptions")
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        
        # Check the record
        record = data[0]
        
        # Verify it has the basic fields
        self.assertIn("electricity", record)
        self.assertIn("water", record)
        self.assertIn("natural_gas", record)
        self.assertIn("coal", record)
        
        # Verify it has the new DEFRA fields with default values
        self.assertIn("diesel", record)
        self.assertIn("gasoline", record)
        self.assertIn("lpg", record)
        self.assertIn("fuel_oil", record)
        
        # Check that the new fields have default values (0.0)
        self.assertEqual(record["diesel"], 0.0)
        self.assertEqual(record["gasoline"], 0.0)
        self.assertEqual(record["lpg"], 0.0)
        self.assertEqual(record["fuel_oil"], 0.0)
        
        logger.info("✅ Old-format record has new DEFRA fields with default values")
        
        # Verify the POST request
        args, kwargs = mock_post.call_args
        sent_data = kwargs.get('json', {})
        
        # Check that old format data doesn't include DEFRA fuel types
        self.assertNotIn("diesel", sent_data)
        self.assertNotIn("gasoline", sent_data)
        self.assertNotIn("lpg", sent_data)
        self.assertNotIn("fuel_oil", sent_data)
        
        logger.info("✅ Backward compatibility test passed")

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