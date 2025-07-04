import requests
import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "https://d416542e-378b-422c-aa16-44ab4c991507.preview.emergentagent.com/api"

# Test data for waste management
test_waste_data = {
    "year": 2024,
    "month": 6,
    "organic_waste": 50.5,
    "plastic_waste": 25.0,
    "glass_waste": 15.5,
    "paper_waste": 30.0,
    "metal_waste": 10.0,
    "electronic_waste": 5.0,
    "oil_waste": 5.0,
    "mixed_waste": 20.0,
    "client_id": "test_client_id"
}

def test_create_waste_record():
    """Test POST /api/waste-management endpoint"""
    logger.info("\n=== Testing POST /api/waste-management endpoint ===")
    
    url = f"{BACKEND_URL}/waste-management"
    
    try:
        response = requests.post(url, json=test_waste_data)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            logger.info(f"Response data: {data}")
            return True
        else:
            logger.error(f"Failed to create waste record: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error testing POST /api/waste-management: {str(e)}")
        return False

def test_get_waste_records():
    """Test GET /api/waste-management endpoint"""
    logger.info("\n=== Testing GET /api/waste-management endpoint ===")
    
    url = f"{BACKEND_URL}/waste-management"
    
    try:
        response = requests.get(url)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {len(data)} waste records")
            return True
        else:
            logger.error(f"Failed to get waste records: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error testing GET /api/waste-management: {str(e)}")
        return False

def test_get_waste_analytics():
    """Test GET /api/waste-management/analytics endpoint"""
    logger.info("\n=== Testing GET /api/waste-management/analytics endpoint ===")
    
    url = f"{BACKEND_URL}/waste-management/analytics"
    
    try:
        response = requests.get(url)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response data keys: {data.keys()}")
            return True
        else:
            logger.error(f"Failed to get waste analytics: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error testing GET /api/waste-management/analytics: {str(e)}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting waste management tests...")
    
    # Test creating a waste record
    create_result = test_create_waste_record()
    
    # Test getting waste records
    get_result = test_get_waste_records()
    
    # Test getting waste analytics
    analytics_result = test_get_waste_analytics()
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Create waste record: {'PASSED' if create_result else 'FAILED'}")
    logger.info(f"Get waste records: {'PASSED' if get_result else 'FAILED'}")
    logger.info(f"Get waste analytics: {'PASSED' if analytics_result else 'FAILED'}")
    
    if create_result and get_result and analytics_result:
        logger.info("All tests PASSED")
        return 0
    else:
        logger.error("Some tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())