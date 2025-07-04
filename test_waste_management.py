import requests
import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "https://rota-crm-production.up.railway.app/api"

# Test JWT token - this is a sample token for testing
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
KAYA_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfS0FZQV9DTElFTlRfMDAxIiwiZW1haWwiOiJpbmZvQGtheWFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiS0FZQSBDbGllbnQifQ.signature"

# Headers for different user types
HEADERS_ADMIN = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
HEADERS_KAYA = {"Authorization": f"Bearer {KAYA_CLIENT_TOKEN}"}

# Test data for waste management
test_waste_data = {
    "year": 2025,
    "month": 6,
    "organic_waste": 50.5,
    "plastic_waste": 25.0,
    "glass_waste": 15.5,
    "paper_waste": 30.0,
    "metal_waste": 10.0,
    "electronic_waste": 5.0,
    "oil_waste": 5.0,
    "mixed_waste": 20.0,
    "client_id": "4d7d0100-bdb4-44a0-ac4e-125d3b77a2bb"  # Client ID from the test requirements
}

def test_create_waste_record():
    """Test POST /api/waste-management endpoint"""
    logger.info("\n=== Testing POST /api/waste-management endpoint ===")
    
    url = f"{BACKEND_URL}/waste-management"
    
    try:
        # Test with admin user and specific client_id
        logger.info("Testing with admin user and specific client_id...")
        response = requests.post(url, headers=HEADERS_ADMIN, json=test_waste_data)
        logger.info(f"Admin response status code: {response.status_code}")
        logger.info(f"Admin response body: {response.text}")
        
        # Check CORS headers
        logger.info(f"CORS headers: {response.headers.get('Access-Control-Allow-Origin', 'Not present')}")
        cors_headers_present = 'Access-Control-Allow-Origin' in response.headers
        
        admin_success = response.status_code in [200, 201, 400]  # 400 is acceptable if record already exists
        
        # Test with client user
        logger.info("Testing with client user...")
        client_waste_data = test_waste_data.copy()
        client_waste_data.pop("client_id", None)  # Client users don't need to specify client_id
        client_waste_data["month"] = 7  # Use a different month to avoid conflict
        
        response = requests.post(url, headers=HEADERS_KAYA, json=client_waste_data)
        logger.info(f"Client response status code: {response.status_code}")
        logger.info(f"Client response body: {response.text}")
        
        client_success = response.status_code in [200, 201, 400]  # 400 is acceptable if record already exists
        
        # Test authentication handling
        logger.info("Testing authentication handling...")
        
        # Test with invalid token
        headers_invalid = {"Authorization": "Bearer invalid.token.format"}
        response = requests.post(url, headers=headers_invalid, json=test_waste_data)
        logger.info(f"Invalid token response status code: {response.status_code}")
        
        invalid_token_success = response.status_code == 401  # Should get 401 Unauthorized
        
        # Test with no token
        response = requests.post(url, json=test_waste_data)
        logger.info(f"No token response status code: {response.status_code}")
        
        no_token_success = response.status_code == 403  # Should get 403 Not authenticated
        
        return admin_success and client_success and invalid_token_success and no_token_success and cors_headers_present
    except Exception as e:
        logger.error(f"Error testing POST /api/waste-management: {str(e)}")
        return False

def test_get_waste_records():
    """Test GET /api/waste-management endpoint"""
    logger.info("\n=== Testing GET /api/waste-management endpoint ===")
    
    url = f"{BACKEND_URL}/waste-management"
    
    try:
        # Test with admin user and specific client_id and year
        logger.info("Testing with admin user for specific client_id and year...")
        params = {
            "year": 2025,
            "client_id": "4d7d0100-bdb4-44a0-ac4e-125d3b77a2bb"
        }
        response = requests.get(url, headers=HEADERS_ADMIN, params=params)
        logger.info(f"Admin response status code: {response.status_code}")
        
        # Check CORS headers
        logger.info(f"CORS headers: {response.headers.get('Access-Control-Allow-Origin', 'Not present')}")
        cors_headers_present = 'Access-Control-Allow-Origin' in response.headers
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {len(data)} waste records for specific client_id and year")
            
            # Check if there are any records
            if len(data) > 0:
                logger.info(f"First record: {json.dumps(data[0], indent=2)}")
            else:
                logger.info("No waste records found for specific client_id and year")
        else:
            logger.info(f"Admin response body: {response.text}")
        
        admin_success = response.status_code == 200
        
        # Test with admin user (all records)
        logger.info("Testing with admin user (all records)...")
        response = requests.get(url, headers=HEADERS_ADMIN)
        logger.info(f"Admin response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {len(data)} waste records for admin")
            
            # Check if there are any records
            if len(data) > 0:
                logger.info(f"First record: {json.dumps(data[0], indent=2)}")
            else:
                logger.info("No waste records found for admin")
        else:
            logger.info(f"Admin response body: {response.text}")
        
        admin_all_success = response.status_code == 200
        
        # Test with client user
        logger.info("Testing with client user...")
        response = requests.get(url, headers=HEADERS_KAYA)
        logger.info(f"Client response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {len(data)} waste records for client")
            
            # Check if there are any records
            if len(data) > 0:
                logger.info(f"First record: {json.dumps(data[0], indent=2)}")
            else:
                logger.info("No waste records found for client")
        else:
            logger.info(f"Client response body: {response.text}")
        
        client_success = response.status_code == 200
        
        return admin_success and admin_all_success and client_success and cors_headers_present
    except Exception as e:
        logger.error(f"Error testing GET /api/waste-management: {str(e)}")
        return False

