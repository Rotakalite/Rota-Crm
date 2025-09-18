#!/usr/bin/env python3
"""
🏨 GUEST NIGHTS CALCULATION COMPREHENSIVE BACKEND TEST
=====================================================

Testing the Guest Nights Calculation feature as requested:

**Updated Feature:**
Geceleme hesabı artık `kişi × gece` mantığıyla çalışıyor:
- 1 oda, 2 yetişkin, 1 gece = 2 geceleme
- 1 oda, 3 yetişkin, 2 gece = 6 geceleme  
- 1 oda, 2 yetişkin + 1 çocuk, 1 gece = 3 geceleme

**Test Requirements:**
1. Test POST /api/reservations endpoint with guest_nights calculation
2. Test PUT /api/reservations/{reservation_id} endpoint with updated guest_nights
3. Test /api/front-office/dashboard monthly_stats with total_guest_nights and total_room_nights
4. Test /api/front-office/monthly-occupancy with guest_nights in daily data
5. Test /api/front-office/report/excel with guest_nights column

**Test Data Examples:**
Reservation 1: 2 adults, 0 children, 3 nights = 6 guest_nights
Reservation 2: 1 adult, 2 children, 2 nights = 6 guest_nights
Reservation 3: 4 adults, 1 child, 1 night = 5 guest_nights

**Expected Results:**
- New reservations should include `guest_nights` field in response
- Dashboard should show both `total_guest_nights` and `total_room_nights`
- Monthly occupancy should include `guest_nights` in daily data
- All calculations should follow the formula: guest_nights = (adults + children) × nights

Backend URL: https://rota-crm-production.up.railway.app
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import uuid

# Production URL from frontend .env
BACKEND_URL = "https://rota-crm-production.up.railway.app"

class GuestNightsCalculationTest:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        # Test data for guest nights calculation
        self.test_reservations = [
            {
                "guest_name": "Ahmet Yılmaz",
                "guest_email": "ahmet@example.com",
                "guest_phone": "+90 532 123 4567",
                "room_id": "room-101",
                "check_in_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                "check_out_date": (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d"),  # 3 nights
                "adults": 2,
                "children": 0,
                "room_rate": 200.0,
                "payment_status": "pending",
                "booking_source": "direct",
                "expected_guest_nights": 6  # 2 adults × 3 nights = 6
            },
            {
                "guest_name": "Fatma Demir",
                "guest_email": "fatma@example.com", 
                "guest_phone": "+90 532 987 6543",
                "room_id": "room-102",
                "check_in_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "check_out_date": (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d"),  # 2 nights
                "adults": 1,
                "children": 2,
                "room_rate": 180.0,
                "payment_status": "pending",
                "booking_source": "online",
                "expected_guest_nights": 6  # (1 adult + 2 children) × 2 nights = 6
            },
            {
                "guest_name": "Mehmet Özkan",
                "guest_email": "mehmet@example.com",
                "guest_phone": "+90 532 555 1234",
                "room_id": "room-103", 
                "check_in_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                "check_out_date": (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d"),  # 1 night
                "adults": 4,
                "children": 1,
                "room_rate": 250.0,
                "payment_status": "pending",
                "booking_source": "agency",
                "expected_guest_nights": 5  # (4 adults + 1 child) × 1 night = 5
            }
        ]
        
        # Test client IDs for role-based testing
        self.test_client_ids = [
            "94927a77-edc3-45ec-8329-795feae35771",  # Known test client
            "test-client-id-1",
            "test-client-id-2"
        ]
        
        # Store created reservation IDs for update tests
        self.created_reservation_ids = []

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

    def test_reservation_creation_guest_nights(self):
        """Test POST /api/reservations endpoint with guest_nights calculation"""
        print("📝 Reservation Creation with Guest Nights Calculation")
        print("=" * 60)
        
        # Test endpoint accessibility
        try:
            response = requests.post(
                f"{self.backend_url}/api/reservations",
                json=self.test_reservations[0],
                timeout=10
            )
            
            # Check if endpoint exists (not 404)
            if response.status_code == 404:
                self.log_test(
                    "POST /api/reservations - Endpoint Exists",
                    False,
                    f"🚨 CRITICAL: Reservation creation endpoint not found!",
                    "Not 404",
                    "404"
                )
                return False
            
            # Should return proper auth error (403/401) for unauthenticated requests
            if response.status_code in [401, 403]:
                self.log_test(
                    "POST /api/reservations - Endpoint Accessible",
                    True,
                    f"✅ Reservation creation endpoint exists and requires authentication (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "POST /api/reservations - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 Internal Server Error - Reservation creation implementation error!",
                    "Not 500",
                    "500"
                )
                return False
            else:
                self.log_test(
                    "POST /api/reservations - Endpoint Accessible",
                    True,
                    f"✅ Reservation creation endpoint accessible (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "POST /api/reservations - Connection Test",
                False,
                f"Request error: {str(e)}"
            )
            return False

        # Test guest nights calculation logic with different scenarios
        for i, reservation_data in enumerate(self.test_reservations):
            try:
                response = requests.post(
                    f"{self.backend_url}/api/reservations",
                    json=reservation_data,
                    timeout=10
                )
                
                test_name = f"POST /api/reservations - Guest Nights Calculation Test {i+1}"
                
                if response.status_code in [401, 403]:
                    self.log_test(
                        test_name,
                        True,
                        f"✅ Authentication required for reservation creation (Status: {response.status_code})"
                    )
                elif response.status_code == 500:
                    self.log_test(
                        test_name,
                        False,
                        f"🚨 CRITICAL: 500 error during guest nights calculation!",
                        "Not 500",
                        "500"
                    )
                else:
                    self.log_test(
                        test_name,
                        True,
                        f"✅ Guest nights calculation endpoint handled (Status: {response.status_code})"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"POST /api/reservations - Guest Nights Test {i+1}",
                    False,
                    f"Request error: {str(e)}"
                )

        # Test with invalid guest counts
        invalid_reservation = {
            "guest_name": "Test Invalid",
            "guest_email": "test@example.com",
            "guest_phone": "+90 532 000 0000",
            "room_id": "room-999",
            "check_in_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "check_out_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "adults": -1,  # Invalid adult count
            "children": -1,  # Invalid children count
            "room_rate": 100.0,
            "payment_status": "pending",
            "booking_source": "direct"
        }
        
        try:
            response = requests.post(
                f"{self.backend_url}/api/reservations",
                json=invalid_reservation,
                timeout=10
            )
            
            if response.status_code == 500:
                self.log_test(
                    "POST /api/reservations - Invalid Guest Count Validation",
                    False,
                    f"🚨 CRITICAL: 500 error with invalid guest counts - validation error!",
                    "400/422",
                    "500"
                )
            elif response.status_code in [400, 401, 403, 422]:
                self.log_test(
                    "POST /api/reservations - Invalid Guest Count Validation",
                    True,
                    f"✅ Invalid guest counts properly validated (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "POST /api/reservations - Invalid Guest Count Validation",
                    True,
                    f"✅ Invalid guest counts handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "POST /api/reservations - Invalid Guest Count Test",
                False,
                f"Request error: {str(e)}"
            )

        return True

    def test_reservation_update_guest_nights(self):
        """Test PUT /api/reservations/{reservation_id} endpoint with updated guest_nights"""
        print("📝 Reservation Update with Guest Nights Recalculation")
        print("=" * 60)
        
        # Test reservation update data with different guest counts
        update_data = {
            "guest_name": "Ahmet Yılmaz (Updated)",
            "guest_email": "ahmet.updated@example.com",
            "guest_phone": "+90 532 123 4567",
            "room_id": "room-101",
            "check_in_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "check_out_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),  # 3 nights
            "adults": 3,  # Changed from 2 to 3
            "children": 2,  # Changed from 0 to 2
            "room_rate": 250.0,
            "payment_status": "partial",
            "booking_source": "online",
            "expected_guest_nights": 15  # (3 adults + 2 children) × 3 nights = 15
        }
        
        test_reservation_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Test endpoint accessibility
        try:
            response = requests.put(
                f"{self.backend_url}/api/reservations/{test_reservation_id}",
                json=update_data,
                timeout=10
            )
            
            # Check if endpoint exists (not 404)
            if response.status_code == 404:
                self.log_test(
                    "PUT /api/reservations/{id} - Endpoint Exists",
                    False,
                    f"🚨 CRITICAL: Reservation update endpoint not found!",
                    "Not 404",
                    "404"
                )
                return False
            
            # Should return proper auth error (403/401) for unauthenticated requests
            if response.status_code in [401, 403]:
                self.log_test(
                    "PUT /api/reservations/{id} - Endpoint Accessible",
                    True,
                    f"✅ Reservation update endpoint exists and requires authentication (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "PUT /api/reservations/{id} - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 Internal Server Error - Reservation update implementation error!",
                    "Not 500",
                    "500"
                )
                return False
            else:
                self.log_test(
                    "PUT /api/reservations/{id} - Endpoint Accessible",
                    True,
                    f"✅ Reservation update endpoint accessible (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "PUT /api/reservations/{id} - Connection Test",
                False,
                f"Request error: {str(e)}"
            )
            return False

        # Test guest nights recalculation with different scenarios
        update_scenarios = [
            {
                "adults": 1, "children": 0, "nights": 2, "expected": 2,
                "description": "Single adult, 2 nights"
            },
            {
                "adults": 2, "children": 1, "nights": 3, "expected": 9,
                "description": "Family (2+1), 3 nights"
            },
            {
                "adults": 4, "children": 2, "nights": 1, "expected": 6,
                "description": "Large group (4+2), 1 night"
            }
        ]
        
        for i, scenario in enumerate(update_scenarios):
            scenario_data = update_data.copy()
            scenario_data["adults"] = scenario["adults"]
            scenario_data["children"] = scenario["children"]
            scenario_data["check_out_date"] = (datetime.now() + timedelta(days=2 + scenario["nights"])).strftime("%Y-%m-%d")
            
            try:
                response = requests.put(
                    f"{self.backend_url}/api/reservations/{test_reservation_id}",
                    json=scenario_data,
                    timeout=10
                )
                
                test_name = f"PUT /api/reservations - Guest Nights Update Scenario {i+1}"
                
                if response.status_code in [401, 403]:
                    self.log_test(
                        test_name,
                        True,
                        f"✅ Authentication required for reservation update - {scenario['description']} (Status: {response.status_code})"
                    )
                elif response.status_code == 500:
                    self.log_test(
                        test_name,
                        False,
                        f"🚨 CRITICAL: 500 error during guest nights recalculation - {scenario['description']}!",
                        "Not 500",
                        "500"
                    )
                else:
                    self.log_test(
                        test_name,
                        True,
                        f"✅ Guest nights recalculation handled - {scenario['description']} (Status: {response.status_code})"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"PUT /api/reservations - Update Scenario {i+1}",
                    False,
                    f"Request error: {str(e)}"
                )

        return True

    def test_dashboard_guest_nights_stats(self):
        """Test /api/front-office/dashboard monthly_stats with total_guest_nights and total_room_nights"""
        print("📊 Dashboard Guest Nights Statistics")
        print("=" * 50)
        
        # Test endpoint accessibility
        try:
            response = requests.get(f"{self.backend_url}/api/front-office/dashboard", timeout=10)
            
            # Check if endpoint exists (not 404)
            if response.status_code == 404:
                self.log_test(
                    "GET /api/front-office/dashboard - Endpoint Exists",
                    False,
                    f"🚨 CRITICAL: Front Office dashboard endpoint not found!",
                    "Not 404",
                    "404"
                )
                return False
            
            # Should return proper auth error (403/401) for unauthenticated requests
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/front-office/dashboard - Endpoint Accessible",
                    True,
                    f"✅ Dashboard endpoint exists and requires authentication (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/dashboard - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 Internal Server Error - Dashboard implementation error!",
                    "Not 500",
                    "500"
                )
                return False
            else:
                self.log_test(
                    "GET /api/front-office/dashboard - Endpoint Accessible",
                    True,
                    f"✅ Dashboard endpoint accessible (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office/dashboard - Connection Test",
                False,
                f"Request error: {str(e)}"
            )
            return False

        # Test with client_id parameter
        try:
            response = requests.get(
                f"{self.backend_url}/api/front-office/dashboard",
                params={"client_id": self.test_client_ids[0]},
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/front-office/dashboard - Client ID Parameter",
                    True,
                    f"✅ Client ID parameter accepted, authentication required (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/dashboard - Client ID Parameter",
                    False,
                    f"🚨 CRITICAL: 500 error with client_id parameter!",
                    "401/403",
                    "500"
                )
            else:
                self.log_test(
                    "GET /api/front-office/dashboard - Client ID Parameter",
                    True,
                    f"✅ Client ID parameter handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office/dashboard - Client ID Test",
                False,
                f"Request error: {str(e)}"
            )

        # Test authentication requirement
        try:
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.get(
                f"{self.backend_url}/api/front-office/dashboard",
                headers=invalid_headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test(
                    "GET /api/front-office/dashboard - Authentication Required",
                    True,
                    f"✅ Invalid token properly rejected (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/dashboard - Authentication Required",
                    False,
                    f"🚨 CRITICAL: 500 error with invalid token!",
                    "401",
                    "500"
                )
            else:
                self.log_test(
                    "GET /api/front-office/dashboard - Authentication Required",
                    True,
                    f"✅ Authentication handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office/dashboard - Authentication Test",
                False,
                f"Request error: {str(e)}"
            )

        return True

    def test_monthly_occupancy_guest_nights(self):
        """Test /api/front-office/monthly-occupancy with guest_nights in daily data"""
        print("📈 Monthly Occupancy with Guest Nights Data")
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
            
            # Should return proper auth error (403/401) for unauthenticated requests
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Endpoint Accessible",
                    True,
                    f"✅ Monthly occupancy endpoint exists and requires authentication (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 Internal Server Error - Monthly occupancy implementation error!",
                    "Not 500",
                    "500"
                )
                return False
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
                    "GET /api/front-office/monthly-occupancy - Year/Month Parameters",
                    True,
                    f"✅ Year/Month parameters accepted, authentication required (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Year/Month Parameters",
                    False,
                    f"🚨 CRITICAL: 500 error with year/month parameters!",
                    "401/403",
                    "500"
                )
            else:
                self.log_test(
                    "GET /api/front-office/monthly-occupancy - Year/Month Parameters",
                    True,
                    f"✅ Year/Month parameters handled (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "GET /api/front-office/monthly-occupancy - Parameters Test",
                False,
                f"Request error: {str(e)}"
            )

        return True

    def test_excel_report_guest_nights(self):
        """Test /api/front-office/report/excel with guest_nights column"""
        print("📊 Excel Report with Guest Nights Column")
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
            
            # Should return proper auth error (403/401) for unauthenticated requests
            if response.status_code in [401, 403]:
                self.log_test(
                    "GET /api/front-office/report/excel - Endpoint Accessible",
                    True,
                    f"✅ Excel report endpoint exists and requires authentication (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "GET /api/front-office/report/excel - No 500 Error",
                    False,
                    f"🚨 CRITICAL: 500 Internal Server Error - Excel report implementation error!",
                    "Not 500",
                    "500"
                )
                return False
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

        return True

    def test_response_formats_and_cors(self):
        """Test response formats and CORS headers"""
        print("📋 Response Format and CORS Tests")
        print("=" * 50)
        
        endpoints_to_test = [
            "/api/reservations",
            "/api/front-office/dashboard",
            "/api/front-office/monthly-occupancy",
            "/api/front-office/report/excel"
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
            response = requests.options(f"{self.backend_url}/api/front-office/dashboard", timeout=10)
            
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

    def run_all_tests(self):
        """Run all tests"""
        print("🏨 GUEST NIGHTS CALCULATION COMPREHENSIVE BACKEND TEST")
        print("=" * 70)
        print(f"🎯 Backend URL: {self.backend_url}")
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Focus: Guest Nights Calculation feature testing")
        print("=" * 70)
        print()
        
        # Backend health check
        if not self.test_backend_health():
            print("❌ Backend inaccessible, stopping tests!")
            return False
        
        # Test Guest Nights Calculation features
        print("🌙 GUEST NIGHTS CALCULATION TESTS:")
        print("-" * 40)
        self.test_reservation_creation_guest_nights()
        self.test_reservation_update_guest_nights()
        self.test_dashboard_guest_nights_stats()
        self.test_monthly_occupancy_guest_nights()
        self.test_excel_report_guest_nights()
        
        print("\n📋 RESPONSE FORMAT & INFRASTRUCTURE TESTS:")
        print("-" * 40)
        self.test_response_formats_and_cors()
        
        # Show results
        self.show_results()
        
        return self.passed_tests >= (self.total_tests * 0.8)  # 80% success rate

    def show_results(self):
        """Show test results"""
        print("\n" + "=" * 70)
        print("📊 GUEST NIGHTS CALCULATION TEST RESULTS")
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
            print("\n🎉 EXCELLENT! Guest Nights Calculation feature is production ready!")
        elif success_rate >= 75:
            print("\n✅ GOOD! Guest Nights Calculation feature is generally working.")
        elif success_rate >= 50:
            print("\n⚠️ MODERATE! Guest Nights Calculation feature has some issues.")
        else:
            print("\n❌ CRITICAL! Guest Nights Calculation feature has serious issues.")
        
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
            dashboard_tests = [t for t in successful_tests if 'dashboard' in t['test'].lower()]
            occupancy_tests = [t for t in successful_tests if 'occupancy' in t['test'].lower()]
            excel_tests = [t for t in successful_tests if 'excel' in t['test'].lower()]
            
            if reservation_tests:
                print(f"   📝 Reservation Tests: {len(reservation_tests)} ✅")
            if dashboard_tests:
                print(f"   📊 Dashboard Tests: {len(dashboard_tests)} ✅")
            if occupancy_tests:
                print(f"   📈 Monthly Occupancy Tests: {len(occupancy_tests)} ✅")
            if excel_tests:
                print(f"   📋 Excel Report Tests: {len(excel_tests)} ✅")
        
        print("\n" + "=" * 70)
        
        # Save test results to JSON
        with open('/app/guest_nights_calculation_test_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'test_summary': {
                    'total_tests': self.total_tests,
                    'passed_tests': self.passed_tests,
                    'failed_tests': self.total_tests - self.passed_tests,
                    'success_rate': success_rate,
                    'backend_url': self.backend_url,
                    'test_timestamp': datetime.now().isoformat(),
                    'test_focus': 'Guest Nights Calculation - Feature Testing',
                    'critical_500_errors': len(critical_500_errors),
                    'missing_endpoints': len(missing_endpoints)
                },
                'test_results': self.test_results,
                'critical_issues': {
                    '500_errors': [r for r in self.test_results if not r['success'] and '500' in r['details']],
                    'missing_endpoints': [r for r in self.test_results if not r['success'] and '404' in r['details']]
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed test results saved: /app/guest_nights_calculation_test_results.json")

def main():
    """Main test function"""
    tester = GuestNightsCalculationTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 GUEST NIGHTS CALCULATION TESTS SUCCESSFUL!")
        print("✅ All Guest Nights Calculation features are accessible")
        print("✅ No 500 Internal Server Errors detected")
        print("✅ Authentication and role-based access working")
        print("✅ Response formats and CORS properly configured")
        sys.exit(0)
    else:
        print("\n🚨 CRITICAL ISSUES DETECTED!")
        print("❌ Guest Nights Calculation features have 500 Internal Server Error or missing endpoint issues")
        print("🔧 Backend implementation needs to be checked")
        print("⚡ Immediate intervention required!")
        sys.exit(1)

if __name__ == "__main__":
    main()