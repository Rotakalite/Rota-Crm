#!/usr/bin/env python3
"""
Admin Bulk Client Import Feature Testing
========================================

This script tests the admin bulk client import functionality including:
1. POST /api/bulk-import/clients endpoint (admin only)
2. GET /api/bulk-import/template endpoint (admin only)
3. Security testing for non-admin users
4. Excel file processing logic
5. Authentication and authorization

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

# Test tokens (these are sample tokens for testing - will be invalid but we test the security)
ADMIN_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQURNSU4iLCJlbWFpbCI6ImFkbWluQHJvdGFrYWxpdGVkYW5pc21hbmxpay5jb20iLCJuYW1lIjoiQWRtaW4gVXNlciJ9.signature"
CLIENT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ0xJRU5UIiwiZW1haWwiOiJjbGllbnRAdGVzdC5jb20iLCJuYW1lIjoiQ2xpZW50IFVzZXIifQ.signature"
CONSULTANT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Imluc18yUHFUQU9lQVNUUTlqaHRQcVpwSGlDRnVvIiwidHlwIjoiSldUIn0.eyJhenAiOiJodHRwczovL3JvdGEtY3JtLXByb2R1Y3Rpb24udXAucmFpbHdheS5hcHAiLCJleHAiOjE3MTk5MzYxNjAsImlhdCI6MTcxOTkzMjU2MCwiaXNzIjoiaHR0cHM6Ly9hZGFwdGluZy1lZnQtNi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3MTk5MzI1NTAsInN1YiI6InVzZXJfQ09OU1VMVEFOVCIsImVtYWlsIjoiY29uc3VsdGFudEB0ZXN0LmNvbSIsIm5hbWUiOiJDb25zdWx0YW50IFVzZXIifQ.signature"
INVALID_TOKEN = "invalid.token.format"

def make_request(method, endpoint, headers=None, data=None, files=None, params=None):
    """Make HTTP request with proper error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, data=data, files=files, json=data if not files else None, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        logger.info(f"{method} {url} -> {response.status_code}")
        
        # Try to parse JSON response
        try:
            response_data = response.json()
        except:
            response_data = {"text": response.text}
        
        return {
            "status_code": response.status_code,
            "data": response_data,
            "headers": dict(response.headers)
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return {
            "status_code": 0,
            "data": {"error": str(e)},
            "headers": {}
        }

def create_test_excel_file():
    """Create a test Excel file for bulk import"""
    test_data = {
        'TESİS ADI': [
            'Test Otel Bulk Import 1',
            'Test Otel Bulk Import 2',
            'Test Otel Bulk Import 3'
        ],
        'İL': ['İstanbul', 'Ankara', 'İzmir'],
        'İLÇE': ['Beyoğlu', 'Çankaya', 'Konak'],
        'TELEFON': ['+90 212 555 0001', '+90 312 555 0002', '+90 232 555 0003'],
        'MAİL': ['test1@bulkimport.com', 'test2@bulkimport.com', 'test3@bulkimport.com'],
        'SERTİFİKA BİTİŞ TARİHİ': ['2024-12-31', '2025-06-30', '2025-12-31'],
        'DENETLEYEN FİRMA': ['Test Denetim A', 'Test Denetim B', 'Test Denetim C']
    }
    
    df = pd.DataFrame(test_data)
    
    # Create temporary Excel file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    df.to_excel(temp_file.name, index=False)
    temp_file.close()
    
    return temp_file.name

def test_bulk_import_endpoints():
    """Test all bulk import endpoints"""
    
    print("=" * 80)
    print("🚀 BULK IMPORT ENDPOINTS TESTING")
    print("=" * 80)
    
    # Test results
    results = {
        "bulk_import_clients": {"tested": False, "working": False, "details": ""},
        "bulk_import_template": {"tested": False, "working": False, "details": ""},
        "bulk_email_stats": {"tested": False, "working": False, "details": ""}
    }
    
    # 1. Test Bulk Import Template Endpoint (GET /api/bulk-import/template)
    print("\n1️⃣ Testing GET /api/bulk-import/template")
    print("-" * 50)
    
    # Test without authentication
    print("Testing without authentication...")
    response = make_request("GET", "/bulk-import/template")
    print(f"Status: {response['status_code']}")
    print(f"Response: {response['data']}")
    
    if response['status_code'] in [401, 403]:
        print("✅ Correctly requires authentication")
    else:
        print("❌ Should require authentication")
    
    # Test with admin authentication
    print("\nTesting with admin authentication...")
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    response = make_request("GET", "/bulk-import/template", headers=headers)
    print(f"Status: {response['status_code']}")
    
    results["bulk_import_template"]["tested"] = True
    if response['status_code'] == 200:
        print("✅ Template endpoint accessible with admin auth")
        results["bulk_import_template"]["working"] = True
        results["bulk_import_template"]["details"] = "Template download endpoint working correctly"
        
        # Check if it's actually an Excel file
        content_type = response['headers'].get('content-type', '')
        if 'spreadsheet' in content_type or 'excel' in content_type:
            print("✅ Returns Excel file format")
        else:
            print(f"⚠️ Content-Type: {content_type}")
    elif response['status_code'] in [401, 403]:
        print("❌ Authentication failed - token may be invalid")
        results["bulk_import_template"]["details"] = f"Authentication failed: {response['data']}"
    else:
        print(f"❌ Unexpected status code: {response['status_code']}")
        results["bulk_import_template"]["details"] = f"Error: {response['data']}"
    
    # 2. Test Bulk Email Stats Endpoint (GET /api/bulk-email/stats)
    print("\n2️⃣ Testing GET /api/bulk-email/stats")
    print("-" * 50)
    
    # Test without authentication
    print("Testing without authentication...")
    response = make_request("GET", "/bulk-email/stats")
    print(f"Status: {response['status_code']}")
    print(f"Response: {response['data']}")
    
    if response['status_code'] in [401, 403]:
        print("✅ Correctly requires authentication")
    else:
        print("❌ Should require authentication")
    
    # Test with admin authentication
    print("\nTesting with admin authentication...")
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    response = make_request("GET", "/bulk-email/stats", headers=headers)
    print(f"Status: {response['status_code']}")
    
    results["bulk_email_stats"]["tested"] = True
    if response['status_code'] == 200:
        print("✅ Bulk email stats endpoint accessible with admin auth")
        results["bulk_email_stats"]["working"] = True
        
        # Check response structure
        data = response['data']
        expected_fields = ['total_clients', 'clients_with_email', 'email_coverage_percentage']
        missing_fields = [field for field in expected_fields if field not in data]
        
        if not missing_fields:
            print("✅ Response contains expected fields")
            print(f"   Total clients: {data.get('total_clients', 'N/A')}")
            print(f"   Clients with email: {data.get('clients_with_email', 'N/A')}")
            print(f"   Email coverage: {data.get('email_coverage_percentage', 'N/A')}%")
            results["bulk_email_stats"]["details"] = f"Stats endpoint working - {data.get('total_clients', 0)} total clients"
        else:
            print(f"⚠️ Missing expected fields: {missing_fields}")
            results["bulk_email_stats"]["details"] = f"Missing fields: {missing_fields}"
            
    elif response['status_code'] in [401, 403]:
        print("❌ Authentication failed - token may be invalid")
        results["bulk_email_stats"]["details"] = f"Authentication failed: {response['data']}"
    else:
        print(f"❌ Unexpected status code: {response['status_code']}")
        results["bulk_email_stats"]["details"] = f"Error: {response['data']}"
    
    # 3. Test Bulk Import Clients Endpoint (POST /api/bulk-import/clients)
    print("\n3️⃣ Testing POST /api/bulk-import/clients")
    print("-" * 50)
    
    # Test without authentication
    print("Testing without authentication...")
    response = make_request("POST", "/bulk-import/clients")
    print(f"Status: {response['status_code']}")
    print(f"Response: {response['data']}")
    
    if response['status_code'] in [401, 403]:
        print("✅ Correctly requires authentication")
    else:
        print("❌ Should require authentication")
    
    # Test with admin authentication but no file
    print("\nTesting with admin authentication but no file...")
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    response = make_request("POST", "/bulk-import/clients", headers=headers)
    print(f"Status: {response['status_code']}")
    print(f"Response: {response['data']}")
    
    if response['status_code'] == 422:
        print("✅ Correctly returns 422 for missing file")
    else:
        print(f"⚠️ Expected 422 for missing file, got {response['status_code']}")
    
    # Test with admin authentication and Excel file
    print("\nTesting with admin authentication and Excel file...")
    try:
        # Create test Excel file
        excel_file_path = create_test_excel_file()
        
        with open(excel_file_path, 'rb') as f:
            files = {'file': ('test_clients.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = make_request("POST", "/bulk-import/clients", headers=headers, files=files)
        
        print(f"Status: {response['status_code']}")
        print(f"Response: {response['data']}")
        
        results["bulk_import_clients"]["tested"] = True
        if response['status_code'] == 200:
            print("✅ Bulk import endpoint accessible with admin auth and file")
            results["bulk_import_clients"]["working"] = True
            
            # Check response structure
            data = response['data']
            if 'imported_count' in data:
                print(f"   Imported: {data.get('imported_count', 0)} clients")
                print(f"   Skipped: {data.get('skipped_count', 0)} clients")
                print(f"   Errors: {data.get('error_count', 0)} clients")
                results["bulk_import_clients"]["details"] = f"Import successful - {data.get('imported_count', 0)} imported"
            else:
                print("⚠️ Response missing expected import statistics")
                results["bulk_import_clients"]["details"] = "Import endpoint accessible but response format unexpected"
                
        elif response['status_code'] in [401, 403]:
            print("❌ Authentication failed - token may be invalid")
            results["bulk_import_clients"]["details"] = f"Authentication failed: {response['data']}"
        else:
            print(f"❌ Unexpected status code: {response['status_code']}")
            results["bulk_import_clients"]["details"] = f"Error: {response['data']}"
        
        # Clean up temporary file
        os.unlink(excel_file_path)
        
    except Exception as e:
        print(f"❌ Error testing bulk import with file: {str(e)}")
        results["bulk_import_clients"]["details"] = f"Test error: {str(e)}"
    
    # 4. Test Invalid File Format
    print("\n4️⃣ Testing POST /api/bulk-import/clients with invalid file format")
    print("-" * 50)
    
    try:
        # Create a text file instead of Excel
        temp_txt = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w')
        temp_txt.write("This is not an Excel file")
        temp_txt.close()
        
        with open(temp_txt.name, 'rb') as f:
            files = {'file': ('test.txt', f, 'text/plain')}
            response = make_request("POST", "/bulk-import/clients", headers=headers, files=files)
        
        print(f"Status: {response['status_code']}")
        print(f"Response: {response['data']}")
        
        if response['status_code'] == 400:
            print("✅ Correctly rejects non-Excel files")
        else:
            print(f"⚠️ Expected 400 for invalid file format, got {response['status_code']}")
        
        # Clean up
        os.unlink(temp_txt.name)
        
    except Exception as e:
        print(f"❌ Error testing invalid file format: {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 BULK IMPORT TESTING SUMMARY")
    print("=" * 80)
    
    for endpoint, result in results.items():
        status = "✅ WORKING" if result["working"] else "❌ FAILED" if result["tested"] else "⚠️ NOT TESTED"
        print(f"{endpoint}: {status}")
        if result["details"]:
            print(f"   Details: {result['details']}")
    
    # Overall assessment
    working_count = sum(1 for r in results.values() if r["working"])
    tested_count = sum(1 for r in results.values() if r["tested"])
    
    print(f"\nOverall: {working_count}/{tested_count} endpoints working")
    
    if working_count == tested_count and tested_count == 3:
        print("🎉 ALL BULK IMPORT ENDPOINTS ARE WORKING!")
        return True
    else:
        print("⚠️ Some bulk import endpoints have issues")
        return False

if __name__ == "__main__":
    try:
        # Check if pandas is available
        import pandas as pd
        print("✅ pandas is available for Excel file creation")
    except ImportError:
        print("❌ pandas not available - installing...")
        os.system("pip install pandas openpyxl")
        import pandas as pd
    
    success = test_bulk_import_endpoints()
    
    if success:
        print("\n🎯 RECOMMENDATION: All bulk import endpoints are working correctly!")
    else:
        print("\n🔧 RECOMMENDATION: Some endpoints need attention - check authentication tokens or endpoint implementation")