def test_get_waste_analytics():
    """Test GET /api/waste-management/analytics endpoint"""
    logger.info("\n=== Testing GET /api/waste-management/analytics endpoint ===")
    
    url = f"{BACKEND_URL}/waste-management/analytics"
    
    try:
        # Test with admin user and specific client_id and year
        logger.info("Testing with admin user for specific client_id and year...")
        params = {
            "year": 2025,
            "client_id": "4d7d0100-bdb4-44a0-ac4e-125d3b77a2bb"
        }
        response = requests.get(url, headers=HEADERS_ADMIN, params=params)
        logger.info(f"Admin response status code: {response.status_code}")
        
        # Check CORS headers
        logger.info(f"CORS headers: {response.headers.get('Access-Control-Allow-Origin', 'Not present')}")
        cors_headers_present = 'Access-Control-Allow-Origin' in response.headers
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response data keys: {data.keys()}")
            
            # Check if there are any records
            if data.get("yearly_totals") and data.get("monthly_data"):
                logger.info(f"Yearly totals: {json.dumps(data['yearly_totals'], indent=2)}")
                logger.info(f"Monthly data count: {len(data['monthly_data'])}")
            else:
                logger.info("No waste analytics data found for specific client_id and year")
        else:
            logger.info(f"Admin response body: {response.text}")
        
        admin_success = response.status_code == 200
        
        # Test with admin user (all records)
        logger.info("Testing with admin user (all records)...")
        response = requests.get(url, headers=HEADERS_ADMIN)
        logger.info(f"Admin response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response data keys: {data.keys()}")
            
            # Check if there are any records
            if data.get("yearly_totals") and data.get("monthly_data"):
                logger.info(f"Yearly totals: {json.dumps(data['yearly_totals'], indent=2)}")
                logger.info(f"Monthly data count: {len(data['monthly_data'])}")
            else:
                logger.info("No waste analytics data found for admin")
        else:
            logger.info(f"Admin response body: {response.text}")
        
        admin_all_success = response.status_code == 200
        
        # Test with client user
        logger.info("Testing with client user...")
        response = requests.get(url, headers=HEADERS_KAYA)
        logger.info(f"Client response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response data keys: {data.keys()}")
            
            # Check if there are any records
            if data.get("yearly_totals") and data.get("monthly_data"):
                logger.info(f"Yearly totals: {json.dumps(data['yearly_totals'], indent=2)}")
                logger.info(f"Monthly data count: {len(data['monthly_data'])}")
            else:
                logger.info("No waste analytics data found for client")
        else:
            logger.info(f"Client response body: {response.text}")
        
        client_success = response.status_code == 200
        
        return admin_success and admin_all_success and client_success and cors_headers_present
    except Exception as e:
        logger.error(f"Error testing GET /api/waste-management/analytics: {str(e)}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting waste management tests...")
    
    # Test creating a waste record
    create_result = test_create_waste_record()
    
    # Test getting waste records
    get_result = test_get_waste_records()
    
    # Test getting waste analytics
    analytics_result = test_get_waste_analytics()
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Create waste record: {'PASSED' if create_result else 'FAILED'}")
    logger.info(f"Get waste records: {'PASSED' if get_result else 'FAILED'}")
    logger.info(f"Get waste analytics: {'PASSED' if analytics_result else 'FAILED'}")
    
    # Test specific client_id
    logger.info("\n=== Testing Specific Client ID ===")
    logger.info(f"Client ID: 4d7d0100-bdb4-44a0-ac4e-125d3b77a2bb")
    logger.info(f"Year: 2025")
    
    # Test OPTIONS request for CORS preflight
    logger.info("\n=== Testing CORS Preflight Request ===")
    url = f"{BACKEND_URL}/waste-management"
    response = requests.options(url)
    logger.info(f"OPTIONS response status code: {response.status_code}")
    logger.info(f"OPTIONS response headers: {dict(response.headers)}")
    
    cors_success = (
        response.status_code == 200 and
        'Access-Control-Allow-Origin' in response.headers and
        'Access-Control-Allow-Methods' in response.headers and
        'Access-Control-Allow-Headers' in response.headers
    )
    
    logger.info(f"CORS preflight: {'PASSED' if cors_success else 'FAILED'}")
    
    if create_result and get_result and analytics_result and cors_success:
        logger.info("All tests PASSED")
        return 0
    else:
        logger.error("Some tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())