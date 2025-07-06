import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Local backend URL
LOCAL_API_URL = "http://localhost:8001/api"

def test_endpoint(url, headers=None):
    """Test an endpoint and log the results"""
    logger.info(f"Testing endpoint: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
            logger.info(f"Response data: {json.dumps(data, indent=2)}")
            logger.info("✅ Endpoint test passed")
            return True
        elif response.status_code == 404:
            logger.error("❌ Endpoint returned 404 Not Found")
            return False
        else:
            logger.warning(f"⚠️ Unexpected status code: {response.status_code}")
            if response.headers.get('content-type') == 'application/json':
                logger.warning(f"Response: {response.json()}")
            else:
                logger.warning(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing endpoint: {str(e)}")
        return False

def main():
    """Test all email management endpoints"""
    # Test regular endpoints first
    test_endpoint(f"{LOCAL_API_URL}/health")
    test_endpoint(f"{LOCAL_API_URL}/clients")
    test_endpoint(f"{LOCAL_API_URL}/documents")
    test_endpoint(f"{LOCAL_API_URL}/trainings")
    
    # Test email management endpoints
    test_endpoint(f"{LOCAL_API_URL}/email-management/clients-real")
    test_endpoint(f"{LOCAL_API_URL}/email-management/documents-real")
    test_endpoint(f"{LOCAL_API_URL}/email-management/trainings-real")

if __name__ == "__main__":
    main()