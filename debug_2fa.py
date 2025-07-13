#!/usr/bin/env python3
"""
Direct 2FA Database Testing
Tests the 2FA system by directly checking the database and API responses
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('/app/backend/.env')

# Configuration
BACKEND_URL = "https://rota-crm-production.up.railway.app"
API_BASE_URL = f"{BACKEND_URL}/api"

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'rotacrm')

def test_2fa_implementation():
    """Test the actual 2FA implementation"""
    logger.info("🔍 Testing 2FA implementation...")
    
    # Test 1: Send code
    logger.info("📤 Testing send-code endpoint...")
    response = requests.post(
        f"{API_BASE_URL}/auth/2fa/send-code",
        json={"email": "test@example.com"},
        headers={'Content-Type': 'application/json'}
    )
    logger.info(f"Send-code response: {response.status_code} - {response.text}")
    
    # Test 2: Verify code
    logger.info("🔍 Testing verify-code endpoint...")
    response = requests.post(
        f"{API_BASE_URL}/auth/2fa/verify-code",
        json={"email": "test@example.com", "code": "123456"},
        headers={'Content-Type': 'application/json'}
    )
    logger.info(f"Verify-code response: {response.status_code} - {response.text}")
    
    # Test 3: Status
    logger.info("📊 Testing status endpoint...")
    response = requests.get(
        f"{API_BASE_URL}/auth/2fa/status",
        params={"user_email": "test@example.com"}
    )
    logger.info(f"Status response: {response.status_code} - {response.text}")
    
    # Test 4: Check database
    logger.info("🗄️ Checking database...")
    try:
        mongo_client = MongoClient(MONGO_URL)
        db = mongo_client[DB_NAME]
        
        # Check if verification_codes collection exists
        collections = db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        if 'verification_codes' in collections:
            codes = list(db.verification_codes.find())
            logger.info(f"Verification codes in database: {len(codes)}")
            for code in codes:
                logger.info(f"Code: {code}")
        else:
            logger.warning("verification_codes collection does not exist")
            
    except Exception as e:
        logger.error(f"Database error: {e}")

def test_different_endpoints():
    """Test if there are different 2FA endpoints"""
    logger.info("🔍 Testing different possible 2FA endpoints...")
    
    endpoints_to_test = [
        "/auth/2fa/send-code",
        "/2fa/send-code", 
        "/send-2fa-code",
        "/auth/send-code",
        "/auth/2fa/verify-code",
        "/2fa/verify-code",
        "/verify-2fa-code", 
        "/auth/verify-code"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.post(
                f"{API_BASE_URL}{endpoint}",
                json={"email": "test@example.com"},
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            logger.info(f"{endpoint}: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            logger.info(f"{endpoint}: ERROR - {str(e)[:50]}")

def check_server_logs():
    """Check if we can get any server information"""
    logger.info("🔍 Checking server information...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        logger.info(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        logger.error(f"Health check error: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting 2FA implementation investigation...")
    
    check_server_logs()
    test_2fa_implementation()
    test_different_endpoints()