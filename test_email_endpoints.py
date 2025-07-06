import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"
LOCAL_API_URL = "http://localhost:8001/api"

# Test JWT token for admin user
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"

def test_endpoint(url, headers=None, method="GET", data=None):
    """Test an API endpoint and return the response"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            logger.error(f"Unsupported method: {method}")
            return None
        
        logger.info(f"{method} {url} - Status code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                logger.info(f"Response: {json.dumps(data, indent=2)[:500]}...")
                return data
            except json.JSONDecodeError:
                logger.info(f"Response (not JSON): {response.text[:500]}...")
                return response.text
        else:
            logger.info(f"Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return None

def test_email_management_endpoints():
    """Test the email management endpoints"""
    logger.info("=== Testing Email Management Endpoints ===")
    
    # Headers for admin user
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test the email management endpoints
    endpoints = [
        "/email-management/clients-real",
        "/email-management/documents-real",
        "/email-management/trainings-real"
    ]
    
    # Test with Railway API URL
    logger.info("\n=== Testing with Railway API URL ===")
    for endpoint in endpoints:
        url = f"{RAILWAY_API_URL}{endpoint}"
        logger.info(f"\nTesting {url}")
        test_endpoint(url, headers)
    
    # Test with local API URL
    logger.info("\n=== Testing with Local API URL ===")
    for endpoint in endpoints:
        url = f"{LOCAL_API_URL}{endpoint}"
        logger.info(f"\nTesting {url}")
        test_endpoint(url, headers)

def test_regular_endpoints():
    """Test regular endpoints for comparison"""
    logger.info("\n=== Testing Regular Endpoints for Comparison ===")
    
    # Headers for admin user
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test regular endpoints
    endpoints = [
        "/clients",
        "/documents",
        "/trainings"
    ]
    
    # Test with Railway API URL
    logger.info("\n=== Testing with Railway API URL ===")
    for endpoint in endpoints:
        url = f"{RAILWAY_API_URL}{endpoint}"
        logger.info(f"\nTesting {url}")
        test_endpoint(url, headers)
    
    # Test with local API URL
    logger.info("\n=== Testing with Local API URL ===")
    for endpoint in endpoints:
        url = f"{LOCAL_API_URL}{endpoint}"
        logger.info(f"\nTesting {url}")
        test_endpoint(url, headers)

def test_health_endpoint():
    """Test the health endpoint"""
    logger.info("\n=== Testing Health Endpoint ===")
    
    # Test with Railway API URL
    url = f"{RAILWAY_API_URL}/health"
    logger.info(f"\nTesting {url}")
    test_endpoint(url)
    
    # Test with local API URL
    url = f"{LOCAL_API_URL}/health"
    logger.info(f"\nTesting {url}")
    test_endpoint(url)

def test_guest_engagement_endpoints():
    """Test guest engagement endpoints (should be public)"""
    logger.info("\n=== Testing Guest Engagement Endpoints ===")
    
    # Test eco-tips endpoint
    url = f"{RAILWAY_API_URL}/guest-engagement/eco-tips"
    logger.info(f"\nTesting {url}")
    test_endpoint(url)
    
    url = f"{LOCAL_API_URL}/guest-engagement/eco-tips"
    logger.info(f"\nTesting {url}")
    test_endpoint(url)

def test_supplier_endpoints():
    """Test supplier endpoints (categories and certifications should be public)"""
    logger.info("\n=== Testing Supplier Endpoints ===")
    
    # Test categories endpoint
    url = f"{RAILWAY_API_URL}/suppliers/categories/list"
    logger.info(f"\nTesting {url}")
    test_endpoint(url)
    
    url = f"{LOCAL_API_URL}/suppliers/categories/list"
    logger.info(f"\nTesting {url}")
    test_endpoint(url)
    
    # Test certifications endpoint
    url = f"{RAILWAY_API_URL}/suppliers/certifications/list"
    logger.info(f"\nTesting {url}")
    test_endpoint(url)
    
    url = f"{LOCAL_API_URL}/suppliers/certifications/list"
    logger.info(f"\nTesting {url}")
    test_endpoint(url)

def main():
    """Main function to run all tests"""
    logger.info("Starting API endpoint tests")
    
    # Test health endpoint
    test_health_endpoint()
    
    # Test public endpoints
    test_guest_engagement_endpoints()
    test_supplier_endpoints()
    
    # Test email management endpoints
    test_email_management_endpoints()
    
    # Test regular endpoints
    test_regular_endpoints()
    
    logger.info("API endpoint tests complete")

if __name__ == "__main__":
    main()