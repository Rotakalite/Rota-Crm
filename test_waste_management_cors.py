import requests
import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

def test_waste_management_endpoints():
    """Test waste management endpoints with specific client_id"""
    logger.info("\n=== Testing Waste Management Endpoints ===")
    
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
    
    # Test OPTIONS request for CORS preflight
    logger.info("Testing CORS preflight request...")
    response = requests.options(url)
    logger.info(f"OPTIONS response status code: {response.status_code}")
    
    # Check CORS headers
    cors_headers = {
        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
        'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
    }
    logger.info(f"CORS headers: {cors_headers}")
    
    cors_success = (
        response.status_code == 200 and
        'Access-Control-Allow-Origin' in response.headers and
        'Access-Control-Allow-Methods' in response.headers and
        'Access-Control-Allow-Headers' in response.headers
    )
    
    logger.info(f"CORS preflight: {'PASSED' if cors_success else 'FAILED'}")
    
    # Test GET request (will get 403 without auth, but we can check CORS headers)
    logger.info("Testing GET request without auth...")
    response = requests.get(url, params=params)
    logger.info(f"GET response status code: {response.status_code}")
    
    # Check CORS headers
    cors_headers = {
        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin')
    }
    logger.info(f"CORS headers: {cors_headers}")
    
    get_cors_success = 'Access-Control-Allow-Origin' in response.headers
    logger.info(f"GET CORS headers: {'PASSED' if get_cors_success else 'FAILED'}")
    
    # Test POST /api/waste-management endpoint
    logger.info("\n=== Testing POST /api/waste-management endpoint ===")
    url = f"{RAILWAY_API_URL}/waste-management"
    
    # Test OPTIONS request for CORS preflight
    logger.info("Testing CORS preflight request...")
    response = requests.options(url)
    logger.info(f"OPTIONS response status code: {response.status_code}")
    
    # Check CORS headers
    cors_headers = {
        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
        'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
    }
    logger.info(f"CORS headers: {cors_headers}")
    
    post_cors_success = (
        response.status_code == 200 and
        'Access-Control-Allow-Origin' in response.headers and
        'Access-Control-Allow-Methods' in response.headers and
        'Access-Control-Allow-Headers' in response.headers
    )
    
    logger.info(f"POST CORS preflight: {'PASSED' if post_cors_success else 'FAILED'}")
    
    # Test GET /api/waste-management/analytics endpoint
    logger.info("\n=== Testing GET /api/waste-management/analytics endpoint ===")
    url = f"{RAILWAY_API_URL}/waste-management/analytics"
    params = {
        "year": year,
        "client_id": client_id
    }
    
    # Test OPTIONS request for CORS preflight
    logger.info("Testing CORS preflight request...")
    response = requests.options(url)
    logger.info(f"OPTIONS response status code: {response.status_code}")
    
    # Check CORS headers
    cors_headers = {
        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
        'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
    }
    logger.info(f"CORS headers: {cors_headers}")
    
    analytics_cors_success = (
        response.status_code == 200 and
        'Access-Control-Allow-Origin' in response.headers and
        'Access-Control-Allow-Methods' in response.headers and
        'Access-Control-Allow-Headers' in response.headers
    )
    
    logger.info(f"Analytics CORS preflight: {'PASSED' if analytics_cors_success else 'FAILED'}")
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"CORS preflight for GET /waste-management: {'PASSED' if cors_success else 'FAILED'}")
    logger.info(f"CORS headers for GET /waste-management: {'PASSED' if get_cors_success else 'FAILED'}")
    logger.info(f"CORS preflight for POST /waste-management: {'PASSED' if post_cors_success else 'FAILED'}")
    logger.info(f"CORS preflight for GET /waste-management/analytics: {'PASSED' if analytics_cors_success else 'FAILED'}")
    
    # Overall result
    overall_success = cors_success and get_cors_success and post_cors_success and analytics_cors_success
    logger.info(f"Overall CORS test: {'PASSED' if overall_success else 'FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    success = test_waste_management_endpoints()
    sys.exit(0 if success else 1)