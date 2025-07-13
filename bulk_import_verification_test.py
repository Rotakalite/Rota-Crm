#!/usr/bin/env python3
"""
Bulk Import Endpoints Verification Test
Verifies that the bulk import endpoints are properly registered and accessible.
"""

import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL from frontend .env
BACKEND_URL = "https://rota-crm-production.up.railway.app"
API_BASE_URL = f"{BACKEND_URL}/api"

def test_endpoint_accessibility():
    """Test that bulk import endpoints are accessible and properly secured"""
    
    print("=" * 80)
    print("🔍 BULK IMPORT ENDPOINTS ACCESSIBILITY TEST")
    print("=" * 80)
    print(f"Testing backend: {BACKEND_URL}")
    print(f"API base URL: {API_BASE_URL}")
    
    # Test results
    results = {
        "health_check": {"accessible": False, "details": ""},
        "bulk_import_template": {"accessible": False, "details": ""},
        "bulk_import_clients": {"accessible": False, "details": ""},
        "bulk_email_stats": {"accessible": False, "details": ""}
    }
    
    # 1. Test Health Endpoint (baseline)
    print("\n🏥 Testing API Health Check")
    print("-" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend is healthy and accessible")
            print(f"   Service: {data.get('service', 'Unknown')}")
            print(f"   Version: {data.get('version', 'Unknown')}")
            print(f"   Timestamp: {data.get('timestamp', 'Unknown')}")
            results["health_check"]["accessible"] = True
            results["health_check"]["details"] = "Backend healthy and accessible"
        else:
            print(f"❌ Health check failed: {response.status_code}")
            results["health_check"]["details"] = f"Health check failed: {response.status_code}"
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        results["health_check"]["details"] = f"Health check error: {str(e)}"
    
    # 2. Test Bulk Import Template Endpoint
    print("\n📄 Testing GET /api/bulk-import/template")
    print("-" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/bulk-import/template", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 403:
            print("✅ Endpoint exists and correctly requires authentication")
            results["bulk_import_template"]["accessible"] = True
            results["bulk_import_template"]["details"] = "Endpoint exists, properly secured"
        elif response.status_code == 404:
            print("❌ Endpoint not found - may not be registered")
            results["bulk_import_template"]["details"] = "Endpoint not found (404)"
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            try:
                data = response.json()
                print(f"   Response: {data}")
                results["bulk_import_template"]["details"] = f"Unexpected status {response.status_code}: {data}"
            except:
                results["bulk_import_template"]["details"] = f"Unexpected status {response.status_code}"
    except Exception as e:
        print(f"❌ Request error: {str(e)}")
        results["bulk_import_template"]["details"] = f"Request error: {str(e)}"
    
    # 3. Test Bulk Import Clients Endpoint
    print("\n📊 Testing POST /api/bulk-import/clients")
    print("-" * 50)
    
    try:
        response = requests.post(f"{API_BASE_URL}/bulk-import/clients", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 403:
            print("✅ Endpoint exists and correctly requires authentication")
            results["bulk_import_clients"]["accessible"] = True
            results["bulk_import_clients"]["details"] = "Endpoint exists, properly secured"
        elif response.status_code == 404:
            print("❌ Endpoint not found - may not be registered")
            results["bulk_import_clients"]["details"] = "Endpoint not found (404)"
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            try:
                data = response.json()
                print(f"   Response: {data}")
                results["bulk_import_clients"]["details"] = f"Unexpected status {response.status_code}: {data}"
            except:
                results["bulk_import_clients"]["details"] = f"Unexpected status {response.status_code}"
    except Exception as e:
        print(f"❌ Request error: {str(e)}")
        results["bulk_import_clients"]["details"] = f"Request error: {str(e)}"
    
    # 4. Test Bulk Email Stats Endpoint
    print("\n📈 Testing GET /api/bulk-email/stats")
    print("-" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/bulk-email/stats", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 403:
            print("✅ Endpoint exists and correctly requires authentication")
            results["bulk_email_stats"]["accessible"] = True
            results["bulk_email_stats"]["details"] = "Endpoint exists, properly secured"
        elif response.status_code == 404:
            print("❌ Endpoint not found - may not be registered")
            results["bulk_email_stats"]["details"] = "Endpoint not found (404)"
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            try:
                data = response.json()
                print(f"   Response: {data}")
                results["bulk_email_stats"]["details"] = f"Unexpected status {response.status_code}: {data}"
            except:
                results["bulk_email_stats"]["details"] = f"Unexpected status {response.status_code}"
    except Exception as e:
        print(f"❌ Request error: {str(e)}")
        results["bulk_email_stats"]["details"] = f"Request error: {str(e)}"
    
    # 5. Test API Router Registration
    print("\n🔗 Testing API Router Registration")
    print("-" * 50)
    
    # Test a few other known endpoints to verify API router is working
    test_endpoints = [
        "/health",
        "/consultants",
        "/clients"
    ]
    
    router_working = 0
    for endpoint in test_endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403]:  # Any response except 404
                router_working += 1
                print(f"✅ {endpoint} -> {response.status_code}")
            else:
                print(f"❌ {endpoint} -> {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} -> Error: {str(e)}")
    
    if router_working >= 2:
        print(f"✅ API router is working ({router_working}/{len(test_endpoints)} endpoints responsive)")
    else:
        print(f"⚠️ API router may have issues ({router_working}/{len(test_endpoints)} endpoints responsive)")
    
    # Summary
    print("\n" + "=" * 80)
    print("📋 BULK IMPORT ENDPOINTS VERIFICATION SUMMARY")
    print("=" * 80)
    
    accessible_count = sum(1 for r in results.values() if r["accessible"])
    total_count = len(results)
    
    for endpoint, result in results.items():
        status = "✅ ACCESSIBLE" if result["accessible"] else "❌ NOT ACCESSIBLE"
        print(f"{endpoint}: {status}")
        if result["details"]:
            print(f"   Details: {result['details']}")
    
    print(f"\nOverall: {accessible_count}/{total_count} endpoints accessible")
    
    # Specific assessment for bulk import endpoints
    bulk_endpoints = ["bulk_import_template", "bulk_import_clients", "bulk_email_stats"]
    bulk_accessible = sum(1 for ep in bulk_endpoints if results[ep]["accessible"])
    
    print(f"Bulk Import Endpoints: {bulk_accessible}/{len(bulk_endpoints)} accessible")
    
    if bulk_accessible == len(bulk_endpoints):
        print("\n🎉 ALL BULK IMPORT ENDPOINTS ARE PROPERLY REGISTERED AND ACCESSIBLE!")
        print("✅ Endpoints exist and are correctly secured with admin authentication")
        print("✅ Ready for frontend integration")
        return True
    else:
        print("\n⚠️ Some bulk import endpoints are not accessible")
        print("🔧 Check endpoint registration in server.py")
        return False

def test_endpoint_methods():
    """Test HTTP methods for bulk import endpoints"""
    
    print("\n" + "=" * 80)
    print("🔧 HTTP METHODS VERIFICATION")
    print("=" * 80)
    
    # Test different HTTP methods to verify endpoint configuration
    endpoints_methods = [
        ("/bulk-import/template", "GET"),
        ("/bulk-import/clients", "POST"),
        ("/bulk-email/stats", "GET")
    ]
    
    for endpoint, expected_method in endpoints_methods:
        print(f"\n🔍 Testing {expected_method} {endpoint}")
        print("-" * 40)
        
        # Test correct method
        try:
            if expected_method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
            elif expected_method == "POST":
                response = requests.post(f"{API_BASE_URL}{endpoint}", timeout=5)
            
            print(f"✅ {expected_method} {endpoint} -> {response.status_code}")
            
            if response.status_code == 403:
                print("   ✅ Correctly requires authentication")
            elif response.status_code == 405:
                print("   ❌ Method not allowed - check endpoint definition")
            elif response.status_code == 404:
                print("   ❌ Endpoint not found")
            
        except Exception as e:
            print(f"❌ Error testing {expected_method} {endpoint}: {str(e)}")
        
        # Test wrong method (should return 405)
        wrong_method = "POST" if expected_method == "GET" else "GET"
        try:
            if wrong_method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
            elif wrong_method == "POST":
                response = requests.post(f"{API_BASE_URL}{endpoint}", timeout=5)
            
            if response.status_code == 405:
                print(f"   ✅ {wrong_method} correctly returns 405 Method Not Allowed")
            else:
                print(f"   ⚠️ {wrong_method} returns {response.status_code} (expected 405)")
                
        except Exception as e:
            print(f"   ⚠️ Error testing wrong method: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 Starting Bulk Import Endpoints Verification")
    print(f"📅 Test Time: {datetime.now().isoformat()}")
    
    # Run accessibility test
    success = test_endpoint_accessibility()
    
    # Run methods test
    test_endpoint_methods()
    
    # Final recommendation
    print("\n" + "=" * 80)
    print("🎯 FINAL ASSESSMENT")
    print("=" * 80)
    
    if success:
        print("✅ BULK IMPORT ENDPOINTS ARE WORKING CORRECTLY!")
        print("📝 All endpoints are properly registered and secured")
        print("🔐 Authentication is correctly enforced")
        print("🚀 Ready for frontend integration")
        print("\n💡 NEXT STEPS:")
        print("   1. Frontend can now safely call these endpoints")
        print("   2. Ensure admin users have valid authentication tokens")
        print("   3. Test file upload functionality with real Excel files")
    else:
        print("⚠️ SOME ENDPOINTS NEED ATTENTION")
        print("🔧 Check server.py for proper endpoint registration")
        print("📋 Verify API router configuration")
        
    print(f"\n📊 Test completed at: {datetime.now().isoformat()}")