import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Emergentagent backend URL
BACKEND_URL = "https://ed2a8706-f4d4-4fc1-b76e-11ca7aabd94f.preview.emergentagent.com/api"

# Test JWT token for admin user
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

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
    # Headers for admin user
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test regular endpoints first
    test_endpoint(f"{BACKEND_URL}/health")
    test_endpoint(f"{BACKEND_URL}/clients", headers)
    test_endpoint(f"{BACKEND_URL}/documents", headers)
    test_endpoint(f"{BACKEND_URL}/trainings", headers)
    
    # Test email management endpoints
    test_endpoint(f"{BACKEND_URL}/email-management/clients-real", headers)
    test_endpoint(f"{BACKEND_URL}/email-management/documents-real", headers)
    test_endpoint(f"{BACKEND_URL}/email-management/trainings-real", headers)

if __name__ == "__main__":
    main()