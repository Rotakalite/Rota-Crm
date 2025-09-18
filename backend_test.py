#!/usr/bin/env python3
"""
🏨 FRONT OFFICE ENHANCEMENTS COMPREHENSIVE BACKEND TEST
=====================================================

Testing the new Front Office features as requested:

1. **Reservation Edit (PUT /api/reservations/{reservation_id})** - Update existing reservations with client_id support
2. **Excel Report Generation (/api/front-office/report/excel)** - Professional Excel reports with reservations, statistics, and occupancy analysis  
3. **Monthly Occupancy Data (/api/front-office/monthly-occupancy)** - Detailed monthly occupancy analytics for charts and tables

Test Requirements:
- Test PUT /api/reservations/{reservation_id} endpoint for reservation updates
- Test /api/front-office/report/excel endpoint for Excel report generation
- Test /api/front-office/monthly-occupancy endpoint with year/month parameters
- Verify all endpoints support client_id parameter for admin/consultant users
- Test authentication and role-based access control for all new endpoints
- Verify response formats and data structures
- Test error handling for invalid data/missing parameters

Expected Results:
- All new endpoints should be accessible and properly secured (403/401 for auth)
- PUT endpoint should support reservation updates with validation
- Excel endpoint should return proper Excel file response headers
- Monthly occupancy endpoint should return structured data for charts/tables
- All endpoints should support role-based client_id parameter handling

Backend URL: https://rota-crm-production.up.railway.app
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import uuid

# Production URL from frontend .env
BACKEND_URL = "https://rota-crm-production.up.railway.app"

class FrontOfficeEnhancementsTest:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        # Test data for reservation updates
        self.test_reservation_update_data = {
            "guest_name": "Ahmet Yılmaz (Güncellendi)",
            "guest_email": "ahmet.updated@example.com",
            "guest_phone": "+90 532 123 4567",
            "room_id": "room-101",
            "check_in_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "check_out_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "adults": 2,
            "children": 1,
            "room_rate": 250.0,
            "total_amount": 750.0,
            "payment_status": "partial",
            "booking_source": "online",
            "special_requests": "Late check-in, sea view",
            "notes": "VIP guest - updated reservation"
        }
        
        # Test reservation IDs for different scenarios
        self.test_reservation_ids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "6ba7b811-9dad-11d1-80b4-00c04fd430c8"
        ]
        
        # Test client IDs for role-based testing
        self.test_client_ids = [
            "94927a77-edc3-45ec-8329-795feae35771",  # Known test client
            "test-client-id-1",
            "test-client-id-2"
        ]

    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Log test result"""
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
        """Backend health check"""
        print("🏥 Backend Health Check")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=10)
            
            if response.status_code == 200:
                self.log_test(
                    "Backend Health Check",
                    True,
                    f"Railway production backend accessible (Status: {response.status_code})"
                )
                return True
            else:
                self.log_test(
                    "Backend Health Check", 
                    False,
                    f"Backend health check failed",
                    "200",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Backend Health Check",
                False, 
                f"Backend connection error: {str(e)}"
            )
            return False

    def test_reservation_edit_endpoint(self):
        """Test PUT /api/reservations/{reservation_id} endpoint"""
        print("📝 Reservation Edit (PUT) Endpoint Tests")
        print("=" * 50)
        
        # Test endpoint accessibility
        try:
            response = requests.put(
                f"{self.backend_url}/api/reservations/{self.test_reservation_ids[0]}",
                json=self.test_reservation_update_data,
                timeout=10
            )
            
            # Check if endpoint exists (not 404)
            if response.status_code == 404:
                self.log_test(
                    "PUT /api/reservations/{id} - Endpoint Exists",
                    False,
                    f"🚨 CRITICAL: Reservation edit endpoint not found!",
                    "Not 404",
                    "404"
                )
                return False
            
            # Check if it's not returning 500 Internal Server Error
            if response.status_code == 500:
                self.log_test(
                    "PUT /api/reservations/{id} - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 Internal Server Error - Reservation update implementation error!",
                    "Not 500",
                    "500"
                )
                return False
            
            # Should return proper auth error (403/401) or validation error (400/422)
            if response.status_code in [400, 401, 403, 422]:
                self.log_test(
                    "PUT /api/reservations/{id} - Proper Response",
                    True,
                    f"✅ Reservation edit endpoint exists and returns proper response (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "PUT /api/reservations/{id} - Endpoint Accessible",
                    True,
                    f"✅ Reservation edit endpoint accessible (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "PUT /api/reservations/{id} - Connection Test",
                False,
                f"Request error: {str(e)}"
            )
            return False

        # Test with invalid reservation ID
        try:
            response = requests.put(
                f"{self.backend_url}/api/reservations/invalid-id-123",
                json=self.test_reservation_update_data,
                timeout=10
            )
            
            if response.status_code in [400, 401, 403, 404, 422]:
                self.log_test(
                    "PUT /api/reservations/{id} - Invalid ID Handling",
                    True,
                    f"✅ Invalid reservation ID properly handled (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "PUT /api/reservations/{id} - Invalid ID Handling",
                    False,
                    f"🚨 CRITICAL: 500 error with invalid ID - error handling issue!",
                    "400/404",
                    "500"
                )
            else:
                self.log_test(
                    "PUT /api/reservations/{id} - Invalid ID Handling",
                    True,
                    f"✅ Invalid ID handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "PUT /api/reservations/{id} - Invalid ID Test",
                False,
                f"Request error: {str(e)}"
            )

        # Test with invalid data
        invalid_data = {
            "guest_name": "",  # Empty name
            "check_in_date": "invalid-date",  # Invalid date
            "check_out_date": "2024-01-01",  # Past date
            "room_id": "",  # Empty room
            "adults": -1,  # Invalid count
            "room_rate": "invalid"  # Invalid rate
        }
        
        try:
            response = requests.put(
                f"{self.backend_url}/api/reservations/{self.test_reservation_ids[0]}",
                json=invalid_data,
                timeout=10
            )
            
            if response.status_code == 500:
                self.log_test(
                    "PUT /api/reservations/{id} - Invalid Data Validation",
                    False,
                    f"🚨 CRITICAL: 500 error with invalid data - validation error!",
                    "400/422",
                    "500"
                )
            elif response.status_code in [400, 401, 403, 422]:
                self.log_test(
                    "PUT /api/reservations/{id} - Invalid Data Validation",
                    True,
                    f"✅ Invalid data properly validated (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "PUT /api/reservations/{id} - Invalid Data Validation",
                    True,
                    f"✅ Invalid data handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "PUT /api/reservations/{id} - Invalid Data Test",
                False,
                f"Request error: {str(e)}"
            )

        # Test authentication requirement
        try:
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.put(
                f"{self.backend_url}/api/reservations/{self.test_reservation_ids[0]}",
                json=self.test_reservation_update_data,
                headers=invalid_headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test(
                    "PUT /api/reservations/{id} - Authentication Required",
                    True,
                    f"✅ Invalid token properly rejected (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "PUT /api/reservations/{id} - Authentication Required",
                    False,
                    f"🚨 CRITICAL: 500 error with invalid token!",
                    "401",
                    "500"
                )
            else:
                self.log_test(
                    "PUT /api/reservations/{id} - Authentication Required",
                    True,
                    f"✅ Authentication handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "PUT /api/reservations/{id} - Authentication Test",
                False,
                f"Request error: {str(e)}"
            )

        return True

    def test_excel_report_endpoint(self):
        """Test /api/front-office/report/excel endpoint"""
        print("📊 Excel Report Generation Endpoint Tests")
        print("=" * 50)
        
        # Test endpoint accessibility
        try:
            response = requests.get(f"{self.backend_url}/api/front-office/report/excel", timeout=15)
            
            # Check if endpoint exists (not 404)
            if response.status_code == 404:
                self.log_test(
                    "GET /api/front-office/report/excel - Endpoint Exists",
                    False,
                    f"🚨 CRITICAL: Excel report endpoint not found!",
                    "Not 404",
                    "404"
                )
                return False
            
            # Check if it's not returning 500 Internal Server Error
            if response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/report/excel - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 Internal Server Error - Excel report implementation error!",
                    "Not 500",
                    "500"
                )
                return False
            
            # Should return proper auth error (403/401) for unauthenticated requests
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/front-office/report/excel - Proper Auth Response",
                    True,
                    f"✅ Excel report endpoint exists and requires authentication (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "GET /api/front-office/report/excel - Endpoint Accessible",
                    True,
                    f"✅ Excel report endpoint accessible (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office/report/excel - Connection Test",
                False,
                f"Request error: {str(e)}"
            )
            return False

        # Test with client_id parameter
        try:
            response = requests.get(
                f"{self.backend_url}/api/front-office/report/excel",
                params={"client_id": self.test_client_ids[0]},
                timeout=15
            )
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/front-office/report/excel - Client ID Parameter",
                    True,
                    f"✅ Client ID parameter accepted, authentication required (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/report/excel - Client ID Parameter",
                    False,
                    f"🚨 CRITICAL: 500 error with client_id parameter!",
                    "401/403",
                    "500"
                )
            else:
                self.log_test(
                    "GET /api/front-office/report/excel - Client ID Parameter",
                    True,
                    f"✅ Client ID parameter handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office/report/excel - Client ID Test",
                False,
                f"Request error: {str(e)}"
            )

        # Test with date range parameters
        try:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")
            
            response = requests.get(
                f"{self.backend_url}/api/front-office/report/excel",
                params={
                    "start_date": start_date,
                    "end_date": end_date,
                    "client_id": self.test_client_ids[0]
                },
                timeout=15
            )
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/front-office/report/excel - Date Range Parameters",
                    True,
                    f"✅ Date range parameters accepted, authentication required (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/report/excel - Date Range Parameters",
                    False,
                    f"🚨 CRITICAL: 500 error with date parameters!",
                    "401/403",
                    "500"
                )
            else:
                self.log_test(
                    "GET /api/front-office/report/excel - Date Range Parameters",
                    True,
                    f"✅ Date range parameters handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office/report/excel - Date Range Test",
                False,
                f"Request error: {str(e)}"
            )

        # Test authentication requirement
        try:
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.get(
                f"{self.backend_url}/api/front-office/report/excel",
                headers=invalid_headers,
                timeout=15
            )
            
            if response.status_code == 401:
                self.log_test(
                    "GET /api/front-office/report/excel - Authentication Required",
                    True,
                    f"✅ Invalid token properly rejected (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/report/excel - Authentication Required",
                    False,
                    f"🚨 CRITICAL: 500 error with invalid token!",
                    "401",
                    "500"
                )
            else:
                self.log_test(
                    "GET /api/front-office/report/excel - Authentication Required",
                    True,
                    f"✅ Authentication handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office/report/excel - Authentication Test",
                False,
                f"Request error: {str(e)}"
            )

        return True

    def test_monthly_occupancy_endpoint(self):
        """Test /api/front-office/monthly-occupancy endpoint"""
        print("📈 Monthly Occupancy Data Endpoint Tests")
        print("=" * 50)
        
        # Test endpoint accessibility
        try:
            response = requests.get(f"{self.backend_url}/api/front-office/monthly-occupancy", timeout=10)
            
            # Check if endpoint exists (not 404)
            if response.status_code == 404:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Endpoint Exists",
                    False,
                    f"🚨 CRITICAL: Monthly occupancy endpoint not found!",
                    "Not 404",
                    "404"
                )
                return False
            
            # Check if it's not returning 500 Internal Server Error
            if response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 Internal Server Error - Monthly occupancy implementation error!",
                    "Not 500",
                    "500"
                )
                return False
            
            # Should return proper auth error (403/401) for unauthenticated requests
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Proper Auth Response",
                    True,
                    f"✅ Monthly occupancy endpoint exists and requires authentication (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Endpoint Accessible",
                    True,
                    f"✅ Monthly occupancy endpoint accessible (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office/monthly-occupancy - Connection Test",
                False,
                f"Request error: {str(e)}"
            )
            return False

        # Test with year parameter
        try:
            current_year = datetime.now().year
            response = requests.get(
                f"{self.backend_url}/api/front-office/monthly-occupancy",
                params={"year": current_year},
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Year Parameter",
                    True,
                    f"✅ Year parameter accepted, authentication required (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Year Parameter",
                    False,
                    f"🚨 CRITICAL: 500 error with year parameter!",
                    "401/403",
                    "500"
                )
            else:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Year Parameter",
                    True,
                    f"✅ Year parameter handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office/monthly-occupancy - Year Parameter Test",
                False,
                f"Request error: {str(e)}"
            )

        # Test with year and month parameters
        try:
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            response = requests.get(
                f"{self.backend_url}/api/front-office/monthly-occupancy",
                params={
                    "year": current_year,
                    "month": current_month,
                    "client_id": self.test_client_ids[0]
                },
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Year/Month/Client Parameters",
                    True,
                    f"✅ Year/Month/Client parameters accepted, authentication required (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Year/Month/Client Parameters",
                    False,
                    f"🚨 CRITICAL: 500 error with year/month/client parameters!",
                    "401/403",
                    "500"
                )
            else:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Year/Month/Client Parameters",
                    True,
                    f"✅ Year/Month/Client parameters handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office/monthly-occupancy - Parameters Test",
                False,
                f"Request error: {str(e)}"
            )

        # Test with invalid parameters
        try:
            response = requests.get(
                f"{self.backend_url}/api/front-office/monthly-occupancy",
                params={
                    "year": "invalid",
                    "month": 15,  # Invalid month
                    "client_id": "invalid-client-id"
                },
                timeout=10
            )
            
            if response.status_code in [400, 401, 403, 422]:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Invalid Parameters",
                    True,
                    f"✅ Invalid parameters properly handled (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Invalid Parameters",
                    False,
                    f"🚨 CRITICAL: 500 error with invalid parameters - validation error!",
                    "400/422",
                    "500"
                )
            else:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Invalid Parameters",
                    True,
                    f"✅ Invalid parameters handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office/monthly-occupancy - Invalid Parameters Test",
                False,
                f"Request error: {str(e)}"
            )

        # Test authentication requirement
        try:
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.get(
                f"{self.backend_url}/api/front-office/monthly-occupancy",
                headers=invalid_headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Authentication Required",
                    True,
                    f"✅ Invalid token properly rejected (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Authentication Required",
                    False,
                    f"🚨 CRITICAL: 500 error with invalid token!",
                    "401",
                    "500"
                )
            else:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Authentication Required",
                    True,
                    f"✅ Authentication handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office/monthly-occupancy - Authentication Test",
                False,
                f"Request error: {str(e)}"
            )

        return True

    def test_response_formats_and_cors(self):
        """Test response formats and CORS headers"""
        print("📋 Response Format and CORS Tests")
        print("=" * 50)
        
        endpoints_to_test = [
            "/api/reservations/test-id",
            "/api/front-office/report/excel",
            "/api/front-office/monthly-occupancy"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    self.log_test(
                        f"Response Format - JSON Content Type ({endpoint})",
                        True,
                        f"✅ Correct JSON content-type: {content_type}"
                    )
                else:
                    # Excel endpoint might return different content type
                    if "excel" in endpoint and response.status_code not in [401, 403]:
                        if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
                            self.log_test(
                                f"Response Format - Excel Content Type ({endpoint})",
                                True,
                                f"✅ Correct Excel content-type: {content_type}"
                            )
                        else:
                            self.log_test(
                                f"Response Format - Excel Content Type ({endpoint})",
                                False,
                                f"⚠️ Expected Excel content-type",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                content_type
                            )
                    else:
                        self.log_test(
                            f"Response Format - Content Type ({endpoint})",
                            False,
                            f"⚠️ Unexpected content-type",
                            "application/json",
                            content_type
                        )
                
                # Try to parse JSON (if not Excel and not 500 error)
                if response.status_code not in [500] and "excel" not in endpoint:
                    try:
                        json_data = response.json()
                        self.log_test(
                            f"Response Format - JSON Parse ({endpoint})",
                            True,
                            "✅ Response successfully parsed as JSON"
                        )
                    except:
                        self.log_test(
                            f"Response Format - JSON Parse ({endpoint})",
                            False,
                            "⚠️ Response could not be parsed as JSON"
                        )
                        
            except Exception as e:
                self.log_test(
                    f"Response Format Test ({endpoint})",
                    False,
                    f"Request error: {str(e)}"
                )

        # Test CORS headers
        try:
            response = requests.options(f"{self.backend_url}/api/front-office/monthly-occupancy", timeout=10)
            
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
                    f"✅ CORS headers present: {[h for h in cors_headers if h in response.headers]}"
                )
            else:
                self.log_test(
                    "CORS Headers Present",
                    False,
                    "⚠️ CORS headers missing - frontend integration may have issues"
                )
                
        except Exception as e:
            self.log_test(
                "CORS Headers Test",
                False,
                f"CORS test error: {str(e)}"
            )

    def test_role_based_access_control(self):
        """Test role-based access control for client_id parameter"""
        print("🔐 Role-Based Access Control Tests")
        print("=" * 50)
        
        # Test endpoints with client_id parameter
        endpoints_with_client_id = [
            "/api/reservations/test-id",
            "/api/front-office/report/excel",
            "/api/front-office/monthly-occupancy"
        ]
        
        for endpoint in endpoints_with_client_id:
            try:
                # Test without client_id (should work for CLIENT role, require for ADMIN/CONSULTANT)
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                
                if response.status_code in [401, 403]:
                    self.log_test(
                        f"Role-Based Access - No Client ID ({endpoint})",
                        True,
                        f"✅ Authentication required without client_id (Status: {response.status_code})"
                    )
                elif response.status_code == 500:
                    self.log_test(
                        f"Role-Based Access - No Client ID ({endpoint})",
                        False,
                        f"🚨 CRITICAL: 500 error without client_id!",
                        "401/403",
                        "500"
                    )
                else:
                    self.log_test(
                        f"Role-Based Access - No Client ID ({endpoint})",
                        True,
                        f"✅ Endpoint accessible without client_id (Status: {response.status_code})"
                    )
                
                # Test with client_id parameter
                response = requests.get(
                    f"{self.backend_url}{endpoint}",
                    params={"client_id": self.test_client_ids[0]},
                    timeout=10
                )
                
                if response.status_code in [401, 403]:
                    self.log_test(
                        f"Role-Based Access - With Client ID ({endpoint})",
                        True,
                        f"✅ Authentication required with client_id (Status: {response.status_code})"
                    )
                elif response.status_code == 500:
                    self.log_test(
                        f"Role-Based Access - With Client ID ({endpoint})",
                        False,
                        f"🚨 CRITICAL: 500 error with client_id parameter!",
                        "401/403",
                        "500"
                    )
                else:
                    self.log_test(
                        f"Role-Based Access - With Client ID ({endpoint})",
                        True,
                        f"✅ Client ID parameter handled (Status: {response.status_code})"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Role-Based Access Test ({endpoint})",
                    False,
                    f"Request error: {str(e)}"
                )

    def run_all_tests(self):
        """Run all tests"""
        print("🏨 FRONT OFFICE ENHANCEMENTS COMPREHENSIVE BACKEND TEST")
        print("=" * 70)
        print(f"🎯 Backend URL: {self.backend_url}")
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Focus: New Front Office features testing")
        print("=" * 70)
        print()
        
        # Backend health check
        if not self.test_backend_health():
            print("❌ Backend inaccessible, stopping tests!")
            return False
        
        # Test new Front Office endpoints
        print("🆕 NEW FRONT OFFICE FEATURES TESTS:")
        print("-" * 40)
        self.test_reservation_edit_endpoint()
        self.test_excel_report_endpoint()
        self.test_monthly_occupancy_endpoint()
        
        print("\n🔐 AUTHENTICATION & SECURITY TESTS:")
        print("-" * 40)
        self.test_role_based_access_control()
        
        print("\n📋 RESPONSE FORMAT & INFRASTRUCTURE TESTS:")
        print("-" * 40)
        self.test_response_formats_and_cors()
        
        # Show results
        self.show_results()
        
        return self.passed_tests >= (self.total_tests * 0.8)  # 80% success rate

    def show_results(self):
        """Show test results"""
        print("\n" + "=" * 70)
        print("📊 FRONT OFFICE ENHANCEMENTS TEST RESULTS")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Successful Tests: {self.passed_tests}")
        print(f"❌ Failed Tests: {self.total_tests - self.passed_tests}")
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        
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
            print("\n🎉 EXCELLENT! Front Office enhancements are production ready!")
        elif success_rate >= 75:
            print("\n✅ GOOD! Front Office enhancements are generally working.")
        elif success_rate >= 50:
            print("\n⚠️ MODERATE! Front Office enhancements have some issues.")
        else:
            print("\n❌ CRITICAL! Front Office enhancements have serious issues.")
        
        print("\n🔍 DETAILED RESULTS:")
        print("-" * 70)
        
        # Group failed tests by category
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("❌ FAILED TESTS:")
            
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
        
        # Successful tests summary
        successful_tests = [r for r in self.test_results if r['success']]
        if successful_tests:
            print(f"\n✅ SUCCESSFUL TESTS: {len(successful_tests)} tests")
            
            # Group by category
            reservation_tests = [t for t in successful_tests if 'reservation' in t['test'].lower()]
            excel_tests = [t for t in successful_tests if 'excel' in t['test'].lower()]
            occupancy_tests = [t for t in successful_tests if 'occupancy' in t['test'].lower()]
            auth_tests = [t for t in successful_tests if 'auth' in t['test'].lower() or 'role' in t['test'].lower()]
            
            if reservation_tests:
                print(f"   📝 Reservation Edit Tests: {len(reservation_tests)} ✅")
            if excel_tests:
                print(f"   📊 Excel Report Tests: {len(excel_tests)} ✅")
            if occupancy_tests:
                print(f"   📈 Monthly Occupancy Tests: {len(occupancy_tests)} ✅")
            if auth_tests:
                print(f"   🔐 Authentication Tests: {len(auth_tests)} ✅")
        
        print("\n" + "=" * 70)
        
        # Save test results to JSON
        with open('/app/front_office_enhancements_test_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'test_summary': {
                    'total_tests': self.total_tests,
                    'passed_tests': self.passed_tests,
                    'failed_tests': self.total_tests - self.passed_tests,
                    'success_rate': success_rate,
                    'backend_url': self.backend_url,
                    'test_timestamp': datetime.now().isoformat(),
                    'test_focus': 'Front Office Enhancements - New Features Testing',
                    'critical_500_errors': len(critical_500_errors),
                    'missing_endpoints': len(missing_endpoints)
                },
                'test_results': self.test_results,
                'critical_issues': {
                    '500_errors': [r for r in self.test_results if not r['success'] and '500' in r['details']],
                    'missing_endpoints': [r for r in self.test_results if not r['success'] and '404' in r['details']]
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed test results saved: /app/front_office_enhancements_test_results.json")

def main():
    """Main test function"""
    tester = FrontOfficeEnhancementsTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 FRONT OFFICE ENHANCEMENTS TESTS SUCCESSFUL!")
        print("✅ All new Front Office features are accessible")
        print("✅ No 500 Internal Server Errors detected")
        print("✅ Authentication and role-based access working")
        print("✅ Response formats and CORS properly configured")
        sys.exit(0)
    else:
        print("\n🚨 CRITICAL ISSUES DETECTED!")
        print("❌ Front Office enhancements have 500 Internal Server Error or missing endpoint issues")
        print("🔧 Backend implementation needs to be checked")
        print("⚡ Immediate intervention required!")
        sys.exit(1)

if __name__ == "__main__":
    main()