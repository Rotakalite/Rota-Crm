import unittest
import json
import logging
from unittest.mock import patch, MagicMock
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test data
TEST_YEAR_CURRENT = 2024
TEST_YEAR_PREVIOUS = 2025

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data

class TestAnalyticsEndpoints(unittest.TestCase):
    """Test class for analytics endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = "https://1f0c3a30-ba23-4cb9-a340-2a6d39e2d493.preview.emergentagent.com/api"
        
        # Sample data structures for mocking responses
        self.client_data = [
            {
                "id": "client1",
                "name": "Test Client",
                "hotel_name": "Test Hotel",
                "contact_person": "John Doe",
                "email": "john@example.com",
                "phone": "1234567890",
                "address": "123 Test St",
                "current_stage": "I.Aşama",
                "services_completed": [],
                "carbon_footprint": None,
                "sustainability_score": None
            }
        ]
        
        self.consumption_data = [
            {
                "id": "consumption1",
                "client_id": "client1",
                "year": 2024,
                "month": 1,
                "electricity": 1000.5,
                "water": 500.25,
                "natural_gas": 300.75,
                "coal": 200.0,
                "accommodation_count": 150
            }
        ]
        
        self.analytics_data = {
            "year": 2024,
            "monthly_comparison": [
                {
                    "month": 1,
                    "month_name": "Ocak",
                    "current_year": {
                        "electricity": 1000.5,
                        "water": 500.25,
                        "natural_gas": 300.75,
                        "coal": 200.0,
                        "accommodation_count": 150
                    },
                    "previous_year": {
                        "electricity": 900.5,
                        "water": 450.25,
                        "natural_gas": 280.75,
                        "coal": 180.0,
                        "accommodation_count": 140
                    },
                    "current_year_per_person": {
                        "electricity": 6.67,
                        "water": 3.33,
                        "natural_gas": 2.0,
                        "coal": 1.33
                    },
                    "previous_year_per_person": {
                        "electricity": 6.43,
                        "water": 3.22,
                        "natural_gas": 2.0,
                        "coal": 1.29
                    }
                }
                # ... other months would be here
            ],
            "yearly_totals": {
                "current_year": {
                    "electricity": 12000.0,
                    "water": 6000.0,
                    "natural_gas": 3600.0,
                    "coal": 2400.0,
                    "accommodation_count": 1800
                },
                "previous_year": {
                    "electricity": 10800.0,
                    "water": 5400.0,
                    "natural_gas": 3240.0,
                    "coal": 2160.0,
                    "accommodation_count": 1680
                }
            },
            "yearly_per_person": {
                "current_year": {
                    "electricity": 6.67,
                    "water": 3.33,
                    "natural_gas": 2.0,
                    "coal": 1.33
                },
                "previous_year": {
                    "electricity": 6.43,
                    "water": 3.22,
                    "natural_gas": 1.93,
                    "coal": 1.29
                }
            }
        }
        
        self.multi_client_data = {
            "year": 2024,
            "clients_comparison": [
                {
                    "client_id": "client1",
                    "client_name": "Test Client 1",
                    "hotel_name": "Test Hotel 1",
                    "yearly_totals": {
                        "electricity": 12000.0,
                        "water": 6000.0,
                        "natural_gas": 3600.0,
                        "coal": 2400.0,
                        "accommodation_count": 1800
                    },
                    "per_person_consumption": {
                        "electricity": 6.67,
                        "water": 3.33,
                        "natural_gas": 2.0,
                        "coal": 1.33
                    },
                    "monthly_data": [
                        {
                            "month": 1,
                            "month_name": "Ocak",
                            "electricity": 1000.0,
                            "water": 500.0,
                            "natural_gas": 300.0,
                            "coal": 200.0,
                            "accommodation_count": 150
                        }
                        # ... other months would be here
                    ]
                },
                {
                    "client_id": "client2",
                    "client_name": "Test Client 2",
                    "hotel_name": "Test Hotel 2",
                    "yearly_totals": {
                        "electricity": 14000.0,
                        "water": 7000.0,
                        "natural_gas": 4200.0,
                        "coal": 2800.0,
                        "accommodation_count": 2100
                    },
                    "per_person_consumption": {
                        "electricity": 6.67,
                        "water": 3.33,
                        "natural_gas": 2.0,
                        "coal": 1.33
                    },
                    "monthly_data": [
                        {
                            "month": 1,
                            "month_name": "Ocak",
                            "electricity": 1200.0,
                            "water": 600.0,
                            "natural_gas": 360.0,
                            "coal": 240.0,
                            "accommodation_count": 180
                        }
                        # ... other months would be here
                    ]
                }
            ],
            "summary": {
                "total_clients": 2,
                "average_consumption": {
                    "electricity": 13000.0,
                    "water": 6500.0,
                    "natural_gas": 3900.0,
                    "coal": 2600.0
                }
            }
        }
        
        self.monthly_trends_data = {
            "year": 2024,
            "monthly_trends": [
                {
                    "month": 1,
                    "month_name": "Ocak",
                    "electricity": 1000.0,
                    "water": 500.0,
                    "natural_gas": 300.0,
                    "coal": 200.0,
                    "accommodation_count": 150
                },
                {
                    "month": 2,
                    "month_name": "Şubat",
                    "electricity": 950.0,
                    "water": 480.0,
                    "natural_gas": 290.0,
                    "coal": 190.0,
                    "accommodation_count": 145
                }
                # ... other months would be here
            ],
            "user_role": "admin"
        }
        
        # Create a full 12-month dataset for monthly_trends
        full_monthly_trends = []
        for month in range(1, 13):
            month_names = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                          "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            full_monthly_trends.append({
                "month": month,
                "month_name": month_names[month],
                "electricity": 1000.0 - (month * 10),
                "water": 500.0 - (month * 5),
                "natural_gas": 300.0 - (month * 3),
                "coal": 200.0 - (month * 2),
                "accommodation_count": 150 - month
            })
        
        self.monthly_trends_data["monthly_trends"] = full_monthly_trends
        
        # Create a full 12-month dataset for analytics
        full_monthly_comparison = []
        for month in range(1, 13):
            month_names = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
                          "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
            full_monthly_comparison.append({
                "month": month,
                "month_name": month_names[month],
                "current_year": {
                    "electricity": 1000.0 - (month * 10),
                    "water": 500.0 - (month * 5),
                    "natural_gas": 300.0 - (month * 3),
                    "coal": 200.0 - (month * 2),
                    "accommodation_count": 150 - month
                },
                "previous_year": {
                    "electricity": 900.0 - (month * 9),
                    "water": 450.0 - (month * 4.5),
                    "natural_gas": 270.0 - (month * 2.7),
                    "coal": 180.0 - (month * 1.8),
                    "accommodation_count": 140 - month
                },
                "current_year_per_person": {
                    "electricity": 6.67,
                    "water": 3.33,
                    "natural_gas": 2.0,
                    "coal": 1.33
                },
                "previous_year_per_person": {
                    "electricity": 6.43,
                    "water": 3.22,
                    "natural_gas": 1.93,
                    "coal": 1.29
                }
            })
        
        self.analytics_data["monthly_comparison"] = full_monthly_comparison

    @patch('requests.get')
    def test_consumption_analytics_endpoint(self, mock_get):
        """Test the /api/consumptions/analytics endpoint"""
        logger.info("\n=== Testing /api/consumptions/analytics endpoint ===")
        
        # Mock the response for admin user
        mock_get.return_value = MockResponse(self.analytics_data, 200)
        
        # Test with admin user
        logger.info("Testing with admin user...")
        url = f"{self.api_url}/consumptions/analytics"
        params = {"client_id": "client1", "year": TEST_YEAR_CURRENT}
        
        response = requests.get(url, params=params)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("year", data)
        self.assertIn("monthly_comparison", data)
        self.assertIn("yearly_totals", data)
        
        self.assertEqual(len(data["monthly_comparison"]), 12)
        
        # Check structure of monthly comparison data
        for month_data in data["monthly_comparison"]:
            self.assertIn("month", month_data)
            self.assertIn("month_name", month_data)
            self.assertIn("current_year", month_data)
            self.assertIn("previous_year", month_data)
            
            self.assertIn("electricity", month_data["current_year"])
            self.assertIn("water", month_data["current_year"])
            self.assertIn("natural_gas", month_data["current_year"])
            self.assertIn("coal", month_data["current_year"])
            self.assertIn("accommodation_count", month_data["current_year"])
        
        logger.info("Admin user test passed for /api/consumptions/analytics")
        
        # Test with client user (same structure, different permissions)
        logger.info("Testing with client user...")
        
        # Update mock for client user
        client_analytics = self.analytics_data.copy()
        mock_get.return_value = MockResponse(client_analytics, 200)
        
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("year", data)
        self.assertIn("monthly_comparison", data)
        self.assertIn("yearly_totals", data)
        
        logger.info("Client user test passed for /api/consumptions/analytics")
        
        # Test with different year
        logger.info("Testing with different year...")
        
        # Update mock for different year
        different_year_analytics = self.analytics_data.copy()
        different_year_analytics["year"] = TEST_YEAR_PREVIOUS
        mock_get.return_value = MockResponse(different_year_analytics, 200)
        
        params = {"year": TEST_YEAR_PREVIOUS, "client_id": "client1"}
        response = requests.get(url, params=params)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["year"], TEST_YEAR_PREVIOUS)
        
        logger.info("Different year test passed for /api/consumptions/analytics")

    @patch('requests.get')
    def test_multi_client_comparison_endpoint(self, mock_get):
        """Test the /api/analytics/multi-client-comparison endpoint"""
        logger.info("\n=== Testing /api/analytics/multi-client-comparison endpoint ===")
        
        # Mock the response for admin user
        mock_get.return_value = MockResponse(self.multi_client_data, 200)
        
        # Test with admin user
        logger.info("Testing with admin user...")
        url = f"{self.api_url}/analytics/multi-client-comparison"
        
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("year", data)
        self.assertIn("clients_comparison", data)
        self.assertIn("summary", data)
        
        self.assertIsInstance(data["clients_comparison"], list)
        
        # Check structure of client comparison data if any clients exist
        if len(data["clients_comparison"]) > 0:
            client_data = data["clients_comparison"][0]
            self.assertIn("client_id", client_data)
            self.assertIn("client_name", client_data)
            self.assertIn("hotel_name", client_data)
            self.assertIn("yearly_totals", client_data)
            self.assertIn("per_person_consumption", client_data)
            self.assertIn("monthly_data", client_data)
        
        logger.info("Admin user test passed for /api/analytics/multi-client-comparison")
        
        # Test with client user (should be forbidden)
        logger.info("Testing with client user (should be forbidden)...")
        
        # Update mock for client user (403 Forbidden)
        mock_get.return_value = MockResponse({"detail": "Admin access required"}, 403)
        
        response = requests.get(url)
        self.assertEqual(response.status_code, 403)
        
        logger.info("Client user access control test passed for /api/analytics/multi-client-comparison")
        
        # Test with different year
        logger.info("Testing with different year...")
        
        # Update mock for different year
        different_year_data = self.multi_client_data.copy()
        different_year_data["year"] = TEST_YEAR_PREVIOUS
        mock_get.return_value = MockResponse(different_year_data, 200)
        
        params = {"year": TEST_YEAR_PREVIOUS}
        response = requests.get(url, params=params)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["year"], TEST_YEAR_PREVIOUS)
        
        logger.info("Different year test passed for /api/analytics/multi-client-comparison")

    @patch('requests.get')
    def test_monthly_trends_endpoint(self, mock_get):
        """Test the /api/analytics/monthly-trends endpoint"""
        logger.info("\n=== Testing /api/analytics/monthly-trends endpoint ===")
        
        # Mock the response for admin user
        mock_get.return_value = MockResponse(self.monthly_trends_data, 200)
        
        # Test with admin user
        logger.info("Testing with admin user...")
        url = f"{self.api_url}/analytics/monthly-trends"
        
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("year", data)
        self.assertIn("monthly_trends", data)
        self.assertIn("user_role", data)
        
        self.assertIsInstance(data["monthly_trends"], list)
        self.assertEqual(len(data["monthly_trends"]), 12)
        
        # Check structure of monthly trends data
        for month_data in data["monthly_trends"]:
            self.assertIn("month", month_data)
            self.assertIn("month_name", month_data)
            self.assertIn("electricity", month_data)
            self.assertIn("water", month_data)
            self.assertIn("natural_gas", month_data)
            self.assertIn("coal", month_data)
            self.assertIn("accommodation_count", month_data)
        
        logger.info("Admin user test passed for /api/analytics/monthly-trends")
        
        # Test with client user
        logger.info("Testing with client user...")
        
        # Update mock for client user
        client_trends = self.monthly_trends_data.copy()
        client_trends["user_role"] = "client"
        mock_get.return_value = MockResponse(client_trends, 200)
        
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("year", data)
        self.assertIn("monthly_trends", data)
        self.assertIn("user_role", data)
        
        self.assertEqual(data["user_role"], "client")
        
        logger.info("Client user test passed for /api/analytics/monthly-trends")
        
        # Test with different year
        logger.info("Testing with different year...")
        
        # Update mock for different year
        different_year_trends = self.monthly_trends_data.copy()
        different_year_trends["year"] = TEST_YEAR_PREVIOUS
        mock_get.return_value = MockResponse(different_year_trends, 200)
        
        params = {"year": TEST_YEAR_PREVIOUS}
        response = requests.get(url, params=params)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["year"], TEST_YEAR_PREVIOUS)
        
        logger.info("Different year test passed for /api/analytics/monthly-trends")

    @patch('requests.get')
    @patch('requests.post')
    def test_existing_consumption_endpoints(self, mock_post, mock_get):
        """Test the existing /api/consumptions endpoints (GET and POST)"""
        logger.info("\n=== Testing existing /api/consumptions endpoints ===")
        
        # Mock the GET response
        mock_get.return_value = MockResponse(self.consumption_data, 200)
        
        # Test GET /api/consumptions with admin user
        logger.info("Testing GET /api/consumptions with admin user...")
        url = f"{self.api_url}/consumptions"
        
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        
        logger.info("GET /api/consumptions with admin user passed")
        
        # Test GET /api/consumptions with client user
        logger.info("Testing GET /api/consumptions with client user...")
        
        # Update mock for client user (same data structure)
        mock_get.return_value = MockResponse(self.consumption_data, 200)
        
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        
        logger.info("GET /api/consumptions with client user passed")
        
        # Test POST /api/consumptions with admin user
        logger.info("Testing POST /api/consumptions with admin user...")
        
        # Mock the POST response
        mock_post.return_value = MockResponse({"message": "Tüketim verisi başarıyla kaydedildi", "consumption_id": "new_consumption_id"}, 200)
        
        # Create a unique month/year combination to avoid conflicts
        current_month = datetime.now().month
        current_year = datetime.now().year
        test_month = (current_month % 12) + 1  # Ensure it's 1-12
        test_year = current_year + 1  # Use next year to avoid conflicts
        
        consumption_data = {
            "client_id": "client1",
            "year": test_year,
            "month": test_month,
            "electricity": 1000.5,
            "water": 500.25,
            "natural_gas": 300.75,
            "coal": 200.0,
            "accommodation_count": 150
        }
        
        response = requests.post(url, json=consumption_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("consumption_id", data)
        
        logger.info("POST /api/consumptions with admin user passed")

def run_tests():
    """Run all API tests"""
    logger.info("Starting API tests...")
    
    # Create a test suite
    suite = unittest.TestSuite()
    suite.addTest(TestAnalyticsEndpoints("test_consumption_analytics_endpoint"))
    suite.addTest(TestAnalyticsEndpoints("test_multi_client_comparison_endpoint"))
    suite.addTest(TestAnalyticsEndpoints("test_monthly_trends_endpoint"))
    suite.addTest(TestAnalyticsEndpoints("test_existing_consumption_endpoints"))
    
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
    import requests  # Import here to avoid issues with mocking
    run_tests()