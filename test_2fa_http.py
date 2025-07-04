import requests
import logging
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "http://localhost:8001/api"

def test_2fa_endpoints():
    """Test 2FA endpoints"""
    logger.info("Testing 2FA endpoints...")
    
    # Test /api/auth/2fa/send-code endpoint
    logger.info("\n=== Testing /api/auth/2fa/send-code endpoint ===")
    
    url = f"{BACKEND_URL}/auth/2fa/send-code"
    
    # JSON data for the request
    json_data = {
        "email": "test@example.com"
    }
    
    try:
        response = requests.post(url, json=json_data)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ 2FA send code endpoint working correctly")
        elif response.status_code == 500:
            logger.info("❌ 2FA send code endpoint returning 500 error")
            logger.info(f"Error detail: {response.json().get('detail', '')}")
        elif response.status_code in [401, 403]:
            logger.info(f"❌ Authentication error: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing 2FA send code endpoint: {str(e)}")
    
    # Test /api/auth/2fa/status endpoint
    logger.info("\n=== Testing /api/auth/2fa/status endpoint ===")
    
    url = f"{BACKEND_URL}/auth/2fa/status"
    
    try:
        response = requests.get(url)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ 2FA status endpoint working correctly")
        elif response.status_code == 500:
            logger.info("❌ 2FA status endpoint returning 500 error")
            logger.info(f"Error detail: {response.json().get('detail', '')}")
        elif response.status_code in [401, 403]:
            logger.info(f"❌ Authentication error: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing 2FA status endpoint: {str(e)}")
    
    # Test /api/auth/2fa/verify-code endpoint
    logger.info("\n=== Testing /api/auth/2fa/verify-code endpoint ===")
    
    url = f"{BACKEND_URL}/auth/2fa/verify-code"
    
    # JSON data for the request
    json_data = {
        "email": "test@example.com",
        "code": "123456"  # This is a dummy code, we expect it to fail verification
    }
    
    try:
        response = requests.post(url, json=json_data)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ 2FA verify code endpoint working correctly")
        elif response.status_code == 400:
            logger.info("✅ 2FA verify code endpoint correctly rejected invalid code")
            logger.info(f"Error detail: {response.json().get('detail', '')}")
        elif response.status_code == 500:
            logger.info("❌ 2FA verify code endpoint returning 500 error")
            logger.info(f"Error detail: {response.json().get('detail', '')}")
        elif response.status_code in [401, 403]:
            logger.info(f"❌ Authentication error: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error testing 2FA verify code endpoint: {str(e)}")

if __name__ == "__main__":
    test_2fa_endpoints()