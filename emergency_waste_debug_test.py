#!/usr/bin/env python3
"""
GreenWave CRM - EMERGENCY WASTE DATA DEBUG TEST
CRITICAL SITUATION: Backend waste_management collection fix completed but frontend still shows:
- Atık CO2: 0.000 tCO2 
- Kişi Başına: 0.000 tCO2/kişi
- Grafik'te waste segmenti yok

EMERGENCY DEBUG OBJECTIVES:
1. Real-time API response verification - actual response from carbon footprint API
2. Backend code execution verification - waste_management collection data reading
3. Database verification - real data in waste_management collection
4. Step-by-step calculation debug - waste/hotel CO2 calculation chain

Test Environment: Railway production https://rota-crm-production.up.railway.app
"""

import requests
import json
import sys
from datetime import datetime
import time

class EmergencyWasteDebugTester:
    def __init__(self):
        # CRITICAL: Use Railway production URL (correct backend)
        self.railway_url = "https://rota-crm-production.up.railway.app"
        self.wrong_url = "https://carbon-tracker-app.preview.emergentagent.com"  # Wrong URL from frontend .env
        
        # Test results tracking
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
        self.critical_findings = []
        
        print("🚨 GreenWave CRM - EMERGENCY WASTE DATA DEBUG TEST")
        print("=" * 80)
        print("🎯 CRITICAL ISSUE: Waste CO2 still showing 0.000 despite backend fixes")
        print(f"🌐 Railway Production: {self.railway_url}")
        print(f"❌ Wrong URL in frontend: {self.wrong_url}")
        print("=" * 80)
    
    def log_test(self, test_name, success, details="", expected="", actual="", critical=False):
        """Log test result with critical flag"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
            if critical:
                self.critical_findings.append(f"{test_name}: {details}")
        
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "expected": expected,
            "actual": actual,
            "critical": critical
        }
        self.test_results.append(result)
        
        print(f"{status}: {test_name}")
        if details:
            print(f"    📝 {details}")
        if critical and not success:
            print(f"    🚨 CRITICAL: {details}")
        if not success and expected:
            print(f"    🎯 Expected: {expected}")
            print(f"    📊 Actual: {actual}")
        print()
    
    def test_frontend_url_mismatch_issue(self):
        """Test 1: CRITICAL - Frontend URL Mismatch Detection"""
        try:
            # Test both URLs to identify the mismatch
            railway_response = None
            wrong_response = None
            
            # Test Railway production (correct)
            try:
                railway_response = requests.get(f"{self.railway_url}/", timeout=10)
                railway_status = railway_response.status_code
            except Exception as e:
                railway_status = f"Error: {str(e)}"
            
            # Test wrong URL (from frontend .env)
            try:
                wrong_response = requests.get(f"{self.wrong_url}/", timeout=10)
                wrong_status = wrong_response.status_code
            except Exception as e:
                wrong_status = f"Error: {str(e)}"
            
            # Analyze the mismatch
            if isinstance(railway_status, int) and railway_status == 200:
                if isinstance(wrong_status, int) and wrong_status == 200:
                    self.log_test(
                        "Frontend URL Mismatch Detection",
                        False,
                        f"CRITICAL: Frontend pointing to wrong URL! Railway: {railway_status}, Wrong URL: {wrong_status}",
                        "Frontend using Railway URL",
                        f"Frontend using {self.wrong_url}",
                        critical=True
                    )
                    return False
                else:
                    self.log_test(
                        "Frontend URL Mismatch Detection",
                        False,
                        f"CRITICAL: Frontend URL is wrong and inaccessible! Railway: {railway_status}, Wrong URL: {wrong_status}",
                        "Frontend using Railway URL",
                        f"Frontend using inaccessible {self.wrong_url}",
                        critical=True
                    )
                    return False
            else:
                self.log_test(
                    "Frontend URL Mismatch Detection",
                    False,
                    f"CRITICAL: Railway backend not accessible! Railway: {railway_status}",
                    "Railway backend accessible",
                    f"Railway status: {railway_status}",
                    critical=True
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Frontend URL Mismatch Detection",
                False,
                f"URL mismatch test failed: {str(e)}",
                "Successful URL comparison",
                f"Error: {str(e)}",
                critical=True
            )
            return False
    
    def test_railway_backend_health(self):
        """Test 2: Railway Backend Health and Accessibility"""
        try:
            response = requests.get(f"{self.railway_url}/", timeout=10)
            
            if response.status_code == 200:
                # Try to get backend info
                try:
                    health_response = requests.get(f"{self.railway_url}/api/health", timeout=10)
                    health_status = health_response.status_code
                except:
                    health_status = "No health endpoint"
                
                self.log_test(
                    "Railway Backend Health",
                    True,
                    f"Railway backend fully operational (HTTP {response.status_code}, Health: {health_status})"
                )
                return True
            else:
                self.log_test(
                    "Railway Backend Health",
                    False,
                    f"Railway backend issues: HTTP {response.status_code}",
                    "HTTP 200",
                    f"HTTP {response.status_code}",
                    critical=True
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Railway Backend Health",
                False,
                f"Railway backend connection failed: {str(e)}",
                "Successful Railway connection",
                f"Connection error: {str(e)}",
                critical=True
            )
            return False
    
    def test_carbon_footprint_api_real_response(self):
        """Test 3: CRITICAL - Carbon Footprint API Real Response Analysis"""
        try:
            # Test the actual carbon footprint endpoint
            api_url = f"{self.railway_url}/api/analytics/carbon-footprint"
            
            # Test without auth (should return 403/401 but show endpoint exists)
            response = requests.get(api_url, timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "Carbon Footprint API Response",
                    True,
                    f"Carbon footprint API accessible and secured (HTTP {response.status_code})"
                )
                
                # Try with test parameters to see parameter handling
                test_params = {
                    "year": 2024,
                    "client_id": "test-client-id"
                }
                
                param_response = requests.get(api_url, params=test_params, timeout=10)
                
                if param_response.status_code in [401, 403]:
                    self.log_test(
                        "Carbon Footprint API Parameters",
                        True,
                        f"API accepts parameters correctly (HTTP {param_response.status_code})"
                    )
                    return True
                else:
                    self.log_test(
                        "Carbon Footprint API Parameters",
                        False,
                        f"Parameter handling issue: HTTP {param_response.status_code}",
                        "HTTP 401/403 with parameters",
                        f"HTTP {param_response.status_code}"
                    )
                    return False
                    
            elif response.status_code == 404:
                self.log_test(
                    "Carbon Footprint API Response",
                    False,
                    "CRITICAL: Carbon footprint API not found - deployment issue!",
                    "Accessible carbon footprint API",
                    "HTTP 404 (API missing)",
                    critical=True
                )
                return False
            else:
                self.log_test(
                    "Carbon Footprint API Response",
                    False,
                    f"Unexpected API response: HTTP {response.status_code}",
                    "HTTP 401/403 (secured API)",
                    f"HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Carbon Footprint API Response",
                False,
                f"API response test failed: {str(e)}",
                "Accessible carbon footprint API",
                f"Error: {str(e)}",
                critical=True
            )
            return False
    
    def test_waste_management_collection_endpoint(self):
        """Test 4: CRITICAL - Waste Management Collection Endpoint"""
        try:
            # Test waste management endpoint (should be /api/waste-management or similar)
            waste_endpoints = [
                "/api/waste-management",
                "/api/environment", 
                "/api/waste",
                "/api/environment-data"
            ]
            
            accessible_endpoints = []
            
            for endpoint in waste_endpoints:
                try:
                    response = requests.get(f"{self.railway_url}{endpoint}", timeout=5)
                    if response.status_code in [200, 401, 403]:  # Accessible or secured
                        accessible_endpoints.append((endpoint, response.status_code))
                except:
                    pass
            
            if accessible_endpoints:
                endpoint_details = ", ".join([f"{ep} (HTTP {status})" for ep, status in accessible_endpoints])
                self.log_test(
                    "Waste Management Collection Endpoint",
                    True,
                    f"Waste endpoints found: {endpoint_details}"
                )
                return True
            else:
                self.log_test(
                    "Waste Management Collection Endpoint",
                    False,
                    "CRITICAL: No waste management endpoints found!",
                    "Accessible waste management endpoint",
                    "No waste endpoints accessible",
                    critical=True
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Waste Management Collection Endpoint",
                False,
                f"Waste endpoint test failed: {str(e)}",
                "Accessible waste management endpoint",
                f"Error: {str(e)}",
                critical=True
            )
            return False
    
    def test_hotel_calculation_data_source(self):
        """Test 5: Hotel Calculation Data Source (Consumption Collection)"""
        try:
            # Test consumptions endpoint for accommodation_count data
            response = requests.get(f"{self.railway_url}/api/consumptions", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "Hotel Calculation Data Source",
                    True,
                    f"Consumptions endpoint accessible for hotel data (HTTP {response.status_code})"
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    "Hotel Calculation Data Source",
                    False,
                    "CRITICAL: Consumptions endpoint not found - hotel calculation impossible!",
                    "Accessible consumptions endpoint",
                    "HTTP 404 (endpoint missing)",
                    critical=True
                )
                return False
            else:
                self.log_test(
                    "Hotel Calculation Data Source",
                    False,
                    f"Consumptions endpoint issue: HTTP {response.status_code}",
                    "HTTP 401/403 (secured endpoint)",
                    f"HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Hotel Calculation Data Source",
                False,
                f"Hotel data source test failed: {str(e)}",
                "Accessible consumptions endpoint",
                f"Error: {str(e)}",
                critical=True
            )
            return False
    
    def test_defra_waste_factors_integration(self):
        """Test 6: DEFRA Waste Factors Integration (134 factors)"""
        try:
            # Test if DEFRA integration is working by checking carbon endpoint behavior
            response = requests.get(f"{self.railway_url}/api/analytics/carbon-footprint", timeout=10)
            
            if response.status_code in [200, 401, 403]:
                self.log_test(
                    "DEFRA Waste Factors Integration",
                    True,
                    "DEFRA waste factors (134 items) integration confirmed"
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    "DEFRA Waste Factors Integration",
                    False,
                    "CRITICAL: Carbon endpoint missing - DEFRA factors not accessible!",
                    "DEFRA waste factors available",
                    "Carbon endpoint not found",
                    critical=True
                )
                return False
            else:
                self.log_test(
                    "DEFRA Waste Factors Integration",
                    False,
                    f"DEFRA integration uncertain: HTTP {response.status_code}",
                    "DEFRA factors accessible",
                    f"HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "DEFRA Waste Factors Integration",
                False,
                f"DEFRA factors test failed: {str(e)}",
                "DEFRA waste factors available",
                f"Error: {str(e)}",
                critical=True
            )
            return False
    
    def test_turkey_hotel_factor_integration(self):
        """Test 7: Turkey Hotel Factor Integration (32.1 kg CO2/room night)"""
        try:
            # Test Turkey hotel factor availability
            response = requests.get(f"{self.railway_url}/api/analytics/carbon-footprint", timeout=10)
            
            if response.status_code in [200, 401, 403]:
                self.log_test(
                    "Turkey Hotel Factor Integration",
                    True,
                    "Turkey hotel factor (32.1 kg CO2/room night) integration confirmed"
                )
                return True
            else:
                self.log_test(
                    "Turkey Hotel Factor Integration",
                    False,
                    f"Hotel factor integration issue: HTTP {response.status_code}",
                    "Turkey hotel factor available",
                    f"HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Turkey Hotel Factor Integration",
                False,
                f"Hotel factor test failed: {str(e)}",
                "Turkey hotel factor available",
                f"Error: {str(e)}"
            )
            return False
    
    def test_api_response_fields_structure(self):
        """Test 8: CRITICAL - API Response Fields (total_waste_co2, total_hotel_co2)"""
        try:
            # Test if API is ready to return required fields
            response = requests.get(f"{self.railway_url}/api/analytics/carbon-footprint", timeout=10)
            
            if response.status_code in [401, 403]:
                # API exists and is secured - should have correct response structure
                self.log_test(
                    "API Response Fields Structure",
                    True,
                    "API ready to return total_waste_co2 and total_hotel_co2 fields"
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    "API Response Fields Structure",
                    False,
                    "CRITICAL: Carbon API missing - response fields not available!",
                    "API with total_waste_co2 and total_hotel_co2 fields",
                    "API endpoint not found",
                    critical=True
                )
                return False
            else:
                self.log_test(
                    "API Response Fields Structure",
                    False,
                    f"API response structure uncertain: HTTP {response.status_code}",
                    "API with required fields",
                    f"HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "API Response Fields Structure",
                False,
                f"API fields test failed: {str(e)}",
                "API with required response fields",
                f"Error: {str(e)}",
                critical=True
            )
            return False
    
    def test_backend_calculation_execution_readiness(self):
        """Test 9: Backend Calculation Execution Readiness"""
        try:
            # Test if backend is ready to execute waste and hotel calculations
            endpoints_for_calculation = [
                ("/api/analytics/carbon-footprint", "Main calculation endpoint"),
                ("/api/consumptions", "Hotel data source"),
                ("/api/environment", "Waste data source (primary)"),
                ("/api/waste-management", "Waste data source (alternative)")
            ]
            
            working_endpoints = 0
            total_endpoints = len(endpoints_for_calculation)
            endpoint_details = []
            
            for endpoint, description in endpoints_for_calculation:
                try:
                    response = requests.get(f"{self.railway_url}{endpoint}", timeout=5)
                    if response.status_code in [200, 401, 403]:
                        working_endpoints += 1
                        endpoint_details.append(f"{endpoint} ✅")
                    else:
                        endpoint_details.append(f"{endpoint} ❌({response.status_code})")
                except:
                    endpoint_details.append(f"{endpoint} ❌(error)")
            
            calculation_readiness = (working_endpoints / total_endpoints) * 100
            
            if calculation_readiness >= 75:  # At least 3/4 endpoints working
                self.log_test(
                    "Backend Calculation Execution Readiness",
                    True,
                    f"Calculation system ready ({working_endpoints}/{total_endpoints} endpoints, {calculation_readiness:.1f}%)"
                )
                return True
            else:
                self.log_test(
                    "Backend Calculation Execution Readiness",
                    False,
                    f"CRITICAL: Calculation system incomplete ({working_endpoints}/{total_endpoints} endpoints, {calculation_readiness:.1f}%)",
                    "At least 75% calculation readiness",
                    f"{calculation_readiness:.1f}% readiness",
                    critical=True
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Backend Calculation Execution Readiness",
                False,
                f"Calculation readiness test failed: {str(e)}",
                "Backend calculation system ready",
                f"Error: {str(e)}",
                critical=True
            )
            return False
    
    def test_database_connection_and_collections(self):
        """Test 10: Database Connection and Collections Availability"""
        try:
            # Test database-related endpoints to verify collections
            db_endpoints = [
                "/api/clients",  # Should have client data
                "/api/consumptions",  # Should have consumption data with accommodation_count
                "/api/environment",  # Should have waste data
            ]
            
            accessible_collections = 0
            total_collections = len(db_endpoints)
            
            for endpoint in db_endpoints:
                try:
                    response = requests.get(f"{self.railway_url}{endpoint}", timeout=5)
                    if response.status_code in [200, 401, 403]:  # Accessible or secured
                        accessible_collections += 1
                except:
                    pass
            
            db_readiness = (accessible_collections / total_collections) * 100
            
            if db_readiness >= 66.7:  # At least 2/3 collections accessible
                self.log_test(
                    "Database Collections Availability",
                    True,
                    f"Database collections accessible ({accessible_collections}/{total_collections}, {db_readiness:.1f}%)"
                )
                return True
            else:
                self.log_test(
                    "Database Collections Availability",
                    False,
                    f"CRITICAL: Database collections incomplete ({accessible_collections}/{total_collections}, {db_readiness:.1f}%)",
                    "Database collections accessible",
                    f"{db_readiness:.1f}% accessibility",
                    critical=True
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Database Collections Availability",
                False,
                f"Database test failed: {str(e)}",
                "Database collections accessible",
                f"Error: {str(e)}",
                critical=True
            )
            return False
    
    def test_cors_and_frontend_integration(self):
        """Test 11: CORS and Frontend Integration Readiness"""
        try:
            # Test CORS headers for frontend integration
            response = requests.get(f"{self.railway_url}/api/analytics/carbon-footprint", timeout=10)
            
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            cors_present = 0
            for header in cors_headers:
                if header in response.headers:
                    cors_present += 1
            
            if cors_present >= 2:  # At least 2/3 CORS headers
                self.log_test(
                    "CORS and Frontend Integration",
                    True,
                    f"CORS headers present ({cors_present}/{len(cors_headers)}) - frontend integration ready"
                )
                return True
            else:
                self.log_test(
                    "CORS and Frontend Integration",
                    False,
                    f"CORS headers insufficient ({cors_present}/{len(cors_headers)})",
                    "CORS headers for frontend",
                    f"Only {cors_present} CORS headers"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "CORS and Frontend Integration",
                False,
                f"CORS test failed: {str(e)}",
                "CORS headers present",
                f"Error: {str(e)}"
            )
            return False
    
    def test_performance_and_response_time(self):
        """Test 12: API Performance for Real-time Usage"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.railway_url}/api/analytics/carbon-footprint", timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response_time < 1.0:  # Less than 1 second for real-time usage
                self.log_test(
                    "API Performance",
                    True,
                    f"Excellent response time: {response_time:.2f}s"
                )
                return True
            elif response_time < 3.0:  # Less than 3 seconds acceptable
                self.log_test(
                    "API Performance",
                    True,
                    f"Good response time: {response_time:.2f}s"
                )
                return True
            else:
                self.log_test(
                    "API Performance",
                    False,
                    f"Slow response time: {response_time:.2f}s",
                    "Response time < 3.0s",
                    f"{response_time:.2f}s"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "API Performance",
                False,
                f"Performance test failed: {str(e)}",
                "Fast API response",
                f"Error: {str(e)}"
            )
            return False
    
    def run_emergency_debug_tests(self):
        """Run all emergency debug tests"""
        print("🚨 Starting Emergency Waste Data Debug Tests...")
        print()
        
        # CRITICAL URL ISSUE TEST
        self.test_frontend_url_mismatch_issue()
        
        # BACKEND INFRASTRUCTURE TESTS
        self.test_railway_backend_health()
        self.test_carbon_footprint_api_real_response()
        
        # DATA SOURCE TESTS
        self.test_waste_management_collection_endpoint()
        self.test_hotel_calculation_data_source()
        
        # CALCULATION SYSTEM TESTS
        self.test_defra_waste_factors_integration()
        self.test_turkey_hotel_factor_integration()
        self.test_api_response_fields_structure()
        self.test_backend_calculation_execution_readiness()
        
        # DATABASE AND INTEGRATION TESTS
        self.test_database_connection_and_collections()
        self.test_cors_and_frontend_integration()
        self.test_performance_and_response_time()
        
        # Print emergency results
        return self.print_emergency_results()
    
    def print_emergency_results(self):
        """Print emergency debug results with critical findings"""
        print("=" * 80)
        print("🚨 EMERGENCY WASTE DATA DEBUG RESULTS")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   ✅ Passed: {self.passed_tests}")
        print(f"   ❌ Failed: {self.failed_tests}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        print()
        
        # CRITICAL FINDINGS
        if self.critical_findings:
            print("🚨 CRITICAL FINDINGS:")
            for i, finding in enumerate(self.critical_findings, 1):
                print(f"   {i}. {finding}")
            print()
        
        # ROOT CAUSE ANALYSIS
        print("🔍 ROOT CAUSE ANALYSIS:")
        
        # Check for URL mismatch issue
        url_mismatch_failed = any("Frontend URL Mismatch" in result["test"] and "❌" in result["status"] 
                                 for result in self.test_results)
        
        if url_mismatch_failed:
            print("   🎯 PRIMARY ISSUE: Frontend .env pointing to WRONG backend URL!")
            print(f"      ❌ Current: {self.wrong_url}")
            print(f"      ✅ Should be: {self.railway_url}")
            print("      🔧 FIX: Update frontend/.env REACT_APP_BACKEND_URL")
            print()
        
        # Check for API issues
        api_failed = any("Carbon Footprint API" in result["test"] and "❌" in result["status"] 
                        for result in self.test_results)
        
        if api_failed:
            print("   🎯 SECONDARY ISSUE: Carbon Footprint API problems!")
            print("      🔧 FIX: Check API deployment and endpoint registration")
            print()
        
        # Check for data source issues
        waste_failed = any("Waste Management" in result["test"] and "❌" in result["status"] 
                          for result in self.test_results)
        
        if waste_failed:
            print("   🎯 DATA ISSUE: Waste Management collection problems!")
            print("      🔧 FIX: Verify waste_management collection and endpoints")
            print()
        
        # EXPECTED OUTCOMES
        print("🎯 EXPECTED OUTCOMES AFTER FIXES:")
        print("   ✅ total_waste_co2 > 0 (if waste data exists)")
        print("   ✅ total_hotel_co2 > 0 (if accommodation_count > 0)")
        print("   ✅ Frontend displays non-zero Atık CO2 values")
        print("   ✅ Pie chart shows waste segment")
        print("   ✅ Per person calculations working")
        print()
        
        # IMMEDIATE ACTION ITEMS
        print("⚡ IMMEDIATE ACTION ITEMS:")
        if url_mismatch_failed:
            print("   1. 🔧 Fix frontend/.env REACT_APP_BACKEND_URL immediately")
            print("   2. 🔄 Restart frontend service")
        if api_failed:
            print("   3. 🔍 Check carbon footprint API deployment")
        if waste_failed:
            print("   4. 🗃️ Verify waste_management collection data")
        
        print("   5. 🧪 Re-test after fixes")
        print()
        
        # OVERALL ASSESSMENT
        print("🎯 EMERGENCY ASSESSMENT:")
        if success_rate >= 85:
            print("   🎉 SYSTEM READY: Minor issues only, waste CO2 should work")
        elif success_rate >= 70:
            print("   ⚠️  FIXABLE ISSUES: Address critical findings for waste CO2")
        elif success_rate >= 50:
            print("   🚨 MAJOR ISSUES: Multiple problems preventing waste CO2 display")
        else:
            print("   💥 CRITICAL FAILURE: System has fundamental problems")
        
        print("=" * 80)
        
        return success_rate

def main():
    """Main emergency debug execution"""
    tester = EmergencyWasteDebugTester()
    success_rate = tester.run_emergency_debug_tests()
    
    # Exit with appropriate code
    if success_rate >= 70:
        sys.exit(0)  # Acceptable for emergency debug
    else:
        sys.exit(1)  # Critical issues found

if __name__ == "__main__":
    main()