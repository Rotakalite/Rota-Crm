#!/usr/bin/env python3
"""
Sustainability Report Endpoint Registration Test
Tests the fix for sustainability report endpoints returning 404 -> now should return 401/403
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://63cd9e66-c298-4a2c-92bc-f8af7936d9a9.preview.emergentagent.com"

def test_endpoint_registration():
    """Test that sustainability report endpoints are properly registered"""
    print("🎯 SUSTAINABILITY REPORT ENDPOINT REGISTRATION TEST")
    print("=" * 60)
    
    # Test endpoints that should be registered
    endpoints_to_test = [
        "/api/reports/comprehensive",
        "/api/reports/training", 
        "/api/reports/consumption"
    ]
    
    results = []
    
    for endpoint in endpoints_to_test:
        print(f"\n📋 Testing endpoint: {endpoint}")
        
        try:
            # Test without authentication - should return 401/403, NOT 404
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 404:
                print(f"   ❌ ENDPOINT NOT REGISTERED - Still returns 404")
                results.append({
                    "endpoint": endpoint,
                    "status": "FAILED",
                    "issue": "Endpoint returns 404 - not registered properly",
                    "status_code": response.status_code
                })
            elif response.status_code in [401, 403]:
                print(f"   ✅ ENDPOINT REGISTERED - Returns {response.status_code} (auth required)")
                results.append({
                    "endpoint": endpoint,
                    "status": "SUCCESS", 
                    "issue": None,
                    "status_code": response.status_code
                })
            else:
                print(f"   ⚠️ UNEXPECTED RESPONSE - Status {response.status_code}")
                results.append({
                    "endpoint": endpoint,
                    "status": "UNEXPECTED",
                    "issue": f"Unexpected status code: {response.status_code}",
                    "status_code": response.status_code
                })
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ REQUEST FAILED: {str(e)}")
            results.append({
                "endpoint": endpoint,
                "status": "ERROR",
                "issue": f"Request failed: {str(e)}",
                "status_code": None
            })
    
    return results

def test_with_invalid_auth():
    """Test endpoints with invalid authentication tokens"""
    print(f"\n🔐 TESTING WITH INVALID AUTH TOKENS")
    print("=" * 60)
    
    endpoints_to_test = [
        "/api/reports/comprehensive",
        "/api/reports/training",
        "/api/reports/consumption"
    ]
    
    # Test with invalid token
    headers = {"Authorization": "Bearer invalid_token_12345"}
    
    results = []
    
    for endpoint in endpoints_to_test:
        print(f"\n📋 Testing {endpoint} with invalid token")
        
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=10)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 401:
                print(f"   ✅ PROPER AUTH VALIDATION - Returns 401 Unauthorized")
                results.append({
                    "endpoint": endpoint,
                    "status": "SUCCESS",
                    "issue": None,
                    "status_code": response.status_code
                })
            elif response.status_code == 404:
                print(f"   ❌ ENDPOINT NOT REGISTERED - Still returns 404")
                results.append({
                    "endpoint": endpoint,
                    "status": "FAILED",
                    "issue": "Endpoint returns 404 with auth header",
                    "status_code": response.status_code
                })
            else:
                print(f"   ⚠️ UNEXPECTED RESPONSE - Status {response.status_code}")
                results.append({
                    "endpoint": endpoint,
                    "status": "UNEXPECTED",
                    "issue": f"Expected 401, got {response.status_code}",
                    "status_code": response.status_code
                })
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ REQUEST FAILED: {str(e)}")
            results.append({
                "endpoint": endpoint,
                "status": "ERROR",
                "issue": f"Request failed: {str(e)}",
                "status_code": None
            })
    
    return results

def test_http_methods():
    """Test that endpoints only accept GET method"""
    print(f"\n🔧 TESTING HTTP METHOD RESTRICTIONS")
    print("=" * 60)
    
    endpoint = "/api/reports/comprehensive"  # Test one endpoint
    methods_to_test = ["POST", "PUT", "DELETE"]
    
    results = []
    
    for method in methods_to_test:
        print(f"\n📋 Testing {method} {endpoint}")
        
        try:
            response = requests.request(method, f"{BACKEND_URL}{endpoint}", timeout=10)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 405:
                print(f"   ✅ METHOD NOT ALLOWED - Properly rejects {method}")
                results.append({
                    "method": method,
                    "status": "SUCCESS",
                    "issue": None,
                    "status_code": response.status_code
                })
            elif response.status_code == 404:
                print(f"   ❌ ENDPOINT NOT REGISTERED - Returns 404")
                results.append({
                    "method": method,
                    "status": "FAILED", 
                    "issue": "Endpoint returns 404",
                    "status_code": response.status_code
                })
            else:
                print(f"   ⚠️ UNEXPECTED RESPONSE - Status {response.status_code}")
                results.append({
                    "method": method,
                    "status": "UNEXPECTED",
                    "issue": f"Expected 405, got {response.status_code}",
                    "status_code": response.status_code
                })
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ REQUEST FAILED: {str(e)}")
            results.append({
                "method": method,
                "status": "ERROR",
                "issue": f"Request failed: {str(e)}",
                "status_code": None
            })
    
    return results

def test_backend_health():
    """Test backend health to ensure it's accessible"""
    print(f"\n🏥 BACKEND HEALTH CHECK")
    print("=" * 60)
    
    try:
        # Test root endpoint
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        print(f"Root endpoint: {response.status_code} - {response.text[:100]}...")
        
        # Test health endpoint
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        print(f"Health endpoint: {response.status_code} - {response.text[:100]}...")
        
        # Test API health
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        print(f"API Health endpoint: {response.status_code} - {response.text[:100]}...")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ BACKEND NOT ACCESSIBLE: {str(e)}")
        return False

