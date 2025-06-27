import requests
import json
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend .env
BACKEND_URL = "https://1f0c3a30-ba23-4cb9-a340-2a6d39e2d493.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

# Test data
TEST_YEAR_CURRENT = 2024
TEST_YEAR_PREVIOUS = 2025

# Mock user tokens (these would normally be obtained from Clerk authentication)
# In a real environment, you would use actual tokens from Clerk
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHZ4U3VIZHdnQVdIUXNLRWZMTXVyY2JfdGVzdCIsInR5cCI6IkpXVCJ9.eyJhenAiOiJodHRwczovL2FkYXB0aW5nLWVmdC02LmNsZXJrLmFjY291bnRzLmRldiIsImV4cCI6MTcxNjQwMDAwMCwiaWF0IjoxNzE1NDAwMDAwLCJpc3MiOiJodHRwczovL2FkYXB0aW5nLWVmdC02LmNsZXJrLmFjY291bnRzLmRldiIsIm5iZiI6MTcxNTQwMDAwMCwic3ViIjoiYWRtaW5fdXNlcl9pZCIsInJvbGUiOiJhZG1pbiJ9.signature"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHZ4U3VIZHdnQVdIUXNLRWZMTXVyY2JfdGVzdCIsInR5cCI6IkpXVCJ9.eyJhenAiOiJodHRwczovL2FkYXB0aW5nLWVmdC02LmNsZXJrLmFjY291bnRzLmRldiIsImV4cCI6MTcxNjQwMDAwMCwiaWF0IjoxNzE1NDAwMDAwLCJpc3MiOiJodHRwczovL2FkYXB0aW5nLWVmdC02LmNsZXJrLmFjY291bnRzLmRldiIsIm5iZiI6MTcxNTQwMDAwMCwic3ViIjoiY2xpZW50X3VzZXJfaWQiLCJyb2xlIjoiY2xpZW50In0.signature"

# Helper functions
def make_request(endpoint, method="GET", token=None, params=None, data=None):
    """Make a request to the API with optional authentication"""
    url = f"{API_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            headers["Content-Type"] = "application/json"
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        return response
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return None

def validate_response(response, expected_status=200):
    """Validate the response status code and return JSON data"""
    if not response:
        logger.error("No response received")
        return None
    
    if response.status_code != expected_status:
        logger.error(f"Expected status {expected_status}, got {response.status_code}: {response.text}")
        return None
    
    try:
        return response.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return None

def test_consumption_analytics_endpoint():
    """Test the /api/consumptions/analytics endpoint"""
    logger.info("\n=== Testing /api/consumptions/analytics endpoint ===")
    
    # Test with admin user
    logger.info("Testing with admin user...")
    
    # Get a client ID first (admin needs to specify client_id)
    clients_response = make_request("/clients", token=ADMIN_TOKEN)
    clients_data = validate_response(clients_response)
    
    if not clients_data or len(clients_data) == 0:
        logger.error("No clients found for admin user")
        return False
    
    client_id = clients_data[0]["id"]
    
    # Test with current year
    params = {"client_id": client_id, "year": TEST_YEAR_CURRENT}
    response = make_request("/consumptions/analytics", token=ADMIN_TOKEN, params=params)
    data = validate_response(response)
    
    if not data:
        return False
    
    # Validate response structure
    if "year" not in data or "monthly_comparison" not in data or "yearly_totals" not in data:
        logger.error("Missing required fields in response")
        return False
    
    if not isinstance(data["monthly_comparison"], list):
        logger.error("monthly_comparison should be a list")
        return False
    
    if len(data["monthly_comparison"]) != 12:
        logger.error(f"Expected 12 months in monthly_comparison, got {len(data['monthly_comparison'])}")
        return False
    
    # Check structure of monthly comparison data
    for month_data in data["monthly_comparison"]:
        if not all(key in month_data for key in ["month", "month_name", "current_year", "previous_year"]):
            logger.error(f"Missing required fields in month data: {month_data}")
            return False
        
        if not all(key in month_data["current_year"] for key in ["electricity", "water", "natural_gas", "coal", "accommodation_count"]):
            logger.error(f"Missing required fields in current_year data: {month_data['current_year']}")
            return False
    
    logger.info("Admin user test passed for /api/consumptions/analytics")
    
    # Test with client user
    logger.info("Testing with client user...")
    response = make_request("/consumptions/analytics", token=CLIENT_TOKEN)
    data = validate_response(response)
    
    if not data:
        return False
    
    # Validate response structure (same checks as admin)
    if "year" not in data or "monthly_comparison" not in data or "yearly_totals" not in data:
        logger.error("Missing required fields in client response")
        return False
    
    logger.info("Client user test passed for /api/consumptions/analytics")
    
    # Test with different year
    params = {"year": TEST_YEAR_PREVIOUS, "client_id": client_id}
    response = make_request("/consumptions/analytics", token=ADMIN_TOKEN, params=params)
    data = validate_response(response)
    
    if not data:
        return False
    
    if data["year"] != TEST_YEAR_PREVIOUS:
        logger.error(f"Expected year {TEST_YEAR_PREVIOUS}, got {data['year']}")
        return False
    
    logger.info("Different year test passed for /api/consumptions/analytics")
    
    return True

