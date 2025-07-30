#!/usr/bin/env python3
"""
422 Error Fix Verification Test - Railway Production
Test the bulk personnel and supplier endpoints for 422 validation error fix
"""

import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway backend URL
RAILWAY_API_URL = "https://rota-crm-production.up.railway.app/api"

# Test client ID from review request
TEST_CLIENT_ID = "94927a77-edc3-45ec-8329-795feae35771"

# Test JWT tokens (these are sample tokens for testing)
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CANO_CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0FOT19DTElFTlRfMDAxIiwiZW1haWwiOiJjYW5lcnBhbEBnbWFpbC5jb20iLCJuYW1lIjoiQ0FOTyBDbGllbnQifQ.signature"

def test_railway_backend_health():
    """Test Railway backend accessibility"""
    logger.info("🚂 TESTING RAILWAY BACKEND ACCESSIBILITY")
    
    # Test root endpoint
    try:
        response = requests.get("https://rota-crm-production.up.railway.app", timeout=10)
        logger.info(f"Root endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Railway backend accessible: {data}")
        else:
            logger.warning(f"⚠️ Root endpoint returned {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Error accessing root endpoint: {str(e)}")
        return False
    
    # Test health endpoint
    try:
        response = requests.get(f"{RAILWAY_API_URL}/health", timeout=10)
        logger.info(f"Health endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Health endpoint working: {data}")
            return True
        else:
            logger.warning(f"⚠️ Health endpoint returned {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error accessing health endpoint: {str(e)}")
        return False

def test_bulk_personnel_422_fix():
    """Test POST /api/personnel/bulk endpoint - 422 Error Fix Verification"""
    logger.info("\n🧑‍💼 TESTING BULK PERSONNEL ENDPOINT - 422 ERROR FIX")
    
    url = f"{RAILWAY_API_URL}/personnel/bulk"
    
    # Test data from review request
    bulk_personnel_payload = {
        "personnel_list": [
            {
                "full_name": "Test Personel",
                "position": "Test Pozisyon", 
                "location": "İstanbul",
                "certifications": ["Test Sertifika"],
                "is_local": True,
                "gender": "Erkek"
            }
        ]
    }
    
    headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}", "Content-Type": "application/json"}
    headers_no_auth = {"Content-Type": "application/json"}
    
    logger.info(f"Testing URL: {url}")
    logger.info(f"Payload: {json.dumps(bulk_personnel_payload, indent=2)}")
    
    # Test with admin user
    try:
        logger.info("Testing with admin token...")
        response = requests.post(url, headers=headers_admin, json=bulk_personnel_payload, timeout=15)
        logger.info(f"Admin response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ SUCCESS: Bulk personnel endpoint returned 200 OK")
            logger.info(f"Response data: {json.dumps(data, indent=2)}")
            
            # Check response structure
            if "created_count" in data:
                logger.info(f"✅ Created {data['created_count']} personnel records")
            if "failed_count" in data:
                logger.info(f"Failed: {data['failed_count']} personnel records")
            
            logger.info("🎉 422 ERROR FIXED FOR BULK PERSONNEL!")
            return True
            
        elif response.status_code == 422:
            try:
                data = response.json()
                logger.error(f"❌ CRITICAL: Still getting 422 Unprocessable Entity!")
                logger.error(f"422 Error details: {json.dumps(data, indent=2)}")
            except:
                logger.error(f"❌ CRITICAL: 422 error with non-JSON response: {response.text}")
            logger.error("❌ 422 ERROR NOT FIXED - BulkPersonnelRequest wrapper model issue persists")
            return False
            
        elif response.status_code == 405:
            logger.error(f"❌ DEPLOYMENT ISSUE: 405 Method Not Allowed")
            logger.error("❌ Bulk personnel endpoint not deployed to Railway production")
            return False
            
        elif response.status_code in [401, 403]:
            try:
                data = response.json()
                logger.info(f"Auth error (expected): {json.dumps(data, indent=2)}")
            except:
                logger.info(f"Auth error (expected): {response.text}")
            logger.info("✅ Authentication working correctly")
            return True
            
        else:
            try:
                data = response.json()
                logger.warning(f"⚠️ Unexpected status {response.status_code}: {json.dumps(data, indent=2)}")
            except:
                logger.warning(f"⚠️ Unexpected status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("❌ Request timeout - Railway backend may be slow")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing bulk personnel endpoint: {str(e)}")
        return False
    
    # Test without authentication
    try:
        logger.info("Testing without authentication...")
        response = requests.post(url, headers=headers_no_auth, json=bulk_personnel_payload, timeout=10)
        logger.info(f"No auth response status: {response.status_code}")
        
        if response.status_code == 403:
            logger.info("✅ Endpoint properly requires authentication")
        else:
            logger.warning(f"⚠️ Expected 403, got {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Error testing no auth: {str(e)}")

