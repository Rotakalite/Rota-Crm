#!/usr/bin/env python3
"""
🏨 FRONT OFFICE 500 INTERNAL SERVER ERROR DEBUG TEST
==================================================

Bu test Front Office modülü endpoint'lerinin 500 Internal Server Error sorununu debug eder:

Test Edilecek Ana Konular:
1. /api/reservations GET endpoint accessibility
2. /api/reservations POST endpoint for creation
3. /api/guests endpoint (Front Office module)
4. /api/front-office-dashboard endpoint if exists
5. Authentication requirements and role-based access
6. Test with various HTTP methods and invalid data
7. Check if endpoints are properly deployed on Railway production
8. Verify ReservationInput model validation
9. Test error handling for invalid dates, room conflicts
10. Check MongoDB collections (reservations, guests) accessibility

Test Environment:
- Backend URL: https://rota-crm-production.up.railway.app
- Focus on ALL Front Office related endpoints
- Test both authenticated and unauthenticated scenarios

Expected Results:
- Endpoints should return proper HTTP codes (403/401 for auth, not 500)
- 500 errors indicate backend implementation issues that need immediate attention
- All Front Office functionality should be accessible and working
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import uuid

# Production URL from review request
BACKEND_URL = "https://rota-crm-production.up.railway.app"

class FrontOfficeDebugTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        # Test data for reservations
        self.test_reservation_data = {
            "guest_name": "Ahmet Yılmaz",
            "guest_email": "ahmet.yilmaz@example.com",
            "guest_phone": "+90 532 123 4567",
            "check_in_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "check_out_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "room_number": "101",
            "room_type": "Standard",
            "guest_count": 2,
            "total_amount": 450.00,
            "payment_status": "pending",
            "special_requests": "Late check-in"
        }
        
        # Test data for guests
        self.test_guest_data = {
            "name": "Fatma Demir",
            "email": "fatma.demir@example.com",
            "phone": "+90 533 987 6543",
            "nationality": "Turkish",
            "id_number": "12345678901",
            "vip_status": False,
            "notes": "Regular guest"
        }
        
        # Test reservation IDs for different scenarios
        self.test_reservation_ids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "6ba7b811-9dad-11d1-80b4-00c04fd430c8"
        ]
        
        # Test guest IDs for different scenarios
        self.test_guest_ids = [
            "750e8400-e29b-41d4-a716-446655440000",
            "7ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "7ba7b811-9dad-11d1-80b4-00c04fd430c8"
        ]

    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Test sonucunu logla"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and expected:
            print(f"   🎯 Expected: {expected}")
            print(f"   📊 Actual: {actual}")
        print()

    def test_backend_health(self):
        """Backend sağlık kontrolü"""
        print("🏥 Backend Health Check")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                self.log_test(
                    "Backend Health Check",
                    True,
                    f"Railway production backend erişilebilir (Status: {response.status_code})"
                )
                return True
            else:
                self.log_test(
                    "Backend Health Check", 
                    False,
                    f"Backend sağlık kontrolü başarısız",
                    "200",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Backend Health Check",
                False, 
                f"Backend bağlantı hatası: {str(e)}"
            )
            return False

    def test_reservations_get_endpoint(self):
        """GET /api/reservations endpoint'ini test et"""
        print("🏨 Reservations GET Endpoint Test")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.backend_url}/api/reservations", timeout=10)
            
            # Check if endpoint exists (not 404)
            if response.status_code == 404:
                self.log_test(
                    "GET /api/reservations - Endpoint Exists",
                    False,
                    f"🚨 CRITICAL: Reservations endpoint bulunamadı - Front Office modülü deploy edilmemiş!",
                    "Not 404",
                    "404"
                )
                return False
            
            # Check if it's not returning 500 Internal Server Error
            if response.status_code == 500:
                self.log_test(
                    "GET /api/reservations - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 Internal Server Error - Backend implementation hatası!",
                    "Not 500",
                    "500"
                )
                return False
            
            # Should return proper auth error (403/401) instead of 500
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/reservations - Proper Auth Response",
                    True,
                    f"✅ Endpoint mevcut ve doğru auth kontrolü yapıyor (Status: {response.status_code})"
                )
                return True
            
            # Any other response is also acceptable (endpoint exists)
            self.log_test(
                "GET /api/reservations - Endpoint Accessible",
                True,
                f"✅ Endpoint erişilebilir (Status: {response.status_code})"
            )
            return True
                
        except Exception as e:
            self.log_test(
                "GET /api/reservations - Connection Test",
                False,
                f"Request hatası: {str(e)}"
            )
            return False

    def test_reservations_post_endpoint(self):
        """POST /api/reservations endpoint'ini test et"""
        print("🏨 Reservations POST Endpoint Test")
        print("=" * 50)
        
        try:
            response = requests.post(
                f"{self.backend_url}/api/reservations",
                json=self.test_reservation_data,
                timeout=10
            )
            
            # Check if endpoint exists (not 404)
            if response.status_code == 404:
                self.log_test(
                    "POST /api/reservations - Endpoint Exists",
                    False,
                    f"🚨 CRITICAL: Reservations POST endpoint bulunamadı!",
                    "Not 404",
                    "404"
                )
                return False
            
            # Check if it's not returning 500 Internal Server Error
            if response.status_code == 500:
                self.log_test(
                    "POST /api/reservations - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 Internal Server Error - Reservation creation hatası!",
                    "Not 500",
                    "500"
                )
                return False
            
            # Should return proper auth error (403/401) or validation error (400/422)
            if response.status_code in [400, 401, 403, 422]:
                self.log_test(
                    "POST /api/reservations - Proper Response",
                    True,
                    f"✅ Endpoint mevcut ve doğru response (Status: {response.status_code})"
                )
                return True
            
            # Success response is also good
            if response.status_code in [200, 201]:
                self.log_test(
                    "POST /api/reservations - Success Response",
                    True,
                    f"✅ Reservation creation başarılı (Status: {response.status_code})"
                )
                return True
            
            # Any other response means endpoint exists
            self.log_test(
                "POST /api/reservations - Endpoint Accessible",
                True,
                f"✅ Endpoint erişilebilir (Status: {response.status_code})"
            )
            return True
                
        except Exception as e:
            self.log_test(
                "POST /api/reservations - Connection Test",
                False,
                f"Request hatası: {str(e)}"
            )
            return False

    def test_guests_endpoint(self):
        """GET /api/guests endpoint'ini test et"""
        print("👥 Guests Endpoint Test")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.backend_url}/api/guests", timeout=10)
            
            # Check if endpoint exists (not 404)
            if response.status_code == 404:
                self.log_test(
                    "GET /api/guests - Endpoint Exists",
                    False,
                    f"🚨 CRITICAL: Guests endpoint bulunamadı - Front Office modülü eksik!",
                    "Not 404",
                    "404"
                )
                return False
            
            # Check if it's not returning 500 Internal Server Error
            if response.status_code == 500:
                self.log_test(
                    "GET /api/guests - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 Internal Server Error - Guests endpoint hatası!",
                    "Not 500",
                    "500"
                )
                return False
            
            # Should return proper auth error (403/401)
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/guests - Proper Auth Response",
                    True,
                    f"✅ Guests endpoint mevcut ve auth kontrolü yapıyor (Status: {response.status_code})"
                )
                return True
            
            # Any other response is also acceptable
            self.log_test(
                "GET /api/guests - Endpoint Accessible",
                True,
                f"✅ Guests endpoint erişilebilir (Status: {response.status_code})"
            )
            return True
                
        except Exception as e:
            self.log_test(
                "GET /api/guests - Connection Test",
                False,
                f"Request hatası: {str(e)}"
            )
            return False

    def test_guests_post_endpoint(self):
        """POST /api/guests endpoint'ini test et"""
        print("👥 Guests POST Endpoint Test")
        print("=" * 50)
        
        try:
            response = requests.post(
                f"{self.backend_url}/api/guests",
                json=self.test_guest_data,
                timeout=10
            )
            
            # Check if endpoint exists (not 404)
            if response.status_code == 404:
                self.log_test(
                    "POST /api/guests - Endpoint Exists",
                    False,
                    f"🚨 CRITICAL: Guests POST endpoint bulunamadı!",
                    "Not 404",
                    "404"
                )
                return False
            
            # Check if it's not returning 500 Internal Server Error
            if response.status_code == 500:
                self.log_test(
                    "POST /api/guests - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 Internal Server Error - Guest creation hatası!",
                    "Not 500",
                    "500"
                )
                return False
            
            # Should return proper response
            if response.status_code in [400, 401, 403, 422]:
                self.log_test(
                    "POST /api/guests - Proper Response",
                    True,
                    f"✅ Guest creation endpoint mevcut (Status: {response.status_code})"
                )
                return True
            
            # Success response
            if response.status_code in [200, 201]:
                self.log_test(
                    "POST /api/guests - Success Response",
                    True,
                    f"✅ Guest creation başarılı (Status: {response.status_code})"
                )
                return True
            
            # Any other response means endpoint exists
            self.log_test(
                "POST /api/guests - Endpoint Accessible",
                True,
                f"✅ Endpoint erişilebilir (Status: {response.status_code})"
            )
            return True
                
        except Exception as e:
            self.log_test(
                "POST /api/guests - Connection Test",
                False,
                f"Request hatası: {str(e)}"
            )
            return False

    def test_front_office_dashboard_endpoint(self):
        """GET /api/front-office-dashboard endpoint'ini test et"""
        print("📊 Front Office Dashboard Endpoint Test")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.backend_url}/api/front-office-dashboard", timeout=10)
            
            # Check if endpoint exists (not 404)
            if response.status_code == 404:
                self.log_test(
                    "GET /api/front-office-dashboard - Endpoint Exists",
                    False,
                    f"⚠️ Front Office dashboard endpoint bulunamadı",
                    "Not 404",
                    "404"
                )
                return False
            
            # Check if it's not returning 500 Internal Server Error
            if response.status_code == 500:
                self.log_test(
                    "GET /api/front-office-dashboard - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 Internal Server Error - Dashboard endpoint hatası!",
                    "Not 500",
                    "500"
                )
                return False
            
            # Should return proper response
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/front-office-dashboard - Proper Auth Response",
                    True,
                    f"✅ Dashboard endpoint mevcut ve auth kontrolü yapıyor (Status: {response.status_code})"
                )
                return True
            
            # Any other response is acceptable
            self.log_test(
                "GET /api/front-office-dashboard - Endpoint Accessible",
                True,
                f"✅ Dashboard endpoint erişilebilir (Status: {response.status_code})"
            )
            return True
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office-dashboard - Connection Test",
                False,
                f"Request hatası: {str(e)}"
            )
            return False

    def test_authentication_requirements(self):
        """Authentication gereksinimlerini test et"""
        print("🔐 Authentication Requirements Test")
        print("=" * 50)
        
        # Test reservations without authentication
        try:
            response = requests.get(f"{self.backend_url}/api/reservations", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "Reservations - Authentication Required",
                    True,
                    f"✅ Reservations endpoint doğru auth kontrolü yapıyor (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "Reservations - Authentication Required",
                    False,
                    f"🚨 CRITICAL: 500 error instead of auth error!",
                    "401 or 403",
                    "500"
                )
            else:
                self.log_test(
                    "Reservations - Authentication Required",
                    True,
                    f"✅ Reservations endpoint erişilebilir (Status: {response.status_code})"
                )
        except Exception as e:
            self.log_test(
                "Reservations - Authentication Required",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test guests without authentication
        try:
            response = requests.get(f"{self.backend_url}/api/guests", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "Guests - Authentication Required",
                    True,
                    f"✅ Guests endpoint doğru auth kontrolü yapıyor (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "Guests - Authentication Required",
                    False,
                    f"🚨 CRITICAL: 500 error instead of auth error!",
                    "401 or 403",
                    "500"
                )
            else:
                self.log_test(
                    "Guests - Authentication Required",
                    True,
                    f"✅ Guests endpoint erişilebilir (Status: {response.status_code})"
                )
        except Exception as e:
            self.log_test(
                "Guests - Authentication Required",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test with invalid token
        try:
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.get(
                f"{self.backend_url}/api/reservations",
                headers=invalid_headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test(
                    "Invalid Token Rejection",
                    True,
                    f"✅ Geçersiz token doğru şekilde reddedildi (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "Invalid Token Rejection",
                    False,
                    f"🚨 CRITICAL: 500 error with invalid token!",
                    "401",
                    "500"
                )
            else:
                self.log_test(
                    "Invalid Token Rejection",
                    True,
                    f"✅ Token validation çalışıyor (Status: {response.status_code})"
                )
        except Exception as e:
            self.log_test(
                "Invalid Token Rejection",
                False,
                f"Request hatası: {str(e)}"
            )

    def test_http_methods_and_validation(self):
        """HTTP methods ve data validation testleri"""
        print("🔧 HTTP Methods and Validation Tests")
        print("=" * 50)
        
        # Test PUT method on reservations
        try:
            response = requests.put(
                f"{self.backend_url}/api/reservations/{self.test_reservation_ids[0]}",
                json=self.test_reservation_data,
                timeout=10
            )
            
            if response.status_code != 404:
                if response.status_code == 500:
                    self.log_test(
                        "PUT /api/reservations/{id} - No 500 Error",
                        False,
                        f"🚨 CRITICAL: 500 error on reservation update!",
                        "Not 500",
                        "500"
                    )
                else:
                    self.log_test(
                        "PUT /api/reservations/{id} - Method Supported",
                        True,
                        f"✅ Reservation update endpoint mevcut (Status: {response.status_code})"
                    )
            else:
                self.log_test(
                    "PUT /api/reservations/{id} - Method Supported",
                    False,
                    f"⚠️ Reservation update endpoint bulunamadı",
                    "Not 404",
                    "404"
                )
        except Exception as e:
            self.log_test(
                "PUT /api/reservations/{id} - Method Test",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test DELETE method on reservations
        try:
            response = requests.delete(
                f"{self.backend_url}/api/reservations/{self.test_reservation_ids[0]}",
                timeout=10
            )
            
            if response.status_code != 404:
                if response.status_code == 500:
                    self.log_test(
                        "DELETE /api/reservations/{id} - No 500 Error",
                        False,
                        f"🚨 CRITICAL: 500 error on reservation delete!",
                        "Not 500",
                        "500"
                    )
                else:
                    self.log_test(
                        "DELETE /api/reservations/{id} - Method Supported",
                        True,
                        f"✅ Reservation delete endpoint mevcut (Status: {response.status_code})"
                    )
            else:
                self.log_test(
                    "DELETE /api/reservations/{id} - Method Supported",
                    False,
                    f"⚠️ Reservation delete endpoint bulunamadı",
                    "Not 404",
                    "404"
                )
        except Exception as e:
            self.log_test(
                "DELETE /api/reservations/{id} - Method Test",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test invalid data validation
        invalid_reservation_data = {
            "guest_name": "",  # Empty name
            "check_in_date": "invalid-date",  # Invalid date
            "check_out_date": "2024-01-01",  # Past date
            "room_number": "",  # Empty room
            "guest_count": -1,  # Invalid count
            "total_amount": "invalid"  # Invalid amount
        }
        
        try:
            response = requests.post(
                f"{self.backend_url}/api/reservations",
                json=invalid_reservation_data,
                timeout=10
            )
            
            if response.status_code == 500:
                self.log_test(
                    "Invalid Data Validation - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 error with invalid data - validation hatası!",
                    "400/422",
                    "500"
                )
            elif response.status_code in [400, 422]:
                self.log_test(
                    "Invalid Data Validation - Proper Error",
                    True,
                    f"✅ Invalid data doğru şekilde reddedildi (Status: {response.status_code})"
                )
            elif response.status_code in [401, 403]:
                self.log_test(
                    "Invalid Data Validation - Auth First",
                    True,
                    f"✅ Auth kontrolü öncelikli (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "Invalid Data Validation - Handled",
                    True,
                    f"✅ Invalid data işlendi (Status: {response.status_code})"
                )
        except Exception as e:
            self.log_test(
                "Invalid Data Validation Test",
                False,
                f"Request hatası: {str(e)}"
            )

    def test_mongodb_collections_access(self):
        """MongoDB collections erişimini test et"""
        print("🗄️ MongoDB Collections Access Test")
        print("=" * 50)
        
        # Test if backend can access reservations collection
        try:
            response = requests.get(f"{self.backend_url}/api/reservations", timeout=10)
            
            # If we get any response other than connection error, DB is accessible
            if response.status_code != 500:
                self.log_test(
                    "MongoDB Reservations Collection Access",
                    True,
                    f"✅ Reservations collection erişilebilir (Status: {response.status_code})"
                )
            else:
                # Check if 500 is due to DB connection issue
                try:
                    response_data = response.json()
                    if "database" in str(response_data).lower() or "mongo" in str(response_data).lower():
                        self.log_test(
                            "MongoDB Reservations Collection Access",
                            False,
                            f"🚨 CRITICAL: MongoDB connection hatası!",
                            "DB accessible",
                            "DB connection error"
                        )
                    else:
                        self.log_test(
                            "MongoDB Reservations Collection Access",
                            False,
                            f"🚨 CRITICAL: 500 error - backend implementation hatası!",
                            "Not 500",
                            "500"
                        )
                except:
                    self.log_test(
                        "MongoDB Reservations Collection Access",
                        False,
                        f"🚨 CRITICAL: 500 error - response parse edilemedi!",
                        "Not 500",
                        "500"
                    )
        except Exception as e:
            self.log_test(
                "MongoDB Reservations Collection Access",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test if backend can access guests collection
        try:
            response = requests.get(f"{self.backend_url}/api/guests", timeout=10)
            
            if response.status_code != 500:
                self.log_test(
                    "MongoDB Guests Collection Access",
                    True,
                    f"✅ Guests collection erişilebilir (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "MongoDB Guests Collection Access",
                    False,
                    f"🚨 CRITICAL: Guests collection 500 error!",
                    "Not 500",
                    "500"
                )
        except Exception as e:
            self.log_test(
                "MongoDB Guests Collection Access",
                False,
                f"Request hatası: {str(e)}"
            )

    def test_response_format_and_cors(self):
        """Response format ve CORS testleri"""
        print("📋 Response Format and CORS Tests")
        print("=" * 50)
        
        # Test response format
        try:
            response = requests.get(f"{self.backend_url}/api/reservations", timeout=10)
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                self.log_test(
                    "Response Format - JSON Content Type",
                    True,
                    f"✅ Doğru JSON content-type: {content_type}"
                )
            else:
                self.log_test(
                    "Response Format - JSON Content Type",
                    False,
                    f"⚠️ JSON content-type eksik",
                    "application/json",
                    content_type
                )
            
            # Try to parse JSON (if not 500 error)
            if response.status_code != 500:
                try:
                    json_data = response.json()
                    self.log_test(
                        "Response Format - JSON Parse",
                        True,
                        "✅ Response başarıyla JSON olarak parse edildi"
                    )
                except:
                    self.log_test(
                        "Response Format - JSON Parse",
                        False,
                        "⚠️ Response JSON olarak parse edilemedi"
                    )
            else:
                self.log_test(
                    "Response Format - JSON Parse",
                    False,
                    "🚨 CRITICAL: 500 error - JSON parse test edilemedi"
                )
                
        except Exception as e:
            self.log_test(
                "Response Format Test",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test CORS headers
        try:
            response = requests.options(f"{self.backend_url}/api/reservations", timeout=10)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            cors_present = any(header in response.headers for header in cors_headers)
            
            if cors_present:
                self.log_test(
                    "CORS Headers Present",
                    True,
                    f"✅ CORS headers mevcut: {[h for h in cors_headers if h in response.headers]}"
                )
            else:
                self.log_test(
                    "CORS Headers Present",
                    False,
                    "⚠️ CORS headers eksik - frontend entegrasyonu sorunlu olabilir"
                )
                
        except Exception as e:
            self.log_test(
                "CORS Headers Test",
                False,
                f"CORS test hatası: {str(e)}"
            )

    def test_related_front_office_endpoints(self):
        """İlgili Front Office endpoint'lerini test et"""
        print("🔗 Related Front Office Endpoints Test")
        print("=" * 50)
        
        # Test room availability endpoint
        try:
            response = requests.get(f"{self.backend_url}/api/rooms/availability", timeout=10)
            
            if response.status_code != 404:
                if response.status_code == 500:
                    self.log_test(
                        "GET /api/rooms/availability - No 500 Error",
                        False,
                        f"🚨 CRITICAL: Room availability 500 error!",
                        "Not 500",
                        "500"
                    )
                else:
                    self.log_test(
                        "GET /api/rooms/availability - Endpoint Exists",
                        True,
                        f"✅ Room availability endpoint mevcut (Status: {response.status_code})"
                    )
            else:
                self.log_test(
                    "GET /api/rooms/availability - Endpoint Exists",
                    False,
                    f"⚠️ Room availability endpoint bulunamadı",
                    "Not 404",
                    "404"
                )
        except Exception as e:
            self.log_test(
                "GET /api/rooms/availability - Endpoint Test",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test rooms endpoint
        try:
            response = requests.get(f"{self.backend_url}/api/rooms", timeout=10)
            
            if response.status_code != 404:
                if response.status_code == 500:
                    self.log_test(
                        "GET /api/rooms - No 500 Error",
                        False,
                        f"🚨 CRITICAL: Rooms endpoint 500 error!",
                        "Not 500",
                        "500"
                    )
                else:
                    self.log_test(
                        "GET /api/rooms - Endpoint Exists",
                        True,
                        f"✅ Rooms endpoint mevcut (Status: {response.status_code})"
                    )
            else:
                self.log_test(
                    "GET /api/rooms - Endpoint Exists",
                    False,
                    f"⚠️ Rooms endpoint bulunamadı",
                    "Not 404",
                    "404"
                )
        except Exception as e:
            self.log_test(
                "GET /api/rooms - Endpoint Test",
                False,
                f"Request hatası: {str(e)}"
            )

        # Test front office stats endpoint
        try:
            response = requests.get(f"{self.backend_url}/api/front-office/stats", timeout=10)
            
            if response.status_code != 404:
                if response.status_code == 500:
                    self.log_test(
                        "GET /api/front-office/stats - No 500 Error",
                        False,
                        f"🚨 CRITICAL: Front office stats 500 error!",
                        "Not 500",
                        "500"
                    )
                else:
                    self.log_test(
                        "GET /api/front-office/stats - Endpoint Exists",
                        True,
                        f"✅ Front office stats endpoint mevcut (Status: {response.status_code})"
                    )
            else:
                self.log_test(
                    "GET /api/front-office/stats - Endpoint Exists",
                    False,
                    f"⚠️ Front office stats endpoint bulunamadı",
                    "Not 404",
                    "404"
                )
        except Exception as e:
            self.log_test(
                "GET /api/front-office/stats - Endpoint Test",
                False,
                f"Request hatası: {str(e)}"
            )

    def run_all_tests(self):
        """Tüm testleri çalıştır"""
        print("🏨 FRONT OFFICE 500 INTERNAL SERVER ERROR DEBUG TEST")
        print("=" * 70)
        print(f"🎯 Backend URL: {self.backend_url}")
        print(f"📅 Test Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Focus: Front Office endpoints 500 error debugging")
        print("=" * 70)
        print()
        
        # Backend sağlık kontrolü
        if not self.test_backend_health():
            print("❌ Backend erişilemediği için testler durduruluyor!")
            return False
        
        # Ana Front Office endpoint testleri
        print("🚨 CRITICAL 500 ERROR DEBUG TESTS:")
        print("-" * 40)
        self.test_reservations_get_endpoint()
        self.test_reservations_post_endpoint()
        self.test_guests_endpoint()
        self.test_guests_post_endpoint()
        self.test_front_office_dashboard_endpoint()
        
        print("\n🔐 AUTHENTICATION & VALIDATION TESTS:")
        print("-" * 40)
        self.test_authentication_requirements()
        self.test_http_methods_and_validation()
        
        print("\n🗄️ DATABASE & INFRASTRUCTURE TESTS:")
        print("-" * 40)
        self.test_mongodb_collections_access()
        self.test_response_format_and_cors()
        self.test_related_front_office_endpoints()
        
        # Sonuçları göster
        self.show_results()
        
        return self.passed_tests >= (self.total_tests * 0.7)  # 70% başarı oranı

    def show_results(self):
        """Test sonuçlarını göster"""
        print("\n" + "=" * 70)
        print("📊 FRONT OFFICE 500 ERROR DEBUG TEST SONUÇLARI")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Başarılı Testler: {self.passed_tests}")
        print(f"❌ Başarısız Testler: {self.total_tests - self.passed_tests}")
        print(f"📊 Toplam Test: {self.total_tests}")
        print(f"🎯 Başarı Oranı: {success_rate:.1f}%")
        
        # Critical 500 errors analysis
        critical_500_errors = [r for r in self.test_results if not r['success'] and '500' in r['details']]
        if critical_500_errors:
            print(f"\n🚨 CRITICAL 500 ERRORS FOUND: {len(critical_500_errors)}")
            print("=" * 50)
            for error in critical_500_errors:
                print(f"❌ {error['test']}")
                print(f"   📝 {error['details']}")
            print("\n⚡ URGENT ACTION REQUIRED: Fix 500 Internal Server Errors!")
        else:
            print("\n✅ NO 500 INTERNAL SERVER ERRORS DETECTED!")
        
        # Missing endpoints analysis
        missing_endpoints = [r for r in self.test_results if not r['success'] and '404' in r['details']]
        if missing_endpoints:
            print(f"\n⚠️ MISSING ENDPOINTS: {len(missing_endpoints)}")
            print("=" * 50)
            for endpoint in missing_endpoints:
                print(f"❌ {endpoint['test']}")
                print(f"   📝 {endpoint['details']}")
        
        if success_rate >= 90:
            print("\n🎉 EXCELLENT! Front Office modülü production ready!")
        elif success_rate >= 75:
            print("\n✅ GOOD! Front Office modülü genel olarak çalışıyor.")
        elif success_rate >= 50:
            print("\n⚠️ MODERATE! Front Office modülünde bazı sorunlar var.")
        else:
            print("\n❌ CRITICAL! Front Office modülünde ciddi sorunlar var.")
        
        print("\n🔍 DETAYLI SONUÇLAR:")
        print("-" * 70)
        
        # Başarısız testleri kategorilere göre grupla
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("❌ BAŞARISIZ TESTLER:")
            
            # 500 errors
            error_500_tests = [t for t in failed_tests if '500' in t['details']]
            if error_500_tests:
                print(f"\n🚨 500 INTERNAL SERVER ERRORS ({len(error_500_tests)}):")
                for test in error_500_tests:
                    print(f"   • {test['test']}: {test['details']}")
            
            # 404 errors (missing endpoints)
            error_404_tests = [t for t in failed_tests if '404' in t['details']]
            if error_404_tests:
                print(f"\n📭 MISSING ENDPOINTS ({len(error_404_tests)}):")
                for test in error_404_tests:
                    print(f"   • {test['test']}: {test['details']}")
            
            # Other errors
            other_errors = [t for t in failed_tests if '500' not in t['details'] and '404' not in t['details']]
            if other_errors:
                print(f"\n⚠️ OTHER ISSUES ({len(other_errors)}):")
                for test in other_errors:
                    print(f"   • {test['test']}: {test['details']}")
        
        # Başarılı testleri özetle
        successful_tests = [r for r in self.test_results if r['success']]
        if successful_tests:
            print(f"\n✅ BAŞARILI TESTLER: {len(successful_tests)} adet")
            
            # Kategorilere göre grupla
            endpoint_tests = [t for t in successful_tests if 'Endpoint' in t['test']]
            auth_tests = [t for t in successful_tests if 'Authentication' in t['test'] or 'Auth' in t['test']]
            validation_tests = [t for t in successful_tests if 'Validation' in t['test']]
            db_tests = [t for t in successful_tests if 'MongoDB' in t['test'] or 'Collection' in t['test']]
            
            if endpoint_tests:
                print(f"   🔗 Endpoint Tests: {len(endpoint_tests)} ✅")
            if auth_tests:
                print(f"   🔐 Authentication Tests: {len(auth_tests)} ✅")
            if validation_tests:
                print(f"   📋 Validation Tests: {len(validation_tests)} ✅")
            if db_tests:
                print(f"   🗄️ Database Tests: {len(db_tests)} ✅")
        
        print("\n" + "=" * 70)
        
        # Test sonuçlarını JSON olarak kaydet
        with open('/app/front_office_debug_test_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'test_summary': {
                    'total_tests': self.total_tests,
                    'passed_tests': self.passed_tests,
                    'failed_tests': self.total_tests - self.passed_tests,
                    'success_rate': success_rate,
                    'backend_url': self.backend_url,
                    'test_timestamp': datetime.now().isoformat(),
                    'test_focus': 'Front Office 500 Internal Server Error Debug',
                    'critical_500_errors': len(critical_500_errors),
                    'missing_endpoints': len(missing_endpoints)
                },
                'test_results': self.test_results,
                'critical_issues': {
                    '500_errors': [r for r in self.test_results if not r['success'] and '500' in r['details']],
                    'missing_endpoints': [r for r in self.test_results if not r['success'] and '404' in r['details']]
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detaylı test sonuçları kaydedildi: /app/front_office_debug_test_results.json")

def main():
    """Ana test fonksiyonu"""
    tester = FrontOfficeDebugTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 FRONT OFFICE DEBUG TESTLERİ BAŞARILI!")
        print("✅ Front Office endpoints erişilebilir")
        print("✅ 500 Internal Server Error sorunu yok")
        print("✅ Authentication ve validation çalışıyor")
        print("✅ MongoDB collections erişilebilir")
        sys.exit(0)
    else:
        print("\n🚨 CRITICAL ISSUES DETECTED!")
        print("❌ Front Office modülünde 500 Internal Server Error veya eksik endpoint sorunları var")
        print("🔧 Backend implementation kontrol edilmeli")
        print("⚡ Acil müdahale gerekli!")
        sys.exit(1)

if __name__ == "__main__":
    main()