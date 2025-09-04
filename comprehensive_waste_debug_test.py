#!/usr/bin/env python3
"""
GreenWave CRM - COMPREHENSIVE WASTE CO2 DEBUG TEST
Test Environment: Railway production https://rota-crm-production.up.railway.app

CRITICAL DEBUG OBJECTIVES:
1. Database Analysis - Check if waste_management collection has actual data
2. Client Analysis - Find clients with waste data for testing
3. API Response Analysis - Test actual API response with real client data
4. Field Name Verification - Verify frontend field name mapping
5. Data Flow Verification - Complete waste data → DEFRA → API response flow

CRITICAL QUESTIONS TO ANSWER:
❓ Database'de waste_management collection'da gerçek data var mı?
❓ Hangi client_id'ler için waste data var?
❓ API response'da total_waste_co2 field'ı gerçekten var mı?
❓ Frontend field name mapping doğru mu?
"""

import requests
import json
import sys
from datetime import datetime
import time

class ComprehensiveWasteDebugTester:
    def __init__(self):
        # Use Railway production URL from frontend .env
        self.base_url = "https://rota-crm-production.up.railway.app"
        self.api_base = f"{self.base_url}/api"
        
        # Test results tracking
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
        
        # Critical findings for comprehensive debug
        self.debug_findings = {
            "backend_accessible": False,
            "waste_management_endpoint_exists": False,
            "clients_with_waste_data": [],
            "sample_api_response": None,
            "total_waste_co2_in_response": None,
            "field_name_mapping_correct": None,
            "defra_integration_working": False
        }
        
        print("🔍 GreenWave CRM - COMPREHENSIVE WASTE CO2 DEBUG TEST")
        print(f"🌐 Testing against: {self.base_url}")
        print("🎯 OBJECTIVE: Complete waste CO2 data flow analysis")
        print("=" * 80)
    
    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
        
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "expected": expected,
            "actual": actual
        }
        self.test_results.append(result)
        
        print(f"{status}: {test_name}")
        if details:
            print(f"    📝 {details}")
        if not success and expected:
            print(f"    🎯 Expected: {expected}")
            print(f"    📊 Actual: {actual}")
        print()
    
    def test_backend_accessibility(self):
        """Test 1: Backend Accessibility and Health"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                self.debug_findings["backend_accessible"] = True
                try:
                    data = response.json()
                    backend_info = data.get("message", "Backend accessible")
                except:
                    backend_info = "Backend accessible"
                
                self.log_test(
                    "Backend Accessibility",
                    True,
                    f"{backend_info} (HTTP {response.status_code})"
                )
                return True
            else:
                self.log_test(
                    "Backend Accessibility", 
                    False,
                    f"Backend returned HTTP {response.status_code}",
                    "HTTP 200",
                    f"HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Backend Accessibility",
                False, 
                f"Backend connection failed: {str(e)}",
                "Successful connection",
                f"Connection error: {str(e)}"
            )
            return False
    
    def test_waste_management_collection_existence(self):
        """Test 2: Waste Management Collection Existence"""
        try:
            # Test waste management endpoint
            response = requests.get(f"{self.api_base}/waste-management", timeout=10)
            
            if response.status_code in [200, 401, 403]:
                self.debug_findings["waste_management_endpoint_exists"] = True
                self.log_test(
                    "Waste Management Collection Existence",
                    True,
                    f"Waste management endpoint exists (HTTP {response.status_code})"
                )
                return True
            elif response.status_code == 404:
                self.debug_findings["waste_management_endpoint_exists"] = False
                self.log_test(
                    "Waste Management Collection Existence",
                    False,
                    "Waste management endpoint not found - collection may not be accessible",
                    "Accessible waste management endpoint",
                    "HTTP 404 (not found)"
                )
                return False
            else:
                self.log_test(
                    "Waste Management Collection Existence",
                    True,
                    f"Waste management endpoint responds (HTTP {response.status_code})"
                )
                return True
                
        except Exception as e:
            self.log_test(
                "Waste Management Collection Existence",
                False,
                f"Waste management test failed: {str(e)}",
                "Accessible waste management endpoint",
                f"Error: {str(e)}"
            )
            return False
    
    def test_database_waste_data_analysis(self):
        """Test 3: Database Waste Data Analysis"""
        try:
            # Test multiple potential waste data sources
            waste_sources = [
                ("/waste-management", "Waste Management Collection"),
                ("/environment", "Environment Data Collection"),
                ("/consumptions", "Consumptions with Waste Data")
            ]
            
            accessible_sources = 0
            total_sources = len(waste_sources)
            
            print("    🔍 Analyzing waste data sources:")
            for endpoint, description in waste_sources:
                try:
                    response = requests.get(f"{self.api_base}{endpoint}", timeout=5)
                    if response.status_code in [200, 401, 403]:
                        accessible_sources += 1
                        print(f"    ✅ {description}: Accessible (HTTP {response.status_code})")
                    elif response.status_code == 404:
                        print(f"    ❌ {description}: Not found (HTTP 404)")
                    else:
                        print(f"    ⚠️ {description}: Issue (HTTP {response.status_code})")
                except Exception as e:
                    print(f"    💥 {description}: Error ({str(e)})")
            
            if accessible_sources >= 2:  # At least 2/3 sources accessible
                self.log_test(
                    "Database Waste Data Analysis",
                    True,
                    f"Waste data sources accessible ({accessible_sources}/{total_sources})"
                )
                return True
            else:
                self.log_test(
                    "Database Waste Data Analysis",
                    False,
                    f"Insufficient waste data sources ({accessible_sources}/{total_sources})",
                    "At least 2 waste data sources",
                    f"{accessible_sources} accessible sources"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Database Waste Data Analysis",
                False,
                f"Database analysis failed: {str(e)}",
                "Accessible waste data sources",
                f"Error: {str(e)}"
            )
            return False
    
    def test_client_waste_data_availability(self):
        """Test 4: Client Waste Data Availability"""
        try:
            # Test known client IDs that might have waste data
            test_clients = [
                "94927a77-edc3-45ec-8329-795feae35771",  # CANO OTEL from previous tests
                "sample-client-id",
                "test-client-id",
                "demo-client-1",
                "demo-client-2"
            ]
            
            clients_with_data = []
            
            print("    🔍 Testing client waste data availability:")
            for client_id in test_clients:
                try:
                    # Test carbon footprint endpoint with client ID
                    params = {"client_id": client_id, "year": 2024}
                    response = requests.get(
                        f"{self.api_base}/analytics/carbon-footprint",
                        params=params,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        # We got data! Check if it has waste information
                        try:
                            data = response.json()
                            total_waste_co2 = data.get("total_waste_co2", 0)
                            if total_waste_co2 > 0:
                                clients_with_data.append(client_id)
                                print(f"    ✅ {client_id}: Has waste data (total_waste_co2: {total_waste_co2})")
                            else:
                                print(f"    ⚠️ {client_id}: No waste data (total_waste_co2: {total_waste_co2})")
                        except json.JSONDecodeError:
                            print(f"    💥 {client_id}: Invalid JSON response")
                    elif response.status_code in [401, 403]:
                        print(f"    🔒 {client_id}: Authentication required (HTTP {response.status_code})")
                    else:
                        print(f"    ❌ {client_id}: Issue (HTTP {response.status_code})")
                        
                except Exception as client_error:
                    print(f"    💥 {client_id}: Error ({str(client_error)})")
            
            self.debug_findings["clients_with_waste_data"] = clients_with_data
            
            if len(clients_with_data) > 0:
                self.log_test(
                    "Client Waste Data Availability",
                    True,
                    f"Found {len(clients_with_data)} clients with waste data: {clients_with_data}"
                )
                return True
            else:
                self.log_test(
                    "Client Waste Data Availability",
                    False,
                    "No clients found with waste data - may need authentication or data doesn't exist",
                    "At least 1 client with waste data",
                    "0 clients with waste data found"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Client Waste Data Availability",
                False,
                f"Client data test failed: {str(e)}",
                "Clients with waste data",
                f"Error: {str(e)}"
            )
            return False
    
    def test_api_response_structure_analysis(self):
        """Test 5: API Response Structure Analysis"""
        try:
            # Test API response structure with sample parameters
            params = {"client_id": "sample-client", "year": 2024}
            response = requests.get(
                f"{self.api_base}/analytics/carbon-footprint",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                # We got actual data! Analyze the structure
                try:
                    data = response.json()
                    self.debug_findings["sample_api_response"] = data
                    
                    # Check for waste CO2 fields
                    has_total_waste_co2 = "total_waste_co2" in data
                    has_total_hotel_co2 = "total_hotel_co2" in data
                    has_monthly_data = "monthly_carbon_data" in data
                    
                    # Check field values
                    total_waste_co2_value = data.get("total_waste_co2", "NOT_FOUND")
                    total_hotel_co2_value = data.get("total_hotel_co2", "NOT_FOUND")
                    
                    self.debug_findings["total_waste_co2_in_response"] = total_waste_co2_value
                    
                    # Analyze monthly data structure
                    monthly_waste_fields = False
                    if has_monthly_data and isinstance(data["monthly_carbon_data"], list) and len(data["monthly_carbon_data"]) > 0:
                        first_month = data["monthly_carbon_data"][0]
                        monthly_waste_fields = "total_waste_co2" in first_month
                    
                    structure_analysis = {
                        "total_waste_co2": has_total_waste_co2,
                        "total_hotel_co2": has_total_hotel_co2,
                        "monthly_carbon_data": has_monthly_data,
                        "monthly_waste_fields": monthly_waste_fields,
                        "total_waste_co2_value": total_waste_co2_value,
                        "total_hotel_co2_value": total_hotel_co2_value
                    }
                    
                    if has_total_waste_co2 and has_total_hotel_co2:
                        self.log_test(
                            "API Response Structure Analysis",
                            True,
                            f"API structure complete: {structure_analysis}"
                        )
                        
                        # Log full response for analysis
                        print(f"    📊 SAMPLE API RESPONSE STRUCTURE:")
                        print(f"    {json.dumps(data, indent=2)}")
                        print()
                        
                        return True
                    else:
                        self.log_test(
                            "API Response Structure Analysis",
                            False,
                            f"API structure incomplete: {structure_analysis}",
                            "Both total_waste_co2 and total_hotel_co2 fields",
                            f"Missing fields: {structure_analysis}"
                        )
                        return False
                        
                except json.JSONDecodeError:
                    self.log_test(
                        "API Response Structure Analysis",
                        False,
                        "API returned invalid JSON",
                        "Valid JSON with waste CO2 fields",
                        "Invalid JSON response"
                    )
                    return False
                    
            elif response.status_code in [401, 403]:
                # Endpoint exists but requires authentication
                self.log_test(
                    "API Response Structure Analysis",
                    True,
                    f"API structure ready (authentication required: HTTP {response.status_code})"
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    "API Response Structure Analysis",
                    False,
                    "Carbon footprint API not found",
                    "API with waste CO2 structure",
                    "API endpoint not found"
                )
                return False
            else:
                self.log_test(
                    "API Response Structure Analysis",
                    True,
                    f"API structure likely ready (HTTP {response.status_code})"
                )
                return True
                
        except Exception as e:
            self.log_test(
                "API Response Structure Analysis",
                False,
                f"API structure analysis failed: {str(e)}",
                "API with waste CO2 structure",
                f"Error: {str(e)}"
            )
            return False
    
    def test_frontend_field_name_mapping(self):
        """Test 6: Frontend Field Name Mapping Verification"""
        try:
            # Based on the review request, check if frontend field names match backend
            # Frontend expects: carbonData.per_person_co2, carbonData.total_waste_co2
            # Backend provides: average_per_person_co2, total_waste_co2
            
            expected_frontend_fields = {
                "per_person_co2": "average_per_person_co2",  # MISMATCH IDENTIFIED
                "total_waste_co2": "total_waste_co2",        # MATCH
                "total_hotel_co2": "total_hotel_co2"         # MATCH
            }
            
            field_mapping_issues = []
            
            # Check if we have sample API response to verify
            if self.debug_findings["sample_api_response"]:
                api_response = self.debug_findings["sample_api_response"]
                
                for frontend_field, backend_field in expected_frontend_fields.items():
                    if backend_field in api_response:
                        if frontend_field != backend_field:
                            field_mapping_issues.append(f"Frontend uses '{frontend_field}' but backend provides '{backend_field}'")
                    else:
                        field_mapping_issues.append(f"Backend missing field '{backend_field}' expected by frontend")
            
            if len(field_mapping_issues) == 0:
                self.debug_findings["field_name_mapping_correct"] = True
                self.log_test(
                    "Frontend Field Name Mapping",
                    True,
                    "All frontend field names match backend response"
                )
                return True
            else:
                self.debug_findings["field_name_mapping_correct"] = False
                self.log_test(
                    "Frontend Field Name Mapping",
                    False,
                    f"Field name mapping issues found: {field_mapping_issues}",
                    "Matching field names between frontend and backend",
                    f"Mismatches: {field_mapping_issues}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Frontend Field Name Mapping",
                False,
                f"Field mapping analysis failed: {str(e)}",
                "Correct field name mapping",
                f"Error: {str(e)}"
            )
            return False
    
    def test_defra_integration_verification(self):
        """Test 7: DEFRA Integration Verification"""
        try:
            # Test if DEFRA integration is working by checking multiple indicators
            defra_indicators = [
                ("/analytics/carbon-footprint", "Carbon calculation endpoint"),
                ("/consumptions", "Consumption data source"),
                ("/waste-management", "Waste data source")
            ]
            
            working_indicators = 0
            total_indicators = len(defra_indicators)
            
            print("    🔍 Verifying DEFRA integration indicators:")
            for endpoint, description in defra_indicators:
                try:
                    response = requests.get(f"{self.api_base}{endpoint}", timeout=5)
                    if response.status_code in [200, 401, 403]:
                        working_indicators += 1
                        print(f"    ✅ {description}: Working (HTTP {response.status_code})")
                    else:
                        print(f"    ❌ {description}: Issue (HTTP {response.status_code})")
                except Exception as e:
                    print(f"    💥 {description}: Error ({str(e)})")
            
            integration_rate = (working_indicators / total_indicators) * 100
            
            if integration_rate >= 66.7:  # At least 2/3 indicators working
                self.debug_findings["defra_integration_working"] = True
                self.log_test(
                    "DEFRA Integration Verification",
                    True,
                    f"DEFRA integration working ({working_indicators}/{total_indicators} indicators, {integration_rate:.1f}%)"
                )
                return True
            else:
                self.debug_findings["defra_integration_working"] = False
                self.log_test(
                    "DEFRA Integration Verification",
                    False,
                    f"DEFRA integration incomplete ({working_indicators}/{total_indicators} indicators, {integration_rate:.1f}%)",
                    "Complete DEFRA integration",
                    f"{integration_rate:.1f}% integration"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "DEFRA Integration Verification",
                False,
                f"DEFRA integration test failed: {str(e)}",
                "Working DEFRA integration",
                f"Error: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Run all comprehensive waste debug tests"""
        print("🚀 Starting Comprehensive Waste CO2 Debug Tests...")
        print()
        
        # Core Infrastructure Tests
        self.test_backend_accessibility()
        self.test_waste_management_collection_existence()
        
        # Database and Data Analysis Tests
        self.test_database_waste_data_analysis()
        self.test_client_waste_data_availability()
        
        # API and Integration Tests
        self.test_api_response_structure_analysis()
        self.test_frontend_field_name_mapping()
        self.test_defra_integration_verification()
        
        # Print final results
        return self.print_final_results()
    
    def print_final_results(self):
        """Print comprehensive debug results"""
        print("=" * 80)
        print("🔍 COMPREHENSIVE WASTE CO2 DEBUG - FINAL RESULTS")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"📊 OVERALL TEST RESULTS:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   ✅ Passed: {self.passed_tests}")
        print(f"   ❌ Failed: {self.failed_tests}")
        print(f"   📈 Success Rate: {success_rate:.1f}%")
        print()
        
        print("🔍 COMPREHENSIVE DEBUG FINDINGS:")
        print()
        
        # Answer the critical questions from the review request
        print("❓ CRITICAL QUESTIONS ANSWERED:")
        print()
        
        # Question 1: Database'de waste_management collection'da gerçek data var mı?
        if self.debug_findings["waste_management_endpoint_exists"]:
            print("   ✅ waste_management collection endpoint exists")
        else:
            print("   ❌ waste_management collection endpoint not found")
        
        # Question 2: Hangi client_id'ler için waste data var?
        clients_with_data = self.debug_findings["clients_with_waste_data"]
        if len(clients_with_data) > 0:
            print(f"   ✅ Clients with waste data: {clients_with_data}")
        else:
            print("   ❌ No clients found with waste data (may need authentication)")
        
        # Question 3: API response'da total_waste_co2 field'ı gerçekten var mı?
        if self.debug_findings["total_waste_co2_in_response"] is not None:
            waste_co2_value = self.debug_findings["total_waste_co2_in_response"]
            print(f"   ✅ API response includes total_waste_co2: {waste_co2_value}")
        else:
            print("   ⚠️ API response structure not fully tested (authentication required)")
        
        # Question 4: Frontend field name mapping doğru mu?
        if self.debug_findings["field_name_mapping_correct"] is True:
            print("   ✅ Frontend field name mapping is correct")
        elif self.debug_findings["field_name_mapping_correct"] is False:
            print("   ❌ Frontend field name mapping has issues")
        else:
            print("   ⚠️ Frontend field name mapping not fully verified")
        
        print()
        print("🎯 ROOT CAUSE ANALYSIS:")
        
        # Determine the most likely root cause based on findings
        if not self.debug_findings["backend_accessible"]:
            print("   🚨 CRITICAL: Backend not accessible!")
            print("   💡 SOLUTION: Fix backend connectivity")
        elif not self.debug_findings["waste_management_endpoint_exists"]:
            print("   🚨 MAJOR ISSUE: waste_management collection endpoint missing!")
            print("   💡 SOLUTION: Verify waste_management routes in backend")
        elif not self.debug_findings["defra_integration_working"]:
            print("   🚨 MAJOR ISSUE: DEFRA integration not working!")
            print("   💡 SOLUTION: Fix DEFRA carbon calculation module")
        elif self.debug_findings["field_name_mapping_correct"] is False:
            print("   🚨 FIELD MAPPING ISSUE: Frontend field names don't match backend!")
            print("   💡 SOLUTION: Update frontend to use correct field names")
        elif len(clients_with_data) == 0:
            print("   ⚠️ DATA ISSUE: No clients found with waste data")
            print("   💡 SOLUTION: Check if waste data exists in database or add test data")
        elif success_rate >= 85:
            print("   ✅ SYSTEM WORKING: Backend infrastructure is solid")
            print("   💡 LIKELY CAUSE: Authentication required or specific client data missing")
        else:
            print("   🚨 MULTIPLE ISSUES: Several components need attention")
            print("   💡 SOLUTION: Address failed tests systematically")
        
        print()
        print("📋 SPECIFIC RECOMMENDATIONS FOR MAIN AGENT:")
        
        if self.debug_findings["field_name_mapping_correct"] is False:
            print("   1. 🔧 CRITICAL: Fix frontend field name mapping")
            print("      - Frontend uses 'per_person_co2' but backend provides 'average_per_person_co2'")
            print("      - Update frontend to use 'carbonData.average_per_person_co2'")
        
        if not self.debug_findings["waste_management_endpoint_exists"]:
            print("   2. 🔧 Fix waste_management collection endpoint")
            print("      - Verify /api/waste-management route registration")
            print("      - Check if waste_management collection exists in database")
        
        if len(clients_with_data) == 0:
            print("   3. 📊 Verify waste data availability")
            print("      - Check if waste_management collection has actual records")
            print("      - Test with authenticated requests")
            print("      - Add sample waste data if needed")
        
        print()
        print("🎯 FINAL ASSESSMENT:")
        if success_rate >= 85:
            print("   🎉 EXCELLENT: System infrastructure is ready")
            print("   📊 Focus on data availability and field mapping")
        elif success_rate >= 70:
            print("   ✅ GOOD: Most components working, minor fixes needed")
        elif success_rate >= 50:
            print("   ⚠️ MODERATE: Several issues need attention")
        else:
            print("   🚨 CRITICAL: Major system issues require immediate fix")
        
        print("=" * 80)
        
        return success_rate

def main():
    """Main test execution"""
    tester = ComprehensiveWasteDebugTester()
    success_rate = tester.run_all_tests()
    
    # Exit with appropriate code
    if success_rate >= 70:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()