def test_multi_client_comparison_endpoint():
    """Test the /api/analytics/multi-client-comparison endpoint"""
    logger.info("\n=== Testing /api/analytics/multi-client-comparison endpoint ===")
    
    # Test with admin user
    logger.info("Testing with admin user...")
    response = make_request("/analytics/multi-client-comparison", token=ADMIN_TOKEN)
    data = validate_response(response)
    
    if not data:
        return False
    
    # Validate response structure
    if "year" not in data or "clients_comparison" not in data or "summary" not in data:
        logger.error("Missing required fields in response")
        return False
    
    if not isinstance(data["clients_comparison"], list):
        logger.error("clients_comparison should be a list")
        return False
    
    # Check structure of client comparison data if any clients exist
    if len(data["clients_comparison"]) > 0:
        client_data = data["clients_comparison"][0]
        if not all(key in client_data for key in ["client_id", "client_name", "hotel_name", "yearly_totals", "per_person_consumption", "monthly_data"]):
            logger.error(f"Missing required fields in client data: {client_data}")
            return False
    
    logger.info("Admin user test passed for /api/analytics/multi-client-comparison")
    
    # Test with client user (should be forbidden)
    logger.info("Testing with client user (should be forbidden)...")
    response = make_request("/analytics/multi-client-comparison", token=CLIENT_TOKEN)
    
    if response.status_code != 403:
        logger.error(f"Expected status 403 for client user, got {response.status_code}")
        return False
    
    logger.info("Client user access control test passed for /api/analytics/multi-client-comparison")
    
    # Test with different year
    params = {"year": TEST_YEAR_PREVIOUS}
    response = make_request("/analytics/multi-client-comparison", token=ADMIN_TOKEN, params=params)
    data = validate_response(response)
    
    if not data:
        return False
    
    if data["year"] != TEST_YEAR_PREVIOUS:
        logger.error(f"Expected year {TEST_YEAR_PREVIOUS}, got {data['year']}")
        return False
    
    logger.info("Different year test passed for /api/analytics/multi-client-comparison")
    
    return True

def test_monthly_trends_endpoint():
    """Test the /api/analytics/monthly-trends endpoint"""
    logger.info("\n=== Testing /api/analytics/monthly-trends endpoint ===")
    
    # Test with admin user
    logger.info("Testing with admin user...")
    response = make_request("/analytics/monthly-trends", token=ADMIN_TOKEN)
    data = validate_response(response)
    
    if not data:
        return False
    
    # Validate response structure
    if "year" not in data or "monthly_trends" not in data or "user_role" not in data:
        logger.error("Missing required fields in response")
        return False
    
    if not isinstance(data["monthly_trends"], list):
        logger.error("monthly_trends should be a list")
        return False
    
    if len(data["monthly_trends"]) != 12:
        logger.error(f"Expected 12 months in monthly_trends, got {len(data['monthly_trends'])}")
        return False
    
    # Check structure of monthly trends data
    for month_data in data["monthly_trends"]:
        if not all(key in month_data for key in ["month", "month_name", "electricity", "water", "natural_gas", "coal", "accommodation_count"]):
            logger.error(f"Missing required fields in month data: {month_data}")
            return False
    
    logger.info("Admin user test passed for /api/analytics/monthly-trends")
    
    # Test with client user
    logger.info("Testing with client user...")
    response = make_request("/analytics/monthly-trends", token=CLIENT_TOKEN)
    data = validate_response(response)
    
    if not data:
        return False
    
    # Validate response structure (same checks as admin)
    if "year" not in data or "monthly_trends" not in data or "user_role" not in data:
        logger.error("Missing required fields in client response")
        return False
    
    if data["user_role"] != "client":
        logger.error(f"Expected user_role 'client', got '{data['user_role']}'")
        return False
    
    logger.info("Client user test passed for /api/analytics/monthly-trends")
    
    # Test with different year
    params = {"year": TEST_YEAR_PREVIOUS}
    response = make_request("/analytics/monthly-trends", token=ADMIN_TOKEN, params=params)
    data = validate_response(response)
    
    if not data:
        return False
    
    if data["year"] != TEST_YEAR_PREVIOUS:
        logger.error(f"Expected year {TEST_YEAR_PREVIOUS}, got {data['year']}")
        return False
    
    logger.info("Different year test passed for /api/analytics/monthly-trends")
    
    return True

