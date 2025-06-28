import requests
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend/.env
BACKEND_URL = "https://1ec08c3c-6aac-4fbe-a51f-120fca82320d.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def test_folders_endpoint():
    """Test the GET /api/folders endpoint directly"""
    logger.info("\n=== Testing GET /api/folders endpoint directly ===")
    
    # Make a direct request to the folders endpoint
    url = f"{API_URL}/folders"
    
    try:
        response = requests.get(url)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        # Try to parse the response body
        try:
            response_data = response.json()
            logger.info(f"Response body (JSON): {json.dumps(response_data, indent=2)[:500]}...")
        except:
            logger.info(f"Response body (text): {response.text[:500]}...")
        
        # Check if the endpoint is accessible
        if response.status_code == 200:
            logger.info("✅ Folders endpoint is accessible and returning data")
            return True
        elif response.status_code in [401, 403]:
            logger.info("✅ Folders endpoint is accessible but requires authentication")
            return True
        else:
            logger.info(f"❌ Folders endpoint returned unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing folders endpoint: {str(e)}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting folder endpoint tests...")
    
    # Test folders endpoint
    folders_result = test_folders_endpoint()
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Folders endpoint test: {'PASSED' if folders_result else 'FAILED'}")
    
    return folders_result

if __name__ == "__main__":
    main()