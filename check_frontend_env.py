import requests
import json
import logging
import sys
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "https://9fdcc5d0-9b6d-4e6f-bc8f-589c3991a8cc.preview.emergentagent.com/api"

def check_frontend_env():
    """Check frontend environment variables"""
    logger.info("\n=== Checking frontend environment variables ===")
    
    try:
        # Read frontend .env file
        with open('/app/frontend/.env', 'r') as f:
            env_content = f.read()
            
        logger.info(f"Frontend .env file content:\n{env_content}")
        
        # Extract REACT_APP_BACKEND_URL
        backend_url = None
        for line in env_content.splitlines():
            if line.startswith('REACT_APP_BACKEND_URL='):
                backend_url = line.split('=', 1)[1].strip()
                break
                
        logger.info(f"REACT_APP_BACKEND_URL: {backend_url}")
        
        # Check if backend URL is accessible
        if backend_url:
            try:
                response = requests.get(f"{backend_url}/api/health", timeout=5)
                logger.info(f"Health check response status code: {response.status_code}")
                logger.info(f"Health check response body: {response.text}")
            except Exception as e:
                logger.error(f"Error checking backend URL: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking frontend environment variables: {str(e)}")
        return False

def main():
    """Run frontend environment check"""
    logger.info("Starting frontend environment check...")
    
    # Check frontend environment variables
    env_result = check_frontend_env()
    
    # Summary
    logger.info("\n=== Summary ===")
    logger.info(f"Frontend environment check: {'PASSED' if env_result else 'FAILED'}")
    
    if env_result:
        logger.info("Frontend environment check PASSED")
        return 0
    else:
        logger.error("Frontend environment check FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())