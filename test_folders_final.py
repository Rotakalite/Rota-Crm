import requests
import logging
import json
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend/.env
BACKEND_URL = "https://4aeb8cfa-61f1-4648-8b57-402bd2c9bfe3.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def test_folders_endpoint():
    """Test the GET /api/folders endpoint directly"""
    logger.info("\n=== Testing GET /api/folders endpoint directly ===")
    
    # Make a direct request to the folders endpoint
    url = f"{API_URL}/folders"
    
    try:
        response = requests.get(url)
        logger.info(f"Response status code: {response.status_code}")
        
        # Check if the endpoint is accessible
        if response.status_code == 200:
            logger.info("✅ Folders endpoint is accessible and returning data without authentication")
            try:
                data = response.json()
                logger.info(f"Found {len(data)} folders")
                return True
            except:
                logger.error("❌ Response is not valid JSON")
                logger.info(f"Response body: {response.text[:500]}...")
                return False
        elif response.status_code in [401, 403]:
            logger.info("✅ Folders endpoint is accessible but requires authentication (expected behavior)")
            try:
                error_data = response.json()
                logger.info(f"Error message: {error_data.get('detail', 'No detail provided')}")
            except:
                logger.info(f"Response body: {response.text[:500]}...")
            return True
        else:
            logger.error(f"❌ Folders endpoint returned unexpected status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:500]}...")
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
    
    # Return exit code based on test result
    return 0 if folders_result else 1

if __name__ == "__main__":
    sys.exit(main())