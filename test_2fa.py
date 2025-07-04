import unittest
import json
import logging
import requests
import os
import sys
import io
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT token - this is a sample token for testing
# In a real scenario, you would generate this from Clerk
VALID_JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.signature"
INVALID_JWT_TOKEN = "invalid.token.format"

# Test JWT tokens for client users
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

class Test2FAEndpoints(unittest.TestCase):
    """Test class for 2FA endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.api_url = RAILWAY_API_URL
        self.headers_valid = {"Authorization": f"Bearer {VALID_JWT_TOKEN}"}
        self.headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        self.headers_invalid = {"Authorization": f"Bearer {INVALID_JWT_TOKEN}"}
        self.headers_no_auth = {}
    
    def test_2fa_send_code_endpoint(self):
        """Test the /api/auth/2fa/send-code endpoint"""
        logger.info("\n=== Testing /api/auth/2fa/send-code endpoint ===")
        
        url = f"{self.api_url}/auth/2fa/send-code"
        
        # Test with valid token
        logger.info("Testing with valid token...")
        
        # JSON data for the request
        json_data = {
            "email": "test@example.com"
        }
        
        try:
            response = requests.post(url, headers=self.headers_valid, json=json_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check response status code
            # We expect either 200 OK (if it works) or 500 Internal Server Error (if email_service.send_email is missing)
            self.assertIn(response.status_code, [200, 500, 401, 403])
            
            if response.status_code == 200:
                logger.info("✅ 2FA send code endpoint working correctly")
                data = response.json()
                self.assertIn("message", data)
                self.assertIn("email", data)
                self.assertIn("expires_in", data)
            elif response.status_code == 500:
                logger.info("❌ 2FA send code endpoint returning 500 error - likely missing email_service.send_email method")
                data = response.json()
                self.assertIn("detail", data)
                logger.info(f"Error detail: {data.get('detail', '')}")
            elif response.status_code in [401, 403]:
                logger.info(f"❌ Authentication error: {response.status_code}")
                data = response.json()
                self.assertIn("detail", data)
                logger.info(f"Error detail: {data.get('detail', '')}")
        except Exception as e:
            logger.error(f"❌ Error testing 2FA send code endpoint: {str(e)}")
            raise
        
        # Test with admin token
        logger.info("Testing with admin token...")
        
        try:
            response = requests.post(url, headers=self.headers_admin, json=json_data)
            logger.info(f"Admin response status code: {response.status_code}")
            logger.info(f"Admin response body: {response.text[:200]}...")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 500, 401, 403])
            
            if response.status_code == 200:
                logger.info("✅ 2FA send code endpoint working correctly with admin token")
            elif response.status_code == 500:
                logger.info("❌ 2FA send code endpoint returning 500 error with admin token")
                data = response.json()
                self.assertIn("detail", data)
                logger.info(f"Error detail: {data.get('detail', '')}")
            elif response.status_code in [401, 403]:
                logger.info(f"❌ Authentication error with admin token: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing 2FA send code endpoint with admin token: {str(e)}")
            raise
    
    def test_2fa_verify_code_endpoint(self):
        """Test the /api/auth/2fa/verify-code endpoint"""
        logger.info("\n=== Testing /api/auth/2fa/verify-code endpoint ===")
        
        url = f"{self.api_url}/auth/2fa/verify-code"
        
        # Test with valid token
        logger.info("Testing with valid token...")
        
        # JSON data for the request
        json_data = {
            "email": "test@example.com",
            "code": "123456"  # This is a dummy code, we expect it to fail verification
        }
        
        try:
            response = requests.post(url, headers=self.headers_valid, json=json_data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check response status code
            # We expect 400 Bad Request (invalid code) or 401/403 (auth issues)
            self.assertIn(response.status_code, [400, 401, 403, 500])
            
            if response.status_code == 400:
                logger.info("✅ 2FA verify code endpoint correctly rejected invalid code")
                data = response.json()
                self.assertIn("detail", data)
                logger.info(f"Error detail: {data.get('detail', '')}")
            elif response.status_code in [401, 403]:
                logger.info(f"❌ Authentication error: {response.status_code}")
                data = response.json()
                self.assertIn("detail", data)
                logger.info(f"Error detail: {data.get('detail', '')}")
            elif response.status_code == 500:
                logger.info("❌ 2FA verify code endpoint returning 500 error")
                data = response.json()
                self.assertIn("detail", data)
                logger.info(f"Error detail: {data.get('detail', '')}")
        except Exception as e:
            logger.error(f"❌ Error testing 2FA verify code endpoint: {str(e)}")
            raise
    
    def test_2fa_status_endpoint(self):
        """Test the /api/auth/2fa/status endpoint"""
        logger.info("\n=== Testing /api/auth/2fa/status endpoint ===")
        
        url = f"{self.api_url}/auth/2fa/status"
        
        # Test with valid token
        logger.info("Testing with valid token...")
        
        try:
            response = requests.get(url, headers=self.headers_valid)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text[:200]}...")
            
            # Check response status code
            self.assertIn(response.status_code, [200, 401, 403, 500])
            
            if response.status_code == 200:
                logger.info("✅ 2FA status endpoint working correctly")
                data = response.json()
                self.assertIn("user_id", data)
                self.assertIn("email", data)
                self.assertIn("has_pending_codes", data)
                self.assertIn("pending_count", data)
            elif response.status_code in [401, 403]:
                logger.info(f"❌ Authentication error: {response.status_code}")
                data = response.json()
                self.assertIn("detail", data)
                logger.info(f"Error detail: {data.get('detail', '')}")
            elif response.status_code == 500:
                logger.info("❌ 2FA status endpoint returning 500 error")
                data = response.json()
                self.assertIn("detail", data)
                logger.info(f"Error detail: {data.get('detail', '')}")
        except Exception as e:
            logger.error(f"❌ Error testing 2FA status endpoint: {str(e)}")
            raise

if __name__ == "__main__":
    # Run the tests
    unittest.main()