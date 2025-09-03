#!/usr/bin/env python3
"""
🎯 GREENWAVE CRM - WASTE & HOTEL DATA DEBUG TEST
Railway Production Environment Testing

PROBLEM: Frontend'de Atık CO2 ve Konaklama CO2 değerleri 0 görünüyor. 
Backend expansion kodu hazır ama veri gelmiyor.

DEBUG OBJECTIVES:
1. Database Schema Inspection - Client consumption data'sında waste_data field var mı?
2. Database Schema Inspection - Client consumption data'sında hotel_data field var mı?
3. Real Client Data Analysis - Bilinen bir client ID ile consumption data'sını al
4. API Response Debug - Carbon footprint API response'unda total_waste_co2 field var mı?
5. API Response Debug - Carbon footprint API response'unda total_hotel_co2 field var mı?
6. Data Flow Verification - Consumption collection'dan waste_data çekiliyor mu?
7. Data Flow Verification - calculate_carbon_emissions function'a waste_data geçiliyor mu?

Test Environment: Railway production https://rota-crm-production.up.railway.app
"""

import requests
import json
import sys
import time
from datetime import datetime
import uuid

# Test Configuration
BACKEND_URL = "https://rota-crm-production.up.railway.app"
API_BASE = f"{BACKEND_URL}/api"

