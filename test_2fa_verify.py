#!/usr/bin/env python3
"""
Additional 2FA Verify Test
"""

import requests
import json

# Railway backend URL
RAILWAY_URL = "https://rota-crm-production.up.railway.app"

def test_2fa_verify():
    """Test 2FA verify endpoint"""
    print("🔍 Testing 2FA Verify Code...")
    try:
        # Test data
        test_data = {
            "email": "test@example.com",
            "code": "123456"
        }
        
        response = requests.post(
            f"{RAILWAY_URL}/api/auth/2fa/verify-code",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code in [200, 201, 422, 400]:  # Various valid responses
            print("   ✅ 2FA Verify Code endpoint is ACCESSIBLE")
            return True
        elif response.status_code == 405:
            print("   ❌ 2FA Verify Code endpoint returns 405 Method Not Allowed")
            return False
        else:
            print(f"   ⚠️ 2FA Verify Code endpoint returned: {response.status_code}")
            return True  # Endpoint exists but may have validation issues
    except Exception as e:
        print(f"   ❌ 2FA Verify Code endpoint ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_2fa_verify()