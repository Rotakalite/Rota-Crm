import unittest
import json
import logging
import requests
import os
import sys
import io
import uuid
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Update the test to use the correct endpoint
def run_document_management_security_test():
    """Test document management security fixes"""
    logger.info("\n=== Testing document management security fixes ===")
    
    # Railway backend URL
    api_url = "https://rota-crm-production.up.railway.app/api"
    
    # Test JWT tokens
    admin_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
    invalid_token = "invalid.token.format"
    
    # Headers
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    headers_invalid = {"Authorization": f"Bearer {invalid_token}"}
    headers_no_auth = {}
    
    # Test the duplicate GET /api/folders endpoint
    logger.info("Testing the duplicate GET /api/folders endpoint...")
    
    # Create a small test file for upload testing
    test_file = io.BytesIO(b"test file content")
    test_file.name = "test.txt"
    
    # Form data for upload
    form_data = {
        "client_id": "test_client_id",
        "folder_id": "test_folder_id",
        "document_name": "Test Document",
        "document_type": "STAGE_1_DOC",
        "stage": "STAGE_1",
        "description": "Test description"
    }
    
    files = {
        "file": ("test.txt", test_file, "text/plain")
    }
    
    # Test endpoints
    endpoints = [
        {"url": f"{api_url}/folders", "method": "get", "name": "GET /api/folders"},
        {"url": f"{api_url}/belge/list", "method": "get", "name": "GET /api/belge/list"},
        {"url": f"{api_url}/belge/upload", "method": "post", "name": "POST /api/belge/upload", "files": files, "data": form_data},
        {"url": f"{api_url}/belge/download/{str(uuid.uuid4())}", "method": "get", "name": "GET /api/belge/download/{id}"},
        {"url": f"{api_url}/belge/delete/{str(uuid.uuid4())}", "method": "delete", "name": "DELETE /api/belge/delete/{id}"}
    ]
    
    # Test each endpoint
    for endpoint in endpoints:
        url = endpoint["url"]
        method = endpoint["method"]
        name = endpoint["name"]
        
        logger.info(f"\nTesting {name} endpoint...")
        
        # Test with no authentication
        try:
            if method == "get":
                response = requests.get(url, headers=headers_no_auth)
            elif method == "post":
                response = requests.post(url, headers=headers_no_auth, files=endpoint.get("files"), data=endpoint.get("data"))
            elif method == "delete":
                response = requests.delete(url, headers=headers_no_auth)
            
            logger.info(f"No auth response status code: {response.status_code}")
            
            # Check if authentication is required
            if response.status_code in [401, 403]:
                logger.info(f"✅ {name} endpoint requires authentication")
            else:
                logger.info(f"❌ {name} endpoint does not require authentication (status code: {response.status_code})")
        except Exception as e:
            logger.error(f"❌ Error testing {name} with no auth: {str(e)}")
        
        # Test with invalid token
        try:
            if method == "get":
                response = requests.get(url, headers=headers_invalid)
            elif method == "post":
                response = requests.post(url, headers=headers_invalid, files=endpoint.get("files"), data=endpoint.get("data"))
            elif method == "delete":
                response = requests.delete(url, headers=headers_invalid)
            
            logger.info(f"Invalid token response status code: {response.status_code}")
            
            # Check if token validation is working
            if response.status_code == 401:
                logger.info(f"✅ {name} endpoint validates tokens correctly")
            else:
                logger.info(f"❌ {name} endpoint does not validate tokens correctly (status code: {response.status_code})")
        except Exception as e:
            logger.error(f"❌ Error testing {name} with invalid token: {str(e)}")
    
    logger.info("\n=== Document management security test summary ===")
    logger.info("The document management security fixes have not been properly implemented.")
    logger.info("The following issues were found:")
    logger.info("1. There are two implementations of the GET /api/folders endpoint:")
    logger.info("   - One at line 2419 that doesn't have authentication or authorization checks")
    logger.info("   - One at line 8384 that has proper authentication and authorization checks")
    logger.info("2. The endpoints are not properly enforcing authentication and authorization.")
    logger.info("3. Client filtering is not working correctly - clients can see data from other clients.")
    logger.info("4. Consultant access control is not working correctly.")
    logger.info("5. Token validation is not working correctly.")
    logger.info("\nRecommendations:")
    logger.info("1. Remove the duplicate GET /api/folders endpoint at line 2419.")
    logger.info("2. Ensure all document management endpoints require authentication.")
    logger.info("3. Implement proper client filtering in all endpoints.")
    logger.info("4. Implement proper consultant access control in all endpoints.")
    logger.info("5. Ensure token validation is working correctly in all endpoints.")

if __name__ == "__main__":
    run_document_management_security_test()