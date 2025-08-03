import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "https://59ac40e0-967c-4254-8b25-c980adb51f08.preview.emergentagent.com"

def test_api_router_registration():
    """Test if the API router is properly registered"""
    logger.info("Testing API router registration...")
    
    # Test a known working endpoint
    url = f"{BACKEND_URL}/api/health"
    
    try:
        response = requests.get(url)
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ API router is properly registered")
            logger.info(f"Response data: {response.json()}")
            return True
        else:
            logger.error(f"❌ API router registration test failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing API router registration: {str(e)}")
        return False

def test_email_management_endpoints():
    """Test the email management endpoints"""
    logger.info("Testing email management endpoints...")
    
    # Test the email management endpoints
    endpoints = [
        "/api/email-management/clients-real",
        "/api/email-management/documents-real",
        "/api/email-management/trainings-real"
    ]
    
    for endpoint in endpoints:
        url = f"{BACKEND_URL}{endpoint}"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code for {endpoint}: {response.status_code}")
            
            if response.status_code == 404:
                logger.error(f"❌ Endpoint {endpoint} returned 404 Not Found")
            elif response.status_code == 401:
                logger.info(f"✅ Endpoint {endpoint} requires authentication (401 Unauthorized)")
            else:
                logger.info(f"✅ Endpoint {endpoint} returned status code: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing endpoint {endpoint}: {str(e)}")

def test_all_api_endpoints():
    """Test all API endpoints to find working ones"""
    logger.info("Testing all API endpoints...")
    
    # Test a variety of endpoints
    endpoints = [
        "/api/health",
        "/api/clients",
        "/api/documents",
        "/api/trainings",
        "/api/suppliers/categories/list",
        "/api/suppliers/certifications/list",
        "/api/guest-engagement/eco-tips",
        "/api/guest-engagement/leaderboard",
        "/api/guest-engagement",
        "/api/auth/register",
        "/api/email-management/clients-real",
        "/api/email-management/documents-real",
        "/api/email-management/trainings-real"
    ]
    
    working_endpoints = []
    not_found_endpoints = []
    auth_required_endpoints = []
    
    for endpoint in endpoints:
        url = f"{BACKEND_URL}{endpoint}"
        
        try:
            response = requests.get(url)
            logger.info(f"Response status code for {endpoint}: {response.status_code}")
            
            if response.status_code == 404:
                not_found_endpoints.append(endpoint)
            elif response.status_code == 401:
                auth_required_endpoints.append(endpoint)
            else:
                working_endpoints.append(endpoint)
        except Exception as e:
            logger.error(f"❌ Error testing endpoint {endpoint}: {str(e)}")
    
    logger.info(f"Working endpoints: {working_endpoints}")
    logger.info(f"Endpoints requiring authentication: {auth_required_endpoints}")
    logger.info(f"Not found endpoints: {not_found_endpoints}")

if __name__ == "__main__":
    logger.info("Starting API router and endpoint tests...")
    
    # Test API router registration
    api_router_registered = test_api_router_registration()
    
    if api_router_registered:
        # Test email management endpoints
        test_email_management_endpoints()
        
        # Test all API endpoints
        test_all_api_endpoints()
    else:
        logger.error("❌ API router is not properly registered. Skipping endpoint tests.")
    
    logger.info("API router and endpoint tests completed.")