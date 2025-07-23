#!/usr/bin/env python3
"""
JOSE Library JWT Fix Test - Focused on Training Endpoints
Testing the specific endpoints mentioned in the review request
"""

import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend .env
BACKEND_URL = "https://694e2ff8-2569-4688-9c7a-7c3b6cd0dd67.preview.emergentagent.com"

# Test tokens - these will likely fail but we want to see the specific error messages
TEST_TOKENS = {
    "valid_format": "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovLzUzOTgwY2E5LWMzMDQtNDMzZS1hYjYyLTFjMzdhNzE3NmRkNS5wcmV2aWV3LmVtZXJnZW50YWdlbnQuY29tIiwiZXhwIjoxNzE5OTM2MTYwLCJpYXQiOjE3MTk5MzI1NjAsImlzcyI6Imh0dHBzOi8vYWRhcHRpbmctZWZ0LTYuY2xlcmsuYWNjb3VudHMuZGV2IiwibmJmIjoxNzE5OTMyNTUwLCJzdWIiOiJ1c2VyXzJYcFRBT2VBU1RROWpodFBxWnBIaUNGdW8iLCJlbWFpbCI6InRlc3RAdGVzdC5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIn0.fake_signature",
    "invalid_format": "invalid.token.format"
}

def test_endpoint(method, endpoint, token=None, data=None):
    """Test an endpoint with given method and token"""
    url = f"{BACKEND_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            headers["Content-Type"] = "application/json"
            response = requests.put(url, headers=headers, json=data, timeout=10)
        else:
            logger.error(f"Unsupported method: {method}")
            return None
            
        return {
            "status_code": response.status_code,
            "response": response.text,
            "headers": dict(response.headers)
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return {
            "status_code": 0,
            "response": f"Request failed: {str(e)}",
            "headers": {}
        }

def main():
    """Main test function"""
    logger.info("🔥 JOSE LIBRARY FIX TEST!")
    logger.info("Testing JWT authentication fix using python-jose instead of PyJWKClient")
    logger.info("=" * 80)
    
    # Test 1: Health check
    logger.info("\n1️⃣ BACKEND HEALTH CHECK")
    result = test_endpoint("GET", "/api/health")
    if result and result['status_code'] == 200:
        logger.info("✅ Backend is accessible")
    else:
        logger.error("❌ Backend health check failed")
        return
    
    # Test 2: Main training endpoints from review request
    logger.info("\n2️⃣ MAIN TRAINING ENDPOINTS TEST")
    logger.info("Testing the 3 endpoints mentioned in review request:")
    
    test_training_id = "test-training-123"
    
    endpoints_to_test = [
        ("PUT", f"/api/trainings/{test_training_id}", "Main issue - training editing"),
        ("GET", "/api/trainings", "Training list"),
        ("POST", "/api/trainings", "Training creation")
    ]
    
    # Test without authentication first
    logger.info("\n🔒 Testing WITHOUT Authentication:")
    for method, endpoint, description in endpoints_to_test:
        logger.info(f"\n📍 {method} {endpoint} - {description}")
        
        test_data = None
        if method in ["POST", "PUT"]:
            test_data = {
                "name": "Test Eğitim",
                "subject": "Test Konusu",
                "participant_count": 10,
                "trainer": "Test Eğitmen",
                "training_date": "2025-01-25T10:00:00Z",
                "description": "Test açıklama",
                "client_id": "test-client-id"
            }
        
        result = test_endpoint(method, endpoint, data=test_data)
        if result:
            logger.info(f"   Status: {result['status_code']}")
            if result['status_code'] == 403:
                logger.info("   ✅ Properly requires authentication (403 Forbidden)")
            elif result['status_code'] == 401:
                logger.info("   ✅ Properly requires authentication (401 Unauthorized)")
            elif result['status_code'] == 404:
                logger.warning("   ⚠️ Endpoint not found (404) - might not be registered")
            elif result['status_code'] == 405:
                logger.warning("   ⚠️ Method not allowed (405) - endpoint exists but method wrong")
            else:
                logger.info(f"   ℹ️ Response: {result['response'][:100]}...")
    
    # Test with invalid tokens to check JWT error messages
    logger.info("\n🔑 Testing WITH Invalid Tokens:")
    logger.info("Checking if we still get 'could not get signing key' errors...")
    
    for method, endpoint, description in endpoints_to_test:
        logger.info(f"\n📍 {method} {endpoint} - {description}")
        
        test_data = None
        if method in ["POST", "PUT"]:
            test_data = {
                "name": "Test Eğitim",
                "subject": "Test Konusu",
                "participant_count": 10,
                "trainer": "Test Eğitmen",
                "training_date": "2025-01-25T10:00:00Z",
                "description": "Test açıklama",
                "client_id": "test-client-id"
            }
        
        # Test with valid format token (but expired/invalid)
        result = test_endpoint(method, endpoint, token=TEST_TOKENS["valid_format"], data=test_data)
        if result:
            logger.info(f"   Status: {result['status_code']}")
            
            if result['status_code'] == 401:
                response_text = result['response'].lower()
                if "could not get signing key" in response_text:
                    logger.error("   ❌ CRITICAL: Still getting 'could not get signing key' error!")
                    logger.error("   ❌ The JOSE library fix is NOT working!")
                    logger.info(f"   Error: {result['response']}")
                elif "invalid crypto padding" in response_text:
                    logger.error("   ❌ CRITICAL: Still getting 'Invalid crypto padding' error!")
                    logger.error("   ❌ The JOSE library fix is NOT working!")
                    logger.info(f"   Error: {result['response']}")
                else:
                    logger.info("   ✅ Different JWT error - JOSE library is working!")
                    logger.info(f"   New error: {result['response']}")
            elif result['status_code'] == 404:
                logger.warning("   ⚠️ Endpoint not found - can't test JWT fix")
            elif result['status_code'] == 405:
                logger.warning("   ⚠️ Method not allowed - endpoint exists but method issue")
            else:
                logger.info(f"   ℹ️ Unexpected status: {result['status_code']}")
                logger.info(f"   Response: {result['response'][:100]}...")
    
    # Test 3: Check JWKS accessibility
    logger.info("\n3️⃣ JWKS ENDPOINT TEST")
    jwks_url = "https://adapting-eft-6.clerk.accounts.dev/.well-known/jwks.json"
    
    try:
        response = requests.get(jwks_url, timeout=10)
        logger.info(f"JWKS Status: {response.status_code}")
        if response.status_code == 200:
            logger.info("✅ JWKS endpoint is accessible from test environment")
            jwks_data = response.json()
            logger.info(f"JWKS keys available: {len(jwks_data.get('keys', []))}")
        else:
            logger.error("❌ JWKS endpoint not accessible")
    except Exception as e:
        logger.error(f"❌ JWKS fetch failed: {str(e)}")
    
    # Test 4: Check if backend can access JWKS
    logger.info("\n4️⃣ BACKEND JWKS ACCESS TEST")
    logger.info("Testing if backend can fetch JWKS by triggering JWT validation...")
    
    # Try to trigger JWT validation with a properly formatted but invalid token
    result = test_endpoint("GET", "/api/trainings", token=TEST_TOKENS["valid_format"])
    if result and result['status_code'] == 401:
        response_text = result['response'].lower()
        if "could not fetch jwks" in response_text or "jwks fetch error" in response_text:
            logger.error("❌ Backend cannot access JWKS endpoint")
        elif "could not get signing key" in response_text:
            logger.error("❌ Old PyJWKClient error still occurring")
        else:
            logger.info("✅ Backend can access JWKS (getting proper JWT validation errors)")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("🏁 JOSE LIBRARY FIX TEST SUMMARY")
    logger.info("=" * 80)
    
    logger.info("\n🎯 KEY FINDINGS:")
    logger.info("1. Backend is accessible and responding")
    logger.info("2. Training endpoints authentication behavior checked")
    logger.info("3. JWT error message analysis completed")
    logger.info("4. JWKS accessibility verified")
    
    logger.info("\n✅ SUCCESS INDICATORS:")
    logger.info("- No 'could not get signing key' errors = JOSE fix working")
    logger.info("- No 'Invalid crypto padding' errors = Crypto issue resolved")
    logger.info("- Different JWT validation errors = New system active")
    
    logger.info("\n❌ FAILURE INDICATORS:")
    logger.info("- Still getting 'could not get signing key' = Fix not working")
    logger.info("- Still getting 'Invalid crypto padding' = Crypto issue persists")
    logger.info("- 404 errors on all endpoints = Deployment/routing issue")
    
    logger.info("\n🔧 IF FIX IS WORKING:")
    logger.info("- User should be able to edit trainings with valid tokens")
    logger.info("- 'bir kere kaydettikten sonra düzenleme yapamıyorum' issue resolved")

if __name__ == "__main__":
    main()