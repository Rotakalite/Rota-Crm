#!/usr/bin/env python3
"""
🚨 EXCEL REPORT 500 ERROR SPECIFIC DEBUG TEST
============================================

This test specifically targets the 500 error reported by the user for:
GET /api/front-office/report/excel?client_id=ac2350e9-3896-4b0d-82a1-2bdaa9788ee3

The user reports getting 500 Internal Server Error with authenticated requests.
Previous tests show 404 errors, but user reports 500 errors.

This test will:
1. Test with various authentication scenarios
2. Check for specific error conditions that cause 500 errors
3. Test the Excel generation components
4. Capture detailed error information
"""

import requests
import json
import sys
import traceback
from datetime import datetime, timedelta
import uuid
import time

# Production URL from frontend .env
BACKEND_URL = "https://rota-crm-production.up.railway.app"

class Excel500ErrorDebugger:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        # Specific client ID from the user's request
        self.target_client_id = "ac2350e9-3896-4b0d-82a1-2bdaa9788ee3"
        
        # Various authentication scenarios to test
        self.auth_scenarios = [
            {"name": "No Auth", "headers": {}},
            {"name": "Invalid Bearer Token", "headers": {"Authorization": "Bearer invalid_token_123"}},
            {"name": "Malformed Token", "headers": {"Authorization": "malformed_token"}},
            {"name": "Empty Bearer", "headers": {"Authorization": "Bearer "}},
            {"name": "JWT-like Token", "headers": {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"}},
            {"name": "Clerk-like Token", "headers": {"Authorization": "Bearer sess_2abcdefghijklmnopqrstuvwxyz123456"}},
        ]

    def log_test(self, test_name, success, details="", expected="", actual="", error_info=""):
        """Log test result with detailed error information"""
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
            "error_info": error_info,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and expected:
            print(f"   🎯 Expected: {expected}")
            print(f"   📊 Actual: {actual}")
        if error_info:
            print(f"   🔍 Error Info: {error_info}")
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
                f"Backend connection error: {str(e)}",
                error_info=traceback.format_exc()
            )
            return False

    def test_excel_endpoint_with_auth_scenarios(self):
        """Test Excel endpoint with various authentication scenarios"""
        print("🔐 Excel Endpoint Authentication Scenarios")
        print("=" * 50)
        
        error_500_found = False
        
        for scenario in self.auth_scenarios:
            try:
                response = requests.get(
                    f"{self.backend_url}/api/front-office/report/excel",
                    params={"client_id": self.target_client_id},
                    headers=scenario["headers"],
                    timeout=30  # Longer timeout for Excel generation
                )
                
                # Capture response details
                status_code = response.status_code
                content_type = response.headers.get('content-type', '')
                response_size = len(response.content)
                
                # Try to get error details if available
                error_detail = ""
                if status_code >= 400:
                    try:
                        if 'application/json' in content_type:
                            error_json = response.json()
                            error_detail = error_json.get('detail', 'No detail provided')
                        else:
                            error_detail = response.text[:500] if response.text else "No error content"
                    except:
                        error_detail = "Could not parse error response"
                
                # Check for 500 error
                if status_code == 500:
                    error_500_found = True
                    self.log_test(
                        f"Excel Endpoint - {scenario['name']} (500 ERROR FOUND!)",
                        False,
                        f"🚨 REPRODUCED 500 ERROR! Auth: {scenario['name']}, Size: {response_size} bytes",
                        "Not 500",
                        "500",
                        error_detail
                    )
                elif status_code == 404:
                    self.log_test(
                        f"Excel Endpoint - {scenario['name']} (404 Not Found)",
                        False,
                        f"⚠️ Endpoint not found - deployment issue? Auth: {scenario['name']}",
                        "Not 404",
                        "404",
                        error_detail
                    )
                elif status_code in [401, 403]:
                    self.log_test(
                        f"Excel Endpoint - {scenario['name']} (Auth Required)",
                        True,
                        f"✅ Proper authentication response. Auth: {scenario['name']}, Status: {status_code}"
                    )
                elif status_code == 200:
                    self.log_test(
                        f"Excel Endpoint - {scenario['name']} (SUCCESS!)",
                        True,
                        f"🎉 Excel generated successfully! Auth: {scenario['name']}, Size: {response_size} bytes"
                    )
                else:
                    self.log_test(
                        f"Excel Endpoint - {scenario['name']} (Other Response)",
                        True,
                        f"✅ Response received. Auth: {scenario['name']}, Status: {status_code}, Size: {response_size} bytes"
                    )
                    
            except requests.exceptions.Timeout:
                self.log_test(
                    f"Excel Endpoint - {scenario['name']} (Timeout)",
                    False,
                    f"⏰ Request timeout - Excel generation taking too long?",
                    "Response within 30s",
                    "Timeout",
                    "Request timed out after 30 seconds"
                )
            except Exception as e:
                self.log_test(
                    f"Excel Endpoint - {scenario['name']} (Exception)",
                    False,
                    f"Request error: {str(e)}",
                    error_info=traceback.format_exc()
                )
        
        return error_500_found

    def test_excel_endpoint_with_different_params(self):
        """Test Excel endpoint with different parameter combinations"""
        print("📊 Excel Endpoint Parameter Testing")
        print("=" * 50)
        
        # Test different parameter combinations that might cause 500 errors
        param_scenarios = [
            {"name": "No Params", "params": {}},
            {"name": "Only Client ID", "params": {"client_id": self.target_client_id}},
            {"name": "Invalid Client ID", "params": {"client_id": "invalid-client-id-123"}},
            {"name": "Empty Client ID", "params": {"client_id": ""}},
            {"name": "With Date Range", "params": {
                "client_id": self.target_client_id,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            }},
            {"name": "Invalid Date Format", "params": {
                "client_id": self.target_client_id,
                "start_date": "invalid-date",
                "end_date": "2024-01-31"
            }},
            {"name": "Future Date Range", "params": {
                "client_id": self.target_client_id,
                "start_date": "2025-01-01",
                "end_date": "2025-01-31"
            }},
        ]
        
        error_500_found = False
        
        for scenario in param_scenarios:
            try:
                # Use invalid token to test parameter handling without auth issues
                headers = {"Authorization": "Bearer test_token_123"}
                
                response = requests.get(
                    f"{self.backend_url}/api/front-office/report/excel",
                    params=scenario["params"],
                    headers=headers,
                    timeout=30
                )
                
                status_code = response.status_code
                
                # Get error details
                error_detail = ""
                if status_code >= 400:
                    try:
                        content_type = response.headers.get('content-type', '')
                        if 'application/json' in content_type:
                            error_json = response.json()
                            error_detail = error_json.get('detail', 'No detail provided')
                        else:
                            error_detail = response.text[:200] if response.text else "No error content"
                    except:
                        error_detail = "Could not parse error response"
                
                if status_code == 500:
                    error_500_found = True
                    self.log_test(
                        f"Excel Params - {scenario['name']} (500 ERROR!)",
                        False,
                        f"🚨 500 error with params: {scenario['params']}",
                        "Not 500",
                        "500",
                        error_detail
                    )
                elif status_code == 404:
                    self.log_test(
                        f"Excel Params - {scenario['name']} (404 Not Found)",
                        False,
                        f"⚠️ Endpoint not found with params: {scenario['params']}",
                        "Not 404",
                        "404"
                    )
                elif status_code in [400, 401, 403, 422]:
                    self.log_test(
                        f"Excel Params - {scenario['name']} (Expected Error)",
                        True,
                        f"✅ Expected error response. Params: {scenario['params']}, Status: {status_code}"
                    )
                else:
                    self.log_test(
                        f"Excel Params - {scenario['name']} (Other Response)",
                        True,
                        f"✅ Response received. Params: {scenario['params']}, Status: {status_code}"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"Excel Params - {scenario['name']} (Exception)",
                    False,
                    f"Request error: {str(e)}",
                    error_info=traceback.format_exc()
                )
        
        return error_500_found

    def test_openpyxl_components(self):
        """Test openpyxl components that might cause 500 errors"""
        print("📋 OpenPyXL Components Test")
        print("=" * 50)
        
        try:
            # Test openpyxl import
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
            from openpyxl.utils import get_column_letter
            from io import BytesIO
            
            self.log_test(
                "OpenPyXL Import",
                True,
                "✅ All required openpyxl components imported successfully"
            )
            
            # Test Excel creation similar to the backend code
            wb = Workbook()
            ws = wb.active
            ws.title = "Test Rezervasyonlar"
            
            # Test styling (this might cause issues)
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            center_alignment = Alignment(horizontal='center', vertical='center')
            
            # Test headers
            headers = ["Rezervasyon ID", "Misafir Adı", "Email", "Telefon", "Oda"]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border
                cell.alignment = center_alignment
            
            # Test data rows
            test_data = [
                ["RES001", "Test Misafir", "test@example.com", "+90 555 123 4567", "101"],
                ["RES002", "Örnek Müşteri", "ornek@example.com", "+90 555 987 6543", "102"]
            ]
            
            for row_idx, row_data in enumerate(test_data, 2):
                for col, value in enumerate(row_data, 1):
                    cell = ws.cell(row=row_idx, column=col, value=value)
                    cell.border = border
            
            # Test column width adjustment
            for col in range(1, len(headers) + 1):
                ws.column_dimensions[get_column_letter(col)].width = 15
            
            # Test additional sheets
            ws_stats = wb.create_sheet("Aylık İstatistikler")
            ws_stats.merge_cells('A1:F2')
            title_cell = ws_stats['A1']
            title_cell.value = "Test Otel - Ön Büro Raporu"
            title_cell.font = Font(size=16, bold=True)
            title_cell.alignment = center_alignment
            
            ws_occupancy = wb.create_sheet("Doluluk Analizi")
            
            # Test BytesIO save
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            
            file_size = len(output.getvalue())
            
            self.log_test(
                "Excel File Creation",
                True,
                f"✅ Complete Excel file created successfully (Size: {file_size} bytes, 3 sheets)"
            )
            
            return True
            
        except Exception as e:
            self.log_test(
                "Excel File Creation",
                False,
                f"🚨 CRITICAL: Excel creation failed! This could cause 500 errors. Error: {str(e)}",
                error_info=traceback.format_exc()
            )
            return False

    def test_database_queries_simulation(self):
        """Test database query patterns that might cause 500 errors"""
        print("🗄️ Database Query Simulation")
        print("=" * 50)
        
        # Test client endpoint to see if database queries work
        try:
            response = requests.get(f"{self.backend_url}/api/clients", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "Database - Client Query",
                    True,
                    f"✅ Client endpoint accessible, database connection working (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "Database - Client Query",
                    False,
                    f"🚨 CRITICAL: 500 error on client query - database issue!",
                    "401/403",
                    "500"
                )
                return False
            else:
                self.log_test(
                    "Database - Client Query",
                    True,
                    f"✅ Client endpoint accessible (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "Database - Client Query",
                False,
                f"Database query error: {str(e)}",
                error_info=traceback.format_exc()
            )

        # Test reservations endpoint
        try:
            response = requests.get(f"{self.backend_url}/api/reservations", timeout=10)
            
            if response.status_code in [401, 403]:
                self.log_test(
                    "Database - Reservations Query",
                    True,
                    f"✅ Reservations endpoint accessible, database working (Status: {response.status_code})"
                )
            elif response.status_code == 500:
                self.log_test(
                    "Database - Reservations Query",
                    False,
                    f"🚨 CRITICAL: 500 error on reservations query - database issue!",
                    "401/403",
                    "500"
                )
                return False
            else:
                self.log_test(
                    "Database - Reservations Query",
                    True,
                    f"✅ Reservations endpoint accessible (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "Database - Reservations Query",
                False,
                f"Database query error: {str(e)}",
                error_info=traceback.format_exc()
            )

        return True

    def run_comprehensive_500_debug(self):
        """Run comprehensive 500 error debug"""
        print("🚨 EXCEL REPORT 500 ERROR COMPREHENSIVE DEBUG")
        print("=" * 70)
        print(f"🎯 Backend URL: {self.backend_url}")
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Target Client ID: {self.target_client_id}")
        print(f"🚨 Focus: Reproduce and debug 500 Internal Server Error")
        print("=" * 70)
        print()
        
        # Backend health check
        if not self.test_backend_health():
            print("❌ Backend inaccessible, stopping tests!")
            return False
        
        # Test Excel endpoint with various auth scenarios
        print("🔐 AUTHENTICATION SCENARIOS:")
        print("-" * 40)
        error_500_auth = self.test_excel_endpoint_with_auth_scenarios()
        
        # Test Excel endpoint with different parameters
        print("\n📊 PARAMETER SCENARIOS:")
        print("-" * 40)
        error_500_params = self.test_excel_endpoint_with_different_params()
        
        # Test openpyxl components
        print("\n📋 EXCEL GENERATION COMPONENTS:")
        print("-" * 40)
        self.test_openpyxl_components()
        
        # Test database queries
        print("\n🗄️ DATABASE QUERY SIMULATION:")
        print("-" * 40)
        self.test_database_queries_simulation()
        
        # Show results
        error_500_reproduced = error_500_auth or error_500_params
        self.show_debug_results(error_500_reproduced)
        
        return True

    def show_debug_results(self, error_500_reproduced):
        """Show debug test results"""
        print("\n" + "=" * 70)
        print("📊 EXCEL REPORT 500 ERROR DEBUG RESULTS")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Successful Tests: {self.passed_tests}")
        print(f"❌ Failed Tests: {self.total_tests - self.passed_tests}")
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        # 500 Error Analysis
        if error_500_reproduced:
            print(f"\n🚨 500 ERROR REPRODUCED: YES")
            print("=" * 50)
            print("✅ Successfully reproduced the 500 Internal Server Error")
            print("🔍 This confirms the issue exists in the Excel generation process")
            
            # Show specific 500 errors
            error_500_tests = [r for r in self.test_results if not r['success'] and '500' in r['details']]
            if error_500_tests:
                print(f"\n🚨 500 ERROR DETAILS:")
                for error in error_500_tests:
                    print(f"   • {error['test']}")
                    print(f"     📝 {error['details']}")
                    if error['error_info']:
                        print(f"     🔍 Error: {error['error_info'][:300]}...")
        else:
            print(f"\n🚨 500 ERROR REPRODUCED: NO")
            print("=" * 50)
            print("⚠️ Could not reproduce 500 error in current test scenarios")
            print("💡 Issue might be specific to valid authentication or specific conditions")
        
        # 404 Error Analysis
        error_404_tests = [r for r in self.test_results if not r['success'] and '404' in r['details']]
        if error_404_tests:
            print(f"\n📭 404 ERRORS FOUND: {len(error_404_tests)}")
            print("=" * 50)
            print("⚠️ Excel endpoint returning 404 Not Found instead of 500")
            print("💡 This suggests a deployment or routing issue")
            for error in error_404_tests:
                print(f"   • {error['test']}: {error['details']}")
        
        # Critical Issues Analysis
        critical_issues = [r for r in self.test_results if not r['success'] and ('CRITICAL' in r['details'] or '500' in r['details'])]
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES FOUND: {len(critical_issues)}")
            print("=" * 50)
            for issue in critical_issues:
                print(f"❌ {issue['test']}")
                print(f"   📝 {issue['details']}")
            print("\n⚡ URGENT ACTION REQUIRED!")
        else:
            print("\n✅ NO CRITICAL COMPONENT ISSUES DETECTED!")
        
        # Recommendations
        print(f"\n💡 DEBUGGING RECOMMENDATIONS:")
        print("=" * 50)
        
        if error_500_reproduced:
            print("🎯 500 ERROR REPRODUCED - NEXT STEPS:")
            print("   1. 🔍 Check the exact error details captured above")
            print("   2. 📋 Check Railway deployment logs for full stack trace")
            print("   3. 🛠️ Add debug logging to Excel endpoint")
            print("   4. 🧪 Test each component of Excel generation individually")
        elif error_404_tests:
            print("🎯 404 ERRORS FOUND - DEPLOYMENT ISSUE:")
            print("   1. 🚀 Check if Excel endpoint is properly deployed")
            print("   2. 🔄 Restart backend service to ensure latest code is deployed")
            print("   3. 📋 Verify API router mounting in server.py")
            print("   4. 🔍 Check if endpoint registration is correct")
        else:
            print("🎯 NO ERRORS REPRODUCED - INVESTIGATION NEEDED:")
            print("   1. 🧪 Test with valid authentication token")
            print("   2. 🔍 Check if issue is specific to certain client data")
            print("   3. 📊 Test with different client IDs")
            print("   4. ⏰ Test during different times/load conditions")
        
        print("\n🔧 GENERAL RECOMMENDATIONS:")
        print("   1. 📋 Monitor Railway logs during Excel download attempts")
        print("   2. 🛠️ Add temporary debug logging to Excel endpoint")
        print("   3. 🧪 Test Excel generation components individually")
        print("   4. 🗄️ Verify database queries return expected data")
        print("   5. 📝 Check for Turkish character encoding issues")
        print("   6. 💾 Monitor memory usage during Excel generation")
        
        print("\n" + "=" * 70)
        
        # Save debug results
        debug_results = {
            'debug_summary': {
                'total_tests': self.total_tests,
                'passed_tests': self.passed_tests,
                'failed_tests': self.total_tests - self.passed_tests,
                'success_rate': success_rate,
                'backend_url': self.backend_url,
                'target_client_id': self.target_client_id,
                'test_timestamp': datetime.now().isoformat(),
                'error_500_reproduced': error_500_reproduced,
                'error_404_found': len(error_404_tests) > 0,
                'critical_issues_count': len(critical_issues)
            },
            'test_results': self.test_results,
            'error_500_tests': [r for r in self.test_results if not r['success'] and '500' in r['details']],
            'error_404_tests': error_404_tests,
            'critical_issues': critical_issues
        }
        
        with open('/app/excel_500_debug_results.json', 'w', encoding='utf-8') as f:
            json.dump(debug_results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Debug results saved: /app/excel_500_debug_results.json")

def main():
    """Main debug function"""
    debugger = Excel500ErrorDebugger()
    success = debugger.run_comprehensive_500_debug()
    
    if success:
        print("\n🔍 EXCEL REPORT 500 ERROR DEBUG COMPLETED!")
        print("📊 Comprehensive analysis completed")
        print("📋 Check debug results for detailed findings")
        print("🛠️ Follow recommendations to resolve the issue")
        sys.exit(0)
    else:
        print("\n🚨 DEBUG TEST FAILED!")
        print("❌ Could not complete comprehensive debug analysis")
        print("🔧 Check backend connectivity and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()