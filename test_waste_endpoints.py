import requests
import json
import logging
import sys
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_waste_management_endpoints():
    """Test waste management endpoints"""
    logger.info("\n=== Testing waste management endpoints ===")
    
    try:
        # Read frontend .env file to get backend URL
        with open('/app/frontend/.env', 'r') as f:
            env_content = f.read()
            
        # Extract REACT_APP_BACKEND_URL
        backend_url = None
        for line in env_content.splitlines():
            if line.startswith('REACT_APP_BACKEND_URL='):
                backend_url = line.split('=', 1)[1].strip()
                break
                
        logger.info(f"Using backend URL: {backend_url}")
        
        # Test GET /api/waste-management endpoint
        url = f"{backend_url}/api/waste-management"
        logger.info(f"Testing GET {url}")
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # We expect a 403 Not authenticated response
            if response.status_code == 403:
                logger.info("✅ GET /api/waste-management returns 403 Not authenticated as expected")
            else:
                logger.error(f"❌ GET /api/waste-management returns {response.status_code} instead of 403")
        except Exception as e:
            logger.error(f"Error testing GET /api/waste-management: {str(e)}")
        
        # Test GET /api/waste-management/analytics endpoint
        url = f"{backend_url}/api/waste-management/analytics"
        logger.info(f"Testing GET {url}")
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # We expect a 403 Not authenticated response
            if response.status_code == 403:
                logger.info("✅ GET /api/waste-management/analytics returns 403 Not authenticated as expected")
            else:
                logger.error(f"❌ GET /api/waste-management/analytics returns {response.status_code} instead of 403")
        except Exception as e:
            logger.error(f"Error testing GET /api/waste-management/analytics: {str(e)}")
        
        # Test POST /api/waste-management endpoint
        url = f"{backend_url}/api/waste-management"
        logger.info(f"Testing POST {url}")
        
        test_waste_data = {
            "year": 2024,
            "month": 7,
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
        
        try:
            response = requests.post(url, json=test_waste_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # We expect a 403 Not authenticated response
            if response.status_code == 403:
                logger.info("✅ POST /api/waste-management returns 403 Not authenticated as expected")
            else:
                logger.error(f"❌ POST /api/waste-management returns {response.status_code} instead of 403")
        except Exception as e:
            logger.error(f"Error testing POST /api/waste-management: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing waste management endpoints: {str(e)}")
        return False

def main():
    """Run waste management endpoints test"""
    logger.info("Starting waste management endpoints test...")
    
    # Test waste management endpoints
    test_result = test_waste_management_endpoints()
    
    # Summary
    logger.info("\n=== Summary ===")
    logger.info(f"Waste management endpoints test: {'PASSED' if test_result else 'FAILED'}")
    
    if test_result:
        logger.info("Waste management endpoints test PASSED")
        return 0
    else:
        logger.error("Waste management endpoints test FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())