def test_existing_consumption_endpoints():
    """Test the existing /api/consumptions endpoints (GET and POST)"""
    logger.info("\n=== Testing existing /api/consumptions endpoints ===")
    
    # Test GET /api/consumptions with admin user
    logger.info("Testing GET /api/consumptions with admin user...")
    response = make_request("/consumptions", token=ADMIN_TOKEN)
    data = validate_response(response)
    
    if not data:
        return False
    
    logger.info("GET /api/consumptions with admin user passed")
    
    # Test GET /api/consumptions with client user
    logger.info("Testing GET /api/consumptions with client user...")
    response = make_request("/consumptions", token=CLIENT_TOKEN)
    data = validate_response(response)
    
    if not data:
        return False
    
    logger.info("GET /api/consumptions with client user passed")
    
    # Test POST /api/consumptions with admin user
    logger.info("Testing POST /api/consumptions with admin user...")
    
    # Get a client ID first
    clients_response = make_request("/clients", token=ADMIN_TOKEN)
    clients_data = validate_response(clients_response)
    
    if not clients_data or len(clients_data) == 0:
        logger.error("No clients found for admin user")
        return False
    
    client_id = clients_data[0]["id"]
    
    # Create a unique month/year combination to avoid conflicts
    current_month = datetime.now().month
    current_year = datetime.now().year
    test_month = (current_month % 12) + 1  # Ensure it's 1-12
    test_year = current_year + 1  # Use next year to avoid conflicts
    
    consumption_data = {
        "client_id": client_id,
        "year": test_year,
        "month": test_month,
        "electricity": 1000.5,
        "water": 500.25,
        "natural_gas": 300.75,
        "coal": 200.0,
        "accommodation_count": 150
    }
    
    response = make_request("/consumptions", method="POST", token=ADMIN_TOKEN, data=consumption_data)
    
    # If the consumption already exists, we'll get a 400 error
    if response.status_code == 400 and "zaten mevcut" in response.text:
        logger.info("Consumption data already exists for this month/year, skipping POST test")
    else:
        data = validate_response(response)
        if not data:
            return False
        logger.info("POST /api/consumptions with admin user passed")
    
    return True

def run_all_tests():
    """Run all API tests"""
    logger.info("Starting API tests...")
    
    # Test authentication endpoints
    logger.info("\n=== Testing authentication endpoints ===")
    auth_response = make_request("/auth/me", token=ADMIN_TOKEN)
    if validate_response(auth_response):
        logger.info("Authentication endpoint test passed")
    else:
        logger.error("Authentication endpoint test failed")
        return False
    
    # Test consumption analytics endpoint
    consumption_analytics_result = test_consumption_analytics_endpoint()
    
    # Test multi-client comparison endpoint
    multi_client_comparison_result = test_multi_client_comparison_endpoint()
    
    # Test monthly trends endpoint
    monthly_trends_result = test_monthly_trends_endpoint()
    
    # Test existing consumption endpoints
    existing_consumption_result = test_existing_consumption_endpoints()
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Consumption Analytics Endpoint: {'PASSED' if consumption_analytics_result else 'FAILED'}")
    logger.info(f"Multi-Client Comparison Endpoint: {'PASSED' if multi_client_comparison_result else 'FAILED'}")
    logger.info(f"Monthly Trends Endpoint: {'PASSED' if monthly_trends_result else 'FAILED'}")
    logger.info(f"Existing Consumption Endpoints: {'PASSED' if existing_consumption_result else 'FAILED'}")
    
    overall_result = all([
        consumption_analytics_result,
        multi_client_comparison_result,
        monthly_trends_result,
        existing_consumption_result
    ])
    
    logger.info(f"\nOverall Test Result: {'PASSED' if overall_result else 'FAILED'}")
    return overall_result

if __name__ == "__main__":
    run_all_tests()