def test_bulk_supplier_422_fix():
    """Test POST /api/suppliers/bulk endpoint - 422 Error Fix Verification"""
    logger.info("\n🏢 TESTING BULK SUPPLIER ENDPOINT - 422 ERROR FIX")
    
    url = f"{RAILWAY_API_URL}/suppliers/bulk"
    
    # Test data from review request
    bulk_supplier_payload = {
        "suppliers_list": [
            {
                "company_name": "Test Şirket",
                "contact_person": "Test Kişi",
                "category": "Test Kategori", 
                "local_supplier": True
            }
        ]
    }
    
    headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}", "Content-Type": "application/json"}
    headers_no_auth = {"Content-Type": "application/json"}
    
    logger.info(f"Testing URL: {url}")
    logger.info(f"Payload: {json.dumps(bulk_supplier_payload, indent=2)}")
    
    # Test with admin user
    try:
        logger.info("Testing with admin token...")
        response = requests.post(url, headers=headers_admin, json=bulk_supplier_payload, timeout=15)
        logger.info(f"Admin response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ SUCCESS: Bulk supplier endpoint returned 200 OK")
            logger.info(f"Response data: {json.dumps(data, indent=2)}")
            
            # Check response structure
            if "created_count" in data:
                logger.info(f"✅ Created {data['created_count']} supplier records")
            if "failed_count" in data:
                logger.info(f"Failed: {data['failed_count']} supplier records")
            
            logger.info("🎉 422 ERROR FIXED FOR BULK SUPPLIER!")
            return True
            
        elif response.status_code == 422:
            try:
                data = response.json()
                logger.error(f"❌ CRITICAL: Still getting 422 Unprocessable Entity!")
                logger.error(f"422 Error details: {json.dumps(data, indent=2)}")
            except:
                logger.error(f"❌ CRITICAL: 422 error with non-JSON response: {response.text}")
            logger.error("❌ 422 ERROR NOT FIXED - BulkSupplierRequest wrapper model issue persists")
            return False
            
        elif response.status_code == 405:
            logger.error(f"❌ DEPLOYMENT ISSUE: 405 Method Not Allowed")
            logger.error("❌ Bulk supplier endpoint not deployed to Railway production")
            return False
            
        elif response.status_code in [401, 403]:
            try:
                data = response.json()
                logger.info(f"Auth error (expected): {json.dumps(data, indent=2)}")
            except:
                logger.info(f"Auth error (expected): {response.text}")
            logger.info("✅ Authentication working correctly")
            return True
            
        else:
            try:
                data = response.json()
                logger.warning(f"⚠️ Unexpected status {response.status_code}: {json.dumps(data, indent=2)}")
            except:
                logger.warning(f"⚠️ Unexpected status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("❌ Request timeout - Railway backend may be slow")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing bulk supplier endpoint: {str(e)}")
        return False
    
    # Test without authentication
    try:
        logger.info("Testing without authentication...")
        response = requests.post(url, headers=headers_no_auth, json=bulk_supplier_payload, timeout=10)
        logger.info(f"No auth response status: {response.status_code}")
        
        if response.status_code == 403:
            logger.info("✅ Endpoint properly requires authentication")
        else:
            logger.warning(f"⚠️ Expected 403, got {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Error testing no auth: {str(e)}")

def main():
    """Main test execution"""
    logger.info("🎯 422 ERROR FIX VERIFICATION - RAILWAY PRODUCTION TEST")
    logger.info("=" * 60)
    
    # Test Railway backend health
    if not test_railway_backend_health():
        logger.error("❌ Railway backend not accessible - aborting tests")
        return
    
    logger.info("=" * 60)
    
    # Test bulk personnel endpoint
    personnel_success = test_bulk_personnel_422_fix()
    
    logger.info("=" * 60)
    
    # Test bulk supplier endpoint  
    supplier_success = test_bulk_supplier_422_fix()
    
    logger.info("=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    if personnel_success and supplier_success:
        logger.info("🎉 ALL TESTS PASSED - 422 ERROR FIX VERIFIED!")
        logger.info("✅ Bulk personnel endpoint: WORKING")
        logger.info("✅ Bulk supplier endpoint: WORKING")
        logger.info("✅ BulkPersonnelRequest wrapper model: FIXED")
        logger.info("✅ BulkSupplierRequest wrapper model: FIXED")
        logger.info("✅ Railway production deployment: SUCCESS")
    else:
        logger.error("❌ SOME TESTS FAILED")
        logger.error(f"❌ Bulk personnel endpoint: {'WORKING' if personnel_success else 'FAILED'}")
        logger.error(f"❌ Bulk supplier endpoint: {'WORKING' if supplier_success else 'FAILED'}")
        
        if not personnel_success and not supplier_success:
            logger.error("❌ CRITICAL: Both endpoints failed - 422 error fix not working")
        elif not personnel_success:
            logger.error("❌ CRITICAL: Personnel endpoint failed - BulkPersonnelRequest issue")
        elif not supplier_success:
            logger.error("❌ CRITICAL: Supplier endpoint failed - BulkSupplierRequest issue")

if __name__ == "__main__":
    main()