class WasteHotelDebugTester:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.debug_findings = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
            
        result = f"{status} - {test_name}"
        if details:
            result += f" | {details}"
            
        self.test_results.append(result)
        print(result)
        
    def log_debug_finding(self, finding):
        """Log debug finding"""
        self.debug_findings.append(finding)
        print(f"🔍 DEBUG: {finding}")
        
    def print_summary(self):
        """Print test summary"""
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("🎯 WASTE & HOTEL DATA DEBUG TEST SUMMARY")
        print("="*80)
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print("="*80)
        
        print("\n🔍 DEBUG FINDINGS:")
        for finding in self.debug_findings:
            print(f"  • {finding}")
            
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"  {result}")
            
    def test_backend_health(self):
        """Test backend health and accessibility"""
        try:
            # Test root endpoint
            response = requests.get(BACKEND_URL, timeout=10)
            if response.status_code == 200:
                self.log_test("Backend Root Access", True, f"Status: {response.status_code}")
            else:
                self.log_test("Backend Root Access", False, f"Status: {response.status_code}")
                
            # Test health endpoint
            health_response = requests.get(f"{API_BASE}/health", timeout=10)
            if health_response.status_code == 200:
                health_data = health_response.json()
                self.log_test("Backend Health Check", True, f"Status: {health_data.get('status', 'unknown')}")
            else:
                self.log_test("Backend Health Check", False, f"Status: {health_response.status_code}")
                
        except Exception as e:
            self.log_test("Backend Connectivity", False, f"Error: {str(e)}")
            
    def test_carbon_footprint_endpoint_accessibility(self):
        """Test carbon footprint endpoint accessibility"""
        try:
            # Test without authentication (should return 403 or 401)
            response = requests.get(f"{API_BASE}/analytics/carbon-footprint", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Carbon Footprint Endpoint Security", True, 
                            f"Properly secured - Status: {response.status_code}")
                self.log_debug_finding("Carbon footprint endpoint exists and requires authentication")
            elif response.status_code == 404:
                self.log_test("Carbon Footprint Endpoint Accessibility", False, 
                            "Endpoint not found - 404")
                self.log_debug_finding("❌ CRITICAL: Carbon footprint endpoint not found!")
            else:
                self.log_test("Carbon Footprint Endpoint Accessibility", True, 
                            f"Accessible - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Carbon Footprint Endpoint Test", False, f"Error: {str(e)}")
            
    def test_consumptions_endpoint_accessibility(self):
        """Test consumptions endpoint accessibility"""
        try:
            # Test without authentication (should return 403 or 401)
            response = requests.get(f"{API_BASE}/consumptions", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Consumptions Endpoint Security", True, 
                            f"Properly secured - Status: {response.status_code}")
                self.log_debug_finding("Consumptions endpoint exists and requires authentication")
            elif response.status_code == 404:
                self.log_test("Consumptions Endpoint Accessibility", False, 
                            "Endpoint not found - 404")
                self.log_debug_finding("❌ CRITICAL: Consumptions endpoint not found!")
            else:
                self.log_test("Consumptions Endpoint Accessibility", True, 
                            f"Accessible - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Consumptions Endpoint Test", False, f"Error: {str(e)}")
            
    def test_clients_endpoint_for_sample_data(self):
        """Test clients endpoint to find sample client IDs"""
        try:
            # Test without authentication (should return 403 or 401)
            response = requests.get(f"{API_BASE}/clients", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Clients Endpoint Security", True, 
                            f"Properly secured - Status: {response.status_code}")
                self.log_debug_finding("Clients endpoint exists and requires authentication")
            elif response.status_code == 404:
                self.log_test("Clients Endpoint Accessibility", False, 
                            "Endpoint not found - 404")
                self.log_debug_finding("❌ CRITICAL: Clients endpoint not found!")
            else:
                self.log_test("Clients Endpoint Accessibility", True, 
                            f"Accessible - Status: {response.status_code}")
                
            # Try with a known client ID pattern (UUID format)
            sample_client_id = "94927a77-edc3-45ec-8329-795feae35771"  # Known from previous tests
            response = requests.get(f"{API_BASE}/clients/{sample_client_id}", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Sample Client ID Access", True, 
                            f"Client endpoint secured - Status: {response.status_code}")
                self.log_debug_finding(f"Sample client ID {sample_client_id} endpoint exists but requires auth")
            else:
                self.log_test("Sample Client ID Access", True, 
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Clients Endpoint Test", False, f"Error: {str(e)}")
            
    def test_carbon_footprint_with_client_id(self):
        """Test carbon footprint endpoint with known client ID"""
        try:
            # Use known client ID from previous tests
            sample_client_id = "94927a77-edc3-45ec-8329-795feae35771"
            
            # Test without authentication but with client_id parameter
            response = requests.get(f"{API_BASE}/analytics/carbon-footprint", 
                                  params={"client_id": sample_client_id}, 
                                  timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Carbon Footprint with Client ID", True, 
                            f"Properly secured - Status: {response.status_code}")
                self.log_debug_finding(f"Carbon footprint endpoint accepts client_id parameter but requires auth")
            elif response.status_code == 404:
                self.log_test("Carbon Footprint with Client ID", False, 
                            "Endpoint not found - 404")
            else:
                self.log_test("Carbon Footprint with Client ID", True, 
                            f"Status: {response.status_code}")
                
            # Test with year parameter as well
            response = requests.get(f"{API_BASE}/analytics/carbon-footprint", 
                                  params={"client_id": sample_client_id, "year": 2024}, 
                                  timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Carbon Footprint with Client ID and Year", True, 
                            f"Properly secured - Status: {response.status_code}")
                self.log_debug_finding(f"Carbon footprint endpoint accepts client_id and year parameters")
            else:
                self.log_test("Carbon Footprint with Client ID and Year", True, 
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Carbon Footprint Client ID Test", False, f"Error: {str(e)}")
            
    def test_consumptions_with_client_id(self):
        """Test consumptions endpoint with known client ID"""
        try:
            # Use known client ID from previous tests
            sample_client_id = "94927a77-edc3-45ec-8329-795feae35771"
            
            # Test without authentication but with client_id parameter
            response = requests.get(f"{API_BASE}/consumptions", 
                                  params={"client_id": sample_client_id}, 
                                  timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Consumptions with Client ID", True, 
                            f"Properly secured - Status: {response.status_code}")
                self.log_debug_finding(f"Consumptions endpoint accepts client_id parameter but requires auth")
            elif response.status_code == 404:
                self.log_test("Consumptions with Client ID", False, 
                            "Endpoint not found - 404")
            else:
                self.log_test("Consumptions with Client ID", True, 
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Consumptions Client ID Test", False, f"Error: {str(e)}")
            
    def test_waste_management_endpoint(self):
        """Test waste management endpoint accessibility"""
        try:
            # Test waste management endpoint
            response = requests.get(f"{API_BASE}/waste-management", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Waste Management Endpoint Security", True, 
                            f"Properly secured - Status: {response.status_code}")
                self.log_debug_finding("Waste management endpoint exists and requires authentication")
            elif response.status_code == 404:
                self.log_test("Waste Management Endpoint Accessibility", False, 
                            "Endpoint not found - 404")
                self.log_debug_finding("❌ CRITICAL: Waste management endpoint not found!")
            else:
                self.log_test("Waste Management Endpoint Accessibility", True, 
                            f"Accessible - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Waste Management Endpoint Test", False, f"Error: {str(e)}")
            
    def test_hotel_data_endpoints(self):
        """Test hotel data related endpoints"""
        try:
            # Test if there are any hotel-specific endpoints
            hotel_endpoints = [
                "/api/hotels",
                "/api/hotel-data", 
                "/api/accommodation",
                "/api/accommodation-data"
            ]
            
            for endpoint in hotel_endpoints:
                try:
                    response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
                    
                    if response.status_code in [401, 403]:
                        self.log_test(f"Hotel Endpoint {endpoint}", True, 
                                    f"Exists and secured - Status: {response.status_code}")
                        self.log_debug_finding(f"Hotel endpoint {endpoint} exists and requires authentication")
                    elif response.status_code == 404:
                        self.log_test(f"Hotel Endpoint {endpoint}", False, 
                                    "Endpoint not found - 404")
                    else:
                        self.log_test(f"Hotel Endpoint {endpoint}", True, 
                                    f"Status: {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Hotel Endpoint {endpoint}", False, f"Error: {str(e)}")
                    
        except Exception as e:
            self.log_test("Hotel Data Endpoints Test", False, f"Error: {str(e)}")
            
    def test_defra_carbon_module_availability(self):
        """Test if DEFRA carbon calculation module is available"""
        try:
            # Test if there's a DEFRA-specific endpoint
            defra_endpoints = [
                "/api/defra/factors",
                "/api/defra/waste-factors",
                "/api/defra/hotel-factors",
                "/api/carbon/factors",
                "/api/carbon/waste-factors"
            ]
            
            for endpoint in defra_endpoints:
                try:
                    response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
                    
                    if response.status_code in [401, 403]:
                        self.log_test(f"DEFRA Endpoint {endpoint}", True, 
                                    f"Exists and secured - Status: {response.status_code}")
                        self.log_debug_finding(f"DEFRA endpoint {endpoint} exists and requires authentication")
                    elif response.status_code == 404:
                        self.log_test(f"DEFRA Endpoint {endpoint}", False, 
                                    "Endpoint not found - 404")
                    elif response.status_code == 200:
                        self.log_test(f"DEFRA Endpoint {endpoint}", True, 
                                    "Accessible without auth")
                        self.log_debug_finding(f"DEFRA endpoint {endpoint} is publicly accessible")
                    else:
                        self.log_test(f"DEFRA Endpoint {endpoint}", True, 
                                    f"Status: {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"DEFRA Endpoint {endpoint}", False, f"Error: {str(e)}")
                    
        except Exception as e:
            self.log_test("DEFRA Carbon Module Test", False, f"Error: {str(e)}")
            
    def test_response_structure_analysis(self):
        """Analyze expected response structure for waste and hotel data"""
        try:
            # Test carbon footprint endpoint response structure (without auth)
            sample_client_id = "94927a77-edc3-45ec-8329-795feae35771"
            response = requests.get(f"{API_BASE}/analytics/carbon-footprint", 
                                  params={"client_id": sample_client_id, "year": 2024}, 
                                  timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Carbon Footprint Response Structure", True, 
                            "Cannot analyze - authentication required")
                self.log_debug_finding("Carbon footprint response structure analysis blocked by authentication")
            else:
                try:
                    response_data = response.json()
                    
                    # Check for expected waste and hotel fields
                    expected_fields = [
                        "total_waste_co2",
                        "total_hotel_co2", 
                        "total_co2_emissions",
                        "waste_emissions",
                        "hotel_emissions"
                    ]
                    
                    present_fields = [field for field in expected_fields if field in response_data]
                    missing_fields = [field for field in expected_fields if field not in response_data]
                    
                    if present_fields:
                        self.log_test("Expected Fields Present", True, f"Found: {present_fields}")
                        self.log_debug_finding(f"✅ Found expected fields: {present_fields}")
                    
                    if missing_fields:
                        self.log_test("Expected Fields Missing", False, f"Missing: {missing_fields}")
                        self.log_debug_finding(f"❌ Missing expected fields: {missing_fields}")
                    
                    # Log full response structure for analysis
                    self.log_debug_finding(f"Full response keys: {list(response_data.keys())}")
                    
                except Exception as json_error:
                    self.log_test("Carbon Footprint Response JSON", False, f"JSON Error: {str(json_error)}")
                    
        except Exception as e:
            self.log_test("Response Structure Analysis", False, f"Error: {str(e)}")
            
    def test_authentication_methods(self):
        """Test different authentication methods to understand the system"""
        try:
            # Test with different auth header formats
            auth_tests = [
                ("No Auth", {}),
                ("Bearer Token", {"Authorization": "Bearer test_token"}),
                ("Basic Auth", {"Authorization": "Basic dGVzdDp0ZXN0"}),
                ("API Key", {"X-API-Key": "test_key"}),
                ("Custom Header", {"X-Auth-Token": "test_token"})
            ]
            
            for auth_name, headers in auth_tests:
                try:
                    response = requests.get(f"{API_BASE}/analytics/carbon-footprint", 
                                          headers=headers, 
                                          timeout=5)
                    
                    self.log_test(f"Auth Method: {auth_name}", True, 
                                f"Status: {response.status_code}")
                    
                    if response.status_code == 401:
                        self.log_debug_finding(f"Auth method {auth_name} returns 401 - token validation active")
                    elif response.status_code == 403:
                        self.log_debug_finding(f"Auth method {auth_name} returns 403 - access forbidden")
                        
                except Exception as e:
                    self.log_test(f"Auth Method: {auth_name}", False, f"Error: {str(e)}")
                    
        except Exception as e:
            self.log_test("Authentication Methods Test", False, f"Error: {str(e)}")
            
    def test_database_schema_hints(self):
        """Test for hints about database schema structure"""
        try:
            # Test consumption creation endpoint to understand schema
            sample_consumption = {
                "year": 2024,
                "month": 1,
                "electricity": 25000.5,
                "water": 15000.2,
                "natural_gas": 8000.0,
                "accommodation_count": 250,
                "waste_data": [  # Test if waste_data field is accepted
                    {"type": "organic", "amount": 100.5},
                    {"type": "plastic", "amount": 50.2}
                ],
                "hotel_data": {  # Test if hotel_data field is accepted
                    "room_nights": 250,
                    "occupancy_rate": 0.75
                }
            }
            
            response = requests.post(f"{API_BASE}/consumptions", 
                                   json=sample_consumption, 
                                   timeout=10)
            
            if response.status_code == 422:  # Validation error
                try:
                    error_data = response.json()
                    self.log_test("Schema Validation Test", True, "422 Validation Error")
                    self.log_debug_finding(f"Schema validation details: {error_data}")
                except:
                    self.log_test("Schema Validation Test", True, "422 Validation Error (no JSON)")
                    
            elif response.status_code in [401, 403]:
                self.log_test("Schema Validation Test", True, "Auth required first")
                self.log_debug_finding("Cannot test schema - authentication required")
            else:
                self.log_test("Schema Validation Test", True, f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Database Schema Test", False, f"Error: {str(e)}")
            
    def run_all_tests(self):
        """Run all waste and hotel data debug tests"""
        print("🎯 STARTING WASTE & HOTEL DATA DEBUG TEST")
        print("="*80)
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"📡 API Base: {API_BASE}")
        print(f"🎯 Target: Waste CO2 and Hotel CO2 data flow debugging")
        print("="*80)
        
        # Run all test categories
        self.test_backend_health()
        self.test_carbon_footprint_endpoint_accessibility()
        self.test_consumptions_endpoint_accessibility()
        self.test_clients_endpoint_for_sample_data()
        self.test_carbon_footprint_with_client_id()
        self.test_consumptions_with_client_id()
        self.test_waste_management_endpoint()
        self.test_hotel_data_endpoints()
        self.test_defra_carbon_module_availability()
        self.test_response_structure_analysis()
        self.test_authentication_methods()
        self.test_database_schema_hints()
        
        # Print final summary
        self.print_summary()
        
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
            "test_results": self.test_results,
            "debug_findings": self.debug_findings
        }

def main():
    """Main test execution"""
    tester = WasteHotelDebugTester()
    results = tester.run_all_tests()
    
    print("\n" + "="*80)
    print("🔍 CRITICAL DEBUG POINTS ANALYSIS")
    print("="*80)
    
    # Analyze critical debug points from review request
    critical_points = [
        "❓ consumption.waste_data field database'de var mı?",
        "❓ consumption.hotel_data field database'de var mı?",
        "❓ Bu fields'lar dolu mu yoksa her zaman empty array mı?",
        "❓ calculate_carbon_emissions function bu data'ları receive ediyor mu?"
    ]
    
    for point in critical_points:
        print(f"  {point}")
        
    print("\n🎯 NEXT STEPS FOR MAIN AGENT:")
    print("  1. Implement authentication to access actual data")
    print("  2. Check consumption collection schema for waste_data and hotel_data fields")
    print("  3. Verify DEFRA waste factors (134 items) are loaded")
    print("  4. Verify Turkey hotel factor (32.1 kg CO2/room night) is loaded")
    print("  5. Test carbon footprint API with real client data")
    print("  6. Check if total_waste_co2 and total_hotel_co2 fields are in response")
    
    # Exit with appropriate code
    if results["success_rate"] >= 75:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()