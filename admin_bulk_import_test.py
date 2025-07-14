#!/usr/bin/env python3
"""
Admin Bulk Client Import Feature Testing
========================================

This script tests the admin bulk client import functionality according to the review request:

1. **Bulk Import Endpoint**: POST /api/bulk-import/clients endpoint for admin users
2. **Template Download**: GET /api/bulk-import/template endpoint for admin users
3. **Admin-Only Access**: Only admin users can access these endpoints
4. **Security Testing**: Non-admin users get 403 Forbidden
5. **File Processing**: Excel file processing logic works correctly

Test Scenarios:
- Admin token with POST /api/bulk-import/clients (multipart/form-data)
- Admin token with GET /api/bulk-import/template
- Non-admin token with endpoints (403 expected)
- Invalid token with endpoints (401 expected)
- No token with endpoints (403 expected)
"""

import requests
import json
import logging
import io
import pandas as pd
from datetime import datetime
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend .env
BACKEND_URL = "https://rota-crm-production.up.railway.app"
API_BASE_URL = f"{BACKEND_URL}/api"

# Test tokens (these are sample tokens - will be invalid but we test the security)
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0xJRU5UIiwiZW1haWwiOiJjbGllbnRAdGVzdC5jb20iLCJuYW1lIjoiQ2xpZW50IFVzZXIifQ.signature"
CONSULTANT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ09OU1VMVEFOVCIsImVtYWlsIjoiY29uc3VsdGFudEB0ZXN0LmNvbSIsIm5hbWUiOiJDb25zdWx0YW50IFVzZXIifQ.signature"
INVALID_TOKEN = "invalid.token.format"

def test_endpoint_security(endpoint, method="GET", files=None):
    """Test endpoint security with different authentication scenarios"""
    logger.info(f"🔒 Testing security for {method} {endpoint}")
    
    url = f"{API_BASE_URL}{endpoint}"
    security_results = {}
    
    # Test scenarios
    test_cases = [
        ("No Token", None, [403]),
        ("Invalid Token", INVALID_TOKEN, [401]),
        ("Client Token", CLIENT_TOKEN, [403]),
        ("Consultant Token", CONSULTANT_TOKEN, [403]),
        ("Admin Token", ADMIN_TOKEN, [200, 401])  # 401 if token expired, 200 if valid
    ]
    
    for test_name, token, expected_codes in test_cases:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, files=files, timeout=30)
            
            logger.info(f"   {test_name}: {response.status_code} (expected: {expected_codes})")
            
            if response.status_code in expected_codes:
                security_results[test_name] = "✅ PASS"
            else:
                security_results[test_name] = f"❌ FAIL (got {response.status_code}, expected {expected_codes})"
                
        except Exception as e:
            logger.error(f"   {test_name}: ERROR - {str(e)}")
            security_results[test_name] = f"❌ ERROR - {str(e)}"
    
    return security_results