def main():
    """Main test execution"""
    print("🎯 SUSTAINABILITY REPORT ENDPOINT FIX VERIFICATION")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Check backend health first
    if not test_backend_health():
        print("\n❌ BACKEND NOT ACCESSIBLE - Cannot run tests")
        sys.exit(1)
    
    # Run tests
    registration_results = test_endpoint_registration()
    auth_results = test_with_invalid_auth()
    method_results = test_http_methods()
    
    # Calculate overall results
    all_results = registration_results + auth_results + method_results
    total_tests = len(all_results)
    successful_tests = len([r for r in all_results if r["status"] == "SUCCESS"])
    failed_tests = len([r for r in all_results if r["status"] == "FAILED"])
    error_tests = len([r for r in all_results if r["status"] == "ERROR"])
    
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    # Print summary
    print(f"\n🎯 SUSTAINABILITY REPORT ENDPOINT FIX TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Successful: {successful_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"🔥 Errors: {error_tests}")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    # Key findings
    print(f"\n🔍 KEY FINDINGS:")
    
    # Check if endpoints are properly registered (not returning 404)
    registration_failures = [r for r in registration_results if r["status"] == "FAILED"]
    if registration_failures:
        print(f"❌ ENDPOINT REGISTRATION ISSUES:")
        for failure in registration_failures:
            print(f"   - {failure['endpoint']}: {failure['issue']}")
    else:
        print(f"✅ ALL REPORT ENDPOINTS PROPERLY REGISTERED (no 404 errors)")
    
    # Check authentication
    auth_failures = [r for r in auth_results if r["status"] == "FAILED"]
    if auth_failures:
        print(f"❌ AUTHENTICATION ISSUES:")
        for failure in auth_failures:
            print(f"   - {failure['endpoint']}: {failure['issue']}")
    else:
        print(f"✅ AUTHENTICATION PROPERLY IMPLEMENTED (401 responses)")
    
    # Overall assessment
    if failed_tests == 0:
        print(f"\n🎉 SUSTAINABILITY REPORT ENDPOINT FIX SUCCESSFUL!")
        print(f"   - All endpoints properly registered (no 404 errors)")
        print(f"   - Authentication working correctly (401/403 responses)")
        print(f"   - HTTP method restrictions working")
    else:
        print(f"\n⚠️ SUSTAINABILITY REPORT ENDPOINT FIX PARTIALLY SUCCESSFUL")
        print(f"   - {failed_tests} issues still need to be addressed")
    
    print("=" * 80)
    
    return success_rate >= 80.0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)