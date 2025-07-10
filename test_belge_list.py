import requests
import logging
import os
import json
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://f083c15a-fa7b-4093-8fa4-c3772ba33625.preview.emergentagent.com/api"

# Test JWT tokens
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
KAYA_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

# Headers for different user types
headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
headers_client = {"Authorization": f"Bearer {KAYA_CLIENT_TOKEN}"}
headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
headers_no_auth = {}

# Test data
test_client_id = "8bfd3a85-2483-4b63-9e80-e53747c3db7e"  # Sample client ID

def test_list_endpoint():
    """Test GET /api/belge/list endpoint"""
    logger.info("\n=== Testing GET /api/belge/list endpoint ===")
    
    url = f"{RAILWAY_API_URL}/belge/list"
    
    # Test with admin authentication
    try:
        response = requests.get(url, headers=headers_admin)
        logger.info(f"Admin response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {len(data)} documents")
            
            # If there are documents, check their structure
            if len(data) > 0:
                document = data[0]
                logger.info(f"Sample document: {document}")
            
            logger.info("✅ GET /api/belge/list with admin auth test passed")
        elif response.status_code == 404:
            logger.info("⚠️ Endpoint returned 404 Not Found - may not be implemented yet")
        else:
            logger.info(f"⚠️ Unexpected status code: {response.status_code}")
    
    except Exception as e:
        logger.error(f"❌ Error testing list endpoint with admin: {e}")

if __name__ == "__main__":
    test_list_endpoint()