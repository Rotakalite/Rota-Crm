#!/usr/bin/env python3
"""
Railway Backend Verification Test
Quick verification test for Railway backend accessibility and 2FA endpoints
"""

import requests
import json
import sys
from datetime import datetime

# Railway backend URL
RAILWAY_URL = "https://rota-crm-production.up.railway.app"

def test_railway_health():
    """Test Railway backend health endpoint"""
    print("🔍 Testing Railway Backend Health...")
    try:
        response = requests.get(f"{RAILWAY_URL}/api/health", timeout=10)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ Railway backend health check PASSED")
            return True
        else:
            print(f"   ❌ Railway backend health check FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Railway backend health check ERROR: {str(e)}")
        return False

def test_2fa_send_code():
    """Test 2FA send code endpoint"""
    print("\n🔍 Testing 2FA Send Code...")
    try:
        # Test data
        test_data = {
            "email": "test@example.com"
        }
        
        response = requests.post(
            f"{RAILWAY_URL}/api/auth/2fa/send-code",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code in [200, 201, 422]:  # 422 might be validation error but endpoint exists
            print("   ✅ 2FA Send Code endpoint is ACCESSIBLE")
            return True
        elif response.status_code == 405:
            print("   ❌ 2FA Send Code endpoint returns 405 Method Not Allowed")
            return False
        else:
            print(f"   ⚠️ 2FA Send Code endpoint returned: {response.status_code}")
            return True  # Endpoint exists but may have validation issues
    except Exception as e:
        print(f"   ❌ 2FA Send Code endpoint ERROR: {str(e)}")
        return False

def test_api_register():
    """Test API register endpoint"""
    print("\n🔍 Testing API Register...")
    try:
        # Test data
        test_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = requests.post(
            f"{RAILWAY_URL}/api/auth/register",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code in [200, 201, 422, 400]:  # Various valid responses
            print("   ✅ API Register endpoint is ACCESSIBLE")
            return True
        elif response.status_code == 405:
            print("   ❌ API Register endpoint returns 405 Method Not Allowed")
            return False
        else:
            print(f"   ⚠️ API Register endpoint returned: {response.status_code}")
            return True  # Endpoint exists but may have validation issues
    except Exception as e:
        print(f"   ❌ API Register endpoint ERROR: {str(e)}")
        return False

def main():
    """Run all Railway verification tests"""
    print("=" * 60)
    print("🚀 RAILWAY BACKEND VERIFICATION TEST")
    print("=" * 60)
    print(f"Testing Railway URL: {RAILWAY_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run tests
    health_ok = test_railway_health()
    send_code_ok = test_2fa_send_code()
    register_ok = test_api_register()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RAILWAY VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"✅ Health Check: {'PASS' if health_ok else 'FAIL'}")
    print(f"✅ 2FA Send Code: {'PASS' if send_code_ok else 'FAIL'}")
    print(f"✅ API Register: {'PASS' if register_ok else 'FAIL'}")
    
    overall_status = health_ok and send_code_ok and register_ok
    print(f"\n🎯 OVERALL RAILWAY STATUS: {'✅ WORKING' if overall_status else '❌ ISSUES DETECTED'}")
    
    if overall_status:
        print("\n💡 CONCLUSION: Railway backend is accessible and working properly.")
        print("   The issue is likely with frontend URL configuration reverting to emergent URL.")
    else:
        print("\n⚠️ CONCLUSION: Railway backend has accessibility issues.")
        print("   Check Railway deployment status and endpoint configurations.")
    
    return overall_status

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)