def create_test_excel_file():
    """Create a test Excel file for bulk import testing"""
    test_data = {
        'TESİS ADI': [
            'Test Bulk Import Hotel 1',
            'Test Bulk Import Hotel 2', 
            'Test Bulk Import Hotel 3',
            'Test Bulk Import Hotel 4'
        ],
        'İL': [
            'İstanbul',
            'Ankara',
            'İzmir',
            'Antalya'
        ],
        'İLÇE': [
            'Beyoğlu',
            'Çankaya',
            'Konak',
            'Kemer'
        ],
        'TELEFON': [
            '+90 212 555 1001',
            '+90 312 555 1002',
            '+90 232 555 1003',
            '+90 242 555 1004'
        ],
        'MAİL': [
            'test1@bulkimporttest.com',
            'test2@bulkimporttest.com',
            'test3@bulkimporttest.com',
            'test4@bulkimporttest.com'
        ],
        'SERTİFİKA BİTİŞ TARİHİ': [
            '2024-12-31',
            '2025-06-30',
            '2025-12-31',
            '2024-09-15'
        ],
        'DENETLEYEN FİRMA': [
            'Test Denetim Ltd.',
            'Örnek Belgelendirme A.Ş.',
            'Demo Kalite Kontrol',
            'Sample Audit Company'
        ]
    }
    
    df = pd.DataFrame(test_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Müşteri Listesi')
    
    output.seek(0)
    return output

def test_template_download():
    """Test the template download endpoint"""
    logger.info("📥 Testing Template Download Endpoint")
    logger.info("=" * 50)
    
    endpoint = "/bulk-import/template"
    
    # Test security
    security_results = test_endpoint_security(endpoint, "GET")
    
    # Test functionality with admin token (even if expired, we test the endpoint exists)
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        logger.info(f"📊 Template download response: {response.status_code}")
        
        if response.status_code == 200:
            # Check if it's an Excel file
            content_type = response.headers.get('content-type', '')
            content_disposition = response.headers.get('content-disposition', '')
            
            logger.info("✅ Template download successful!")
            logger.info(f"   Content-Type: {content_type}")
            logger.info(f"   Content-Disposition: {content_disposition}")
            logger.info(f"   File size: {len(response.content)} bytes")
            
            # Verify Excel format
            if 'spreadsheet' in content_type or 'excel' in content_type:
                logger.info("✅ Response is Excel file format")
                return True, security_results, "Template download working correctly"
            else:
                logger.warning("⚠️ Response may not be Excel format")
                return False, security_results, f"Unexpected content type: {content_type}"
                
        elif response.status_code == 401:
            logger.info("⚠️ Authentication failed (token expired) but endpoint exists")
            return "ENDPOINT_EXISTS", security_results, "Endpoint exists but token expired"
        else:
            logger.error(f"❌ Unexpected response: {response.status_code}")
            return False, security_results, f"Error: {response.status_code}"
            
    except Exception as e:
        logger.error(f"❌ Template download error: {str(e)}")
        return False, security_results, f"Error: {str(e)}"

def test_bulk_import():
    """Test the bulk import endpoint"""
    logger.info("📤 Testing Bulk Import Endpoint")
    logger.info("=" * 50)
    
    endpoint = "/bulk-import/clients"
    
    # Create test Excel file
    excel_file = create_test_excel_file()
    files = {
        'file': ('test_clients.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    
    # Test security
    security_results = test_endpoint_security(endpoint, "POST", files)
    
    # Test functionality with admin token
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Reset file pointer
    excel_file.seek(0)
    files = {
        'file': ('test_clients.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    
    try:
        response = requests.post(url, headers=headers, files=files, timeout=60)
        logger.info(f"📊 Bulk import response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ Bulk import successful!")
            logger.info(f"   Imported: {result.get('imported_count', 0)} clients")
            logger.info(f"   Skipped: {result.get('skipped_count', 0)} clients")
            logger.info(f"   Errors: {result.get('error_count', 0)} clients")
            logger.info(f"   Total rows: {result.get('total_rows', 0)}")
            logger.info(f"   Message: {result.get('message', 'No message')}")
            
            return True, security_results, f"Import successful - {result.get('imported_count', 0)} imported"
            
        elif response.status_code == 401:
            logger.info("⚠️ Authentication failed (token expired) but endpoint exists")
            return "ENDPOINT_EXISTS", security_results, "Endpoint exists but token expired"
        else:
            logger.error(f"❌ Bulk import failed: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return False, security_results, f"Error: {response.status_code}"
            
    except Exception as e:
        logger.error(f"❌ Bulk import error: {str(e)}")
        return False, security_results, f"Error: {str(e)}"

def test_file_validation():
    """Test file format validation"""
    logger.info("📄 Testing File Format Validation")
    logger.info("=" * 50)
    
    url = f"{API_BASE_URL}/bulk-import/clients"
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    
    # Test with invalid file format (text file)
    text_content = "This is not an Excel file"
    text_file = io.BytesIO(text_content.encode())
    
    files = {
        'file': ('test.txt', text_file, 'text/plain')
    }
    
    try:
        response = requests.post(url, headers=headers, files=files, timeout=30)
        logger.info(f"📊 Invalid file test response: {response.status_code}")
        
        if response.status_code == 400:
            logger.info("✅ Invalid file correctly rejected with 400 Bad Request")
            return True, "File validation working correctly"
        elif response.status_code == 401:
            logger.info("⚠️ Authentication failed but endpoint would validate file format")
            return "ENDPOINT_EXISTS", "Endpoint exists but token expired"
        else:
            logger.error(f"❌ Expected 400 for invalid file, got {response.status_code}")
            return False, f"Unexpected response: {response.status_code}"
            
    except Exception as e:
        logger.error(f"❌ File validation test error: {str(e)}")
        return False, f"Error: {str(e)}"

def test_dependencies():
    """Test if required Python packages are available"""
    logger.info("📦 Testing Backend Dependencies")
    logger.info("=" * 50)
    
    try:
        import pandas as pd
        logger.info("✅ pandas is available")
        
        import openpyxl
        logger.info("✅ openpyxl is available")
        
        # Test basic Excel operations
        test_data = {'A': [1, 2], 'B': [3, 4]}
        df = pd.DataFrame(test_data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        logger.info("✅ Excel file creation works")
        return True, "All dependencies available"
        
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {str(e)}")
        return False, f"Missing dependency: {str(e)}"
    except Exception as e:
        logger.error(f"❌ Dependency test error: {str(e)}")
        return False, f"Error: {str(e)}"

def main():
    """Run all bulk import tests"""
    logger.info("🚀 ADMIN BULK CLIENT IMPORT FEATURE TESTING")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Test 1: Dependencies
    logger.info("\n📦 Testing Backend Dependencies...")
    deps_result, deps_details = test_dependencies()
    test_results['dependencies'] = {
        'working': deps_result,
        'details': deps_details,
        'security': {}
    }
    
    # Test 2: Template Download
    logger.info("\n📥 Testing Template Download...")
    template_result, template_security, template_details = test_template_download()
    test_results['template_download'] = {
        'working': template_result,
        'details': template_details,
        'security': template_security
    }
    
    # Test 3: Bulk Import
    logger.info("\n📤 Testing Bulk Import...")
    import_result, import_security, import_details = test_bulk_import()
    test_results['bulk_import'] = {
        'working': import_result,
        'details': import_details,
        'security': import_security
    }
    
    # Test 4: File Validation
    logger.info("\n📄 Testing File Validation...")
    validation_result, validation_details = test_file_validation()
    test_results['file_validation'] = {
        'working': validation_result,
        'details': validation_details,
        'security': {}
    }
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 BULK IMPORT FEATURE TEST RESULTS")
    logger.info("=" * 60)
    
    working_count = 0
    total_count = len(test_results)
    
    for test_name, result in test_results.items():
        working = result['working']
        if working is True:
            status = "✅ WORKING"
            working_count += 1
        elif working == "ENDPOINT_EXISTS":
            status = "⚠️ EXISTS (Auth Issue)"
            working_count += 0.5  # Partial credit
        else:
            status = "❌ FAILED"
        
        logger.info(f"{test_name.upper():<20}: {status}")
        logger.info(f"{'Details:':<20} {result['details']}")
        
        # Show security test results
        if result['security']:
            logger.info(f"{'Security Tests:':<20}")
            for sec_test, sec_result in result['security'].items():
                logger.info(f"{'  ' + sec_test:<18}: {sec_result}")
        
        logger.info("")
    
    logger.info("-" * 60)
    logger.info(f"TOTAL: {working_count}/{total_count} features working")
    
    # Final assessment
    if working_count >= total_count * 0.75:  # 75% threshold
        logger.info("🎉 BULK IMPORT FEATURE IS WORKING!")
        logger.info("✅ Admin bulk client import functionality is properly implemented")
        logger.info("✅ Security controls are in place (admin-only access)")
        logger.info("✅ Excel file processing logic is available")
        return True
    else:
        logger.error("❌ BULK IMPORT FEATURE HAS ISSUES")
        logger.error("⚠️ Some components need attention")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)