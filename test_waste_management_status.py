import requests
import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

def test_waste_management_endpoints_status_codes():
    """Test waste management endpoints status codes with specific client_id"""
    logger.info("\n=== Testing Waste Management Endpoints Status Codes ===")
    
    # Test data
    client_id = "4d7d0100-bdb4-44a0-ac4e-125d3b77a2bb"
    year = 2025
    
    # Test GET /api/waste-management endpoint
    logger.info("\n=== Testing GET /api/waste-management endpoint ===")
    url = f"{RAILWAY_API_URL}/waste-management"
    params = {
        "year": year,
        "client_id": client_id
    }
    
    # Test GET request (will get 403 without auth, which is expected)
    logger.info("Testing GET request without auth...")
    response = requests.get(url, params=params)
    logger.info(f"GET response status code: {response.status_code}")
    logger.info(f"GET response body: {response.text}")
    
    get_status_success = response.status_code == 403  # Expected 403 without auth
    logger.info(f"GET status code check: {'PASSED' if get_status_success else 'FAILED'}")
    
    # Test POST /api/waste-management endpoint
    logger.info("\n=== Testing POST /api/waste-management endpoint ===")
    url = f"{RAILWAY_API_URL}/waste-management"
    
    # Test data
    waste_data = {
        "year": year,
        "month": 6,
        "organic_waste": 50.5,
        "plastic_waste": 25.0,
        "glass_waste": 15.5,
        "paper_waste": 30.0,
        "metal_waste": 10.0,
        "electronic_waste": 5.0,
        "oil_waste": 5.0,
        "mixed_waste": 20.0,
        "client_id": client_id
    }
    
    # Test POST request (will get 403 without auth, which is expected)
    logger.info("Testing POST request without auth...")
    response = requests.post(url, json=waste_data)
    logger.info(f"POST response status code: {response.status_code}")
    logger.info(f"POST response body: {response.text}")
    
    post_status_success = response.status_code == 403  # Expected 403 without auth
    logger.info(f"POST status code check: {'PASSED' if post_status_success else 'FAILED'}")
    
    # Test GET /api/waste-management/analytics endpoint
    logger.info("\n=== Testing GET /api/waste-management/analytics endpoint ===")
    url = f"{RAILWAY_API_URL}/waste-management/analytics"
    params = {
        "year": year,
        "client_id": client_id
    }
    
    # Test GET request (will get 403 without auth, which is expected)
    logger.info("Testing GET request without auth...")
    response = requests.get(url, params=params)
    logger.info(f"GET analytics response status code: {response.status_code}")
    logger.info(f"GET analytics response body: {response.text}")
    
    analytics_status_success = response.status_code == 403  # Expected 403 without auth
    logger.info(f"GET analytics status code check: {'PASSED' if analytics_status_success else 'FAILED'}")
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"GET /waste-management status code: {'PASSED' if get_status_success else 'FAILED'}")
    logger.info(f"POST /waste-management status code: {'PASSED' if post_status_success else 'FAILED'}")
    logger.info(f"GET /waste-management/analytics status code: {'PASSED' if analytics_status_success else 'FAILED'}")
    
    # Overall result
    overall_success = get_status_success and post_status_success and analytics_status_success
    logger.info(f"Overall status code test: {'PASSED' if overall_success else 'FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    success = test_waste_management_endpoints_status_codes()
    sys.exit(0 if success else 1)