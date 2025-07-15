import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "https://5d84c72f-46a8-441d-903f-729b5668f555.preview.emergentagent.com/api"

def test_supplier_endpoints():
    """Test supplier management endpoints"""
    logger.info("Testing supplier management endpoints...")
    
    # Test categories list endpoint
    logger.info("Testing GET /api/suppliers/categories/list endpoint...")
    response = requests.get(f"{BACKEND_URL}/suppliers/categories/list")
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response body: {response.text}")
    
    # Test certifications list endpoint
    logger.info("Testing GET /api/suppliers/certifications/list endpoint...")
    response = requests.get(f"{BACKEND_URL}/suppliers/certifications/list")
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response body: {response.text}")
    
    # Test suppliers endpoint
    logger.info("Testing GET /api/suppliers endpoint...")
    response = requests.get(f"{BACKEND_URL}/suppliers")
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response body: {response.text}")
    
    # Test suppliers analytics endpoint
    logger.info("Testing GET /api/suppliers/analytics/dashboard endpoint...")
    response = requests.get(f"{BACKEND_URL}/suppliers/analytics/dashboard")
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response body: {response.text}")

if __name__ == "__main__":
    test_supplier_endpoints()