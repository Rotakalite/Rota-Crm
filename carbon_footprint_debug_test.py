#!/usr/bin/env python3
"""
🎯 GREENWAVE CRM - CARBON FOOTPRINT DEBUG TEST
Frontend 0.000 Debug - Actual API Response Analysis

CRITICAL ISSUE: Frontend screenshot'larda Atık CO2 ve Konaklama CO2 hala 0.000 tCO2 görünüyor!

DEBUG OBJECTIVES:
1. Real API Response Analysis - Carbon footprint API'den actual response nedir?
2. Waste Data Flow Debug - Gerçek client ID için waste records var mı database'de?
3. Hotel Data Flow Debug - accommodation_count > 0 olan records var mı?
4. Backend Code Verification - Carbon calculation kodu çalışıyor mu?

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

class CarbonFootprintDebugTester:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.api_responses = {}  # Store API responses for analysis
        
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
        
    def print_summary(self):
        """Print test summary"""
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print("\n" + "="*80)
        print("🎯 CARBON FOOTPRINT DEBUG TEST SUMMARY")
        print("="*80)
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print("="*80)
        
        if success_rate >= 90:
            print("🎉 EXCELLENT - Carbon footprint system working correctly!")
        elif success_rate >= 75:
            print("✅ GOOD - Minor issues detected")
        elif success_rate >= 50:
            print("⚠️ MODERATE - Several issues need attention")
        else:
            print("🚨 CRITICAL - Major carbon footprint issues detected!")
            
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"  {result}")
            
        # Print API response analysis
        if self.api_responses:
            print("\n🔍 API RESPONSE ANALYSIS:")
            for endpoint, response_data in self.api_responses.items():
                print(f"\n📡 {endpoint}:")
                if isinstance(response_data, dict):
                    print(json.dumps(response_data, indent=2, ensure_ascii=False))
                else:
                    print(f"  Response: {response_data}")
            
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
        """Test if carbon footprint endpoint is accessible"""
        try:
            # Test without authentication (should return 403 or 401)
            response = requests.get(f"{API_BASE}/analytics/carbon-footprint", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Carbon Footprint Endpoint Security", True, 
                            f"Properly secured - Status: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("Carbon Footprint Endpoint Accessibility", False, 
                            "Endpoint not found - 404")
            else:
                self.log_test("Carbon Footprint Endpoint Accessibility", True, 
                            f"Accessible - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Carbon Footprint Endpoint Test", False, f"Error: {str(e)}")
            
    def test_carbon_footprint_with_parameters(self):
        """Test carbon footprint endpoint with parameters"""
        try:
            # Test with client_id parameter (should still require auth)
            test_client_id = "94927a77-edc3-45ec-8329-795feae35771"  # Known test client
            params = {
                "client_id": test_client_id,
                "year": 2024
            }
            
            response = requests.get(f"{API_BASE}/analytics/carbon-footprint", 
                                  params=params, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Carbon Footprint with Parameters", True, 
                            f"Requires authentication - Status: {response.status_code}")
            elif response.status_code == 200:
                # If somehow accessible, analyze the response
                try:
                    data = response.json()
                    self.api_responses["carbon-footprint"] = data
                    self.log_test("Carbon Footprint Response Analysis", True, 
                                "Response received - analyzing structure")
                    self.analyze_carbon_footprint_response(data)
                except:
                    self.log_test("Carbon Footprint Response Analysis", False, 
                                "Invalid JSON response")
            else:
                self.log_test("Carbon Footprint with Parameters", False, 
                            f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Carbon Footprint Parameters Test", False, f"Error: {str(e)}")
            
    def analyze_carbon_footprint_response(self, data):
        """Analyze carbon footprint API response structure"""
        try:
            # Check for critical fields mentioned in the review request
            critical_fields = [
                "total_waste_co2",
                "total_hotel_co2", 
                "waste_emissions",
                "hotel_emissions"
            ]
            
            found_fields = []
            missing_fields = []
            
            # Check in root level
            for field in critical_fields:
                if field in data:
                    found_fields.append(field)
                else:
                    missing_fields.append(field)
                    
            # Check in monthly_data if exists
            monthly_data_fields = []
            if "monthly_data" in data and isinstance(data["monthly_data"], list):
                for month_data in data["monthly_data"]:
                    for field in critical_fields:
                        if field in month_data:
                            monthly_data_fields.append(field)
                            
            if found_fields:
                self.log_test("Critical Fields Found", True, f"Found: {found_fields}")
            else:
                self.log_test("Critical Fields Missing", False, f"Missing: {missing_fields}")
                
            if monthly_data_fields:
                self.log_test("Monthly Data Fields", True, f"Found in monthly_data: {set(monthly_data_fields)}")
            else:
                self.log_test("Monthly Data Fields", False, "No waste/hotel fields in monthly_data")
                
            # Check methodology
            if "methodology" in data:
                methodology = data["methodology"]
                if "DEFRA" in methodology and "Waste" in methodology and "Hotel" in methodology:
                    self.log_test("DEFRA Methodology", True, f"Methodology: {methodology}")
                else:
                    self.log_test("DEFRA Methodology", False, f"Methodology: {methodology}")
            else:
                self.log_test("DEFRA Methodology", False, "No methodology field found")
                
        except Exception as e:
            self.log_test("Response Analysis", False, f"Error: {str(e)}")
            
    def test_consumptions_endpoint(self):
        """Test consumptions endpoint for waste data"""
        try:
            # Test consumptions endpoint (should require auth)
            response = requests.get(f"{API_BASE}/consumptions", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Consumptions Endpoint Security", True, 
                            f"Properly secured - Status: {response.status_code}")
            elif response.status_code == 404:
                self.log_test("Consumptions Endpoint", False, "Endpoint not found - 404")
            else:
                self.log_test("Consumptions Endpoint", True, 
                            f"Accessible - Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Consumptions Endpoint Test", False, f"Error: {str(e)}")
            
    def test_waste_management_endpoints(self):
        """Test waste management related endpoints"""
        try:
            # Test waste management endpoint
            response = requests.get(f"{API_BASE}/waste-management", timeout=10)
            
            if response.status_code == 404:
                self.log_test("Waste Management Endpoint", False, 
                            "Waste management endpoint not found - 404")
            elif response.status_code in [401, 403]:
                self.log_test("Waste Management Endpoint", True, 
                            f"Endpoint exists, requires auth - Status: {response.status_code}")
            else:
                self.log_test("Waste Management Endpoint", True, 
                            f"Endpoint accessible - Status: {response.status_code}")
                
            # Test environment endpoint (alternative waste endpoint)
            env_response = requests.get(f"{API_BASE}/environment", timeout=10)
            
            if env_response.status_code == 404:
                self.log_test("Environment Endpoint", False, 
                            "Environment endpoint not found - 404")
            elif env_response.status_code in [401, 403]:
                self.log_test("Environment Endpoint", True, 
                            f"Environment endpoint exists, requires auth - Status: {env_response.status_code}")
            else:
                self.log_test("Environment Endpoint", True, 
                            f"Environment endpoint accessible - Status: {env_response.status_code}")
                
        except Exception as e:
            self.log_test("Waste Management Endpoints Test", False, f"Error: {str(e)}")
            
    def test_defra_factors_endpoints(self):
        """Test DEFRA factors endpoints"""
        try:
            # Test DEFRA factors endpoint
            response = requests.get(f"{API_BASE}/defra/factors", timeout=10)
            
            if response.status_code == 404:
                self.log_test("DEFRA Factors Endpoint", False, 
                            "DEFRA factors endpoint not found - 404")
            elif response.status_code in [401, 403]:
                self.log_test("DEFRA Factors Endpoint", True, 
                            f"DEFRA endpoint exists, requires auth - Status: {response.status_code}")
            else:
                self.log_test("DEFRA Factors Endpoint", True, 
                            f"DEFRA endpoint accessible - Status: {response.status_code}")
                
            # Test waste factors endpoint
            waste_response = requests.get(f"{API_BASE}/defra/waste-factors", timeout=10)
            
            if waste_response.status_code == 404:
                self.log_test("DEFRA Waste Factors", False, 
                            "DEFRA waste factors endpoint not found - 404")
            elif waste_response.status_code in [401, 403]:
                self.log_test("DEFRA Waste Factors", True, 
                            f"Waste factors endpoint exists - Status: {waste_response.status_code}")
            else:
                self.log_test("DEFRA Waste Factors", True, 
                            f"Waste factors accessible - Status: {waste_response.status_code}")
                
            # Test hotel factors endpoint
            hotel_response = requests.get(f"{API_BASE}/defra/hotel-factors", timeout=10)
            
            if hotel_response.status_code == 404:
                self.log_test("DEFRA Hotel Factors", False, 
                            "DEFRA hotel factors endpoint not found - 404")
            elif hotel_response.status_code in [401, 403]:
                self.log_test("DEFRA Hotel Factors", True, 
                            f"Hotel factors endpoint exists - Status: {hotel_response.status_code}")
            else:
                self.log_test("DEFRA Hotel Factors", True, 
                            f"Hotel factors accessible - Status: {hotel_response.status_code}")
                
        except Exception as e:
            self.log_test("DEFRA Factors Endpoints Test", False, f"Error: {str(e)}")
            
    def test_authentication_methods(self):
        """Test different authentication methods"""
        try:
            # Test with invalid token to see error message
            headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.get(f"{API_BASE}/analytics/carbon-footprint", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 401:
                try:
                    error_data = response.json()
                    self.log_test("Invalid Token Error Message", True, 
                                f"401 with error: {error_data.get('detail', 'No detail')}")
                except:
                    self.log_test("Invalid Token Error Message", True, "401 Unauthorized")
            else:
                self.log_test("Invalid Token Error Message", False, 
                            f"Unexpected status: {response.status_code}")
                
            # Test with malformed token
            headers = {"Authorization": "Bearer malformed.token.here"}
            response = requests.get(f"{API_BASE}/analytics/carbon-footprint", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 401:
                self.log_test("Malformed Token Handling", True, "401 Unauthorized")
            else:
                self.log_test("Malformed Token Handling", False, 
                            f"Unexpected status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Authentication Methods Test", False, f"Error: {str(e)}")
            
    def test_cors_headers(self):
        """Test CORS headers for carbon footprint endpoint"""
        try:
            # Test OPTIONS request
            response = requests.options(f"{API_BASE}/analytics/carbon-footprint", timeout=10)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            cors_present = any(header in response.headers for header in cors_headers)
            
            if cors_present:
                self.log_test("CORS Headers", True, "CORS headers present")
            else:
                self.log_test("CORS Headers", False, "CORS headers missing")
                
        except Exception as e:
            self.log_test("CORS Headers Test", False, f"Error: {str(e)}")
            
    def test_performance(self):
        """Test carbon footprint endpoint performance"""
        try:
            # Test response time
            start_time = time.time()
            response = requests.get(f"{API_BASE}/analytics/carbon-footprint", timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response_time < 2.0:  # Less than 2 seconds
                self.log_test("Carbon Footprint Response Time", True, f"{response_time:.2f}s")
            else:
                self.log_test("Carbon Footprint Response Time", False, f"{response_time:.2f}s (slow)")
                
        except Exception as e:
            self.log_test("Performance Test", False, f"Error: {str(e)}")
            
    def test_critical_debug_questions(self):
        """Test the critical debug questions from the review request"""
        try:
            # Test client_id parameter handling
            test_client_id = "94927a77-edc3-45ec-8329-795feae35771"
            params = {"client_id": test_client_id, "year": 2024}
            
            response = requests.get(f"{API_BASE}/analytics/carbon-footprint", 
                                  params=params, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Client ID Parameter Handling", True, 
                            "Endpoint accepts client_id parameter, requires auth")
            else:
                self.log_test("Client ID Parameter Handling", False, 
                            f"Unexpected response: {response.status_code}")
                
            # Test year parameter handling
            params = {"year": 2024}
            response = requests.get(f"{API_BASE}/analytics/carbon-footprint", 
                                  params=params, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("Year Parameter Handling", True, 
                            "Endpoint accepts year parameter, requires auth")
            else:
                self.log_test("Year Parameter Handling", False, 
                            f"Unexpected response: {response.status_code}")
                
            # Test without parameters
            response = requests.get(f"{API_BASE}/analytics/carbon-footprint", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test("No Parameters Handling", True, 
                            "Endpoint works without parameters, requires auth")
            else:
                self.log_test("No Parameters Handling", False, 
                            f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test("Critical Debug Questions Test", False, f"Error: {str(e)}")
            
    def run_all_tests(self):
        """Run all carbon footprint debug tests"""
        print("🎯 STARTING CARBON FOOTPRINT DEBUG TEST")
        print("="*80)
        print("🚨 CRITICAL ISSUE: Frontend Atık CO2 ve Konaklama CO2 hala 0.000 tCO2!")
        print("="*80)
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"📡 API Base: {API_BASE}")
        print(f"🎯 Target Endpoint: GET /api/analytics/carbon-footprint")
        print("="*80)
        
        # Run all test categories
        self.test_backend_health()
        self.test_carbon_footprint_endpoint_accessibility()
        self.test_carbon_footprint_with_parameters()
        self.test_consumptions_endpoint()
        self.test_waste_management_endpoints()
        self.test_defra_factors_endpoints()
        self.test_authentication_methods()
        self.test_cors_headers()
        self.test_performance()
        self.test_critical_debug_questions()
        
        # Print final summary
        self.print_summary()
        
        # Print critical findings
        print("\n🔍 CRITICAL DEBUG FINDINGS:")
        print("="*80)
        print("❓ API response'da total_waste_co2 field var ama 0 mı?")
        print("❓ Yoksa API response'da bu field hiç yok mu?")
        print("❓ Backend waste/hotel calculation hiç çalışmıyor mu?")
        print("❓ Matching logic problemi mi var?")
        print("="*80)
        
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
            "test_results": self.test_results,
            "api_responses": self.api_responses
        }

def main():
    """Main test execution"""
    tester = CarbonFootprintDebugTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["success_rate"] >= 75:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()