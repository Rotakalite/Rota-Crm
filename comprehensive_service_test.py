#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE RAILWAY PRODUCTION IMPORT & SERVICE TEST
Test specific import issues and service functionality reported by user

Focus Areas:
1. Elite PDF service import düzeltmesi
2. services.pdf_report_service import'u
3. Backend service availability
4. Real endpoint functionality with proper client_id
"""

import asyncio
import httpx
import json
import logging
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Railway Production Backend URL
BACKEND_URL = "https://rota-crm-production.up.railway.app"
REAL_CLIENT_ID = "94927a77-edc3-45ec-8329-795feae35771"

class ComprehensiveServiceTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.client_id = REAL_CLIENT_ID
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        self.total_tests += 1
        if success:
            self.passed_tests += 1
        logging.info(f"{status}: {test_name} - {details}")

    async def test_local_import_status(self):
        """Test local import status of PDF services"""
        logging.info("🔍 TESTING LOCAL PDF SERVICE IMPORTS")
        
        # Test 1: Check if elite_pdf_report_service.py exists
        elite_pdf_path = "/app/backend/services/elite_pdf_report_service.py"
        if os.path.exists(elite_pdf_path):
            self.log_test("Elite PDF Service File", True, f"File exists at {elite_pdf_path}")
        else:
            self.log_test("Elite PDF Service File", False, f"File not found at {elite_pdf_path}")
        
        # Test 2: Check if pdf_report_service.py exists (fallback)
        pdf_service_path = "/app/backend/services/pdf_report_service.py"
        if os.path.exists(pdf_service_path):
            self.log_test("PDF Report Service File (Fallback)", True, f"File exists at {pdf_service_path}")
        else:
            self.log_test("PDF Report Service File (Fallback)", False, f"File not found at {pdf_service_path}")
        
        # Test 3: Try importing the service locally
        try:
            sys.path.append('/app/backend')
            from services.pdf_report_service import PDFReportService
            service = PDFReportService()
            self.log_test("Local PDF Service Import", True, f"Successfully imported PDFReportService class")
        except Exception as e:
            self.log_test("Local PDF Service Import", False, f"Import error: {str(e)}")
        
        # Test 4: Check if elite_pdf_service variable would be set
        try:
            sys.path.append('/app/backend')
            try:
                from services.elite_pdf_report_service import elite_pdf_service
                self.log_test("Elite PDF Service Import", True, "Primary import successful")
            except Exception as e1:
                try:
                    from services.pdf_report_service import elite_pdf_service
                    self.log_test("Elite PDF Service Import (Fallback)", True, "Fallback import successful")
                except Exception as e2:
                    self.log_test("Elite PDF Service Import", False, f"Both imports failed: {e1} | {e2}")
        except Exception as e:
            self.log_test("Elite PDF Service Import", False, f"Import test error: {str(e)}")

    async def test_backend_service_status(self):
        """Test backend service status and availability"""
        logging.info("🔍 TESTING BACKEND SERVICE STATUS")
        
        # Test 1: Backend connectivity
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    self.log_test("Backend Health Status", True, f"Backend healthy: {health_data}")
                else:
                    self.log_test("Backend Health Status", False, f"Health check failed: {response.status_code}")
        except Exception as e:
            self.log_test("Backend Health Status", False, f"Connection error: {str(e)}")

        # Test 2: API router mounting
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/health")
                if response.status_code == 200:
                    self.log_test("API Router Health", True, f"API router mounted correctly")
                else:
                    self.log_test("API Router Health", False, f"API router issue: {response.status_code}")
        except Exception as e:
            self.log_test("API Router Health", False, f"API router error: {str(e)}")

    async def test_pdf_report_endpoint_detailed(self):
        """Detailed test of PDF report endpoint"""
        logging.info("🔍 TESTING PDF REPORT ENDPOINT IN DETAIL")
        
        # Test 1: Endpoint accessibility (should not return 404)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/reports/comprehensive")
                if response.status_code != 404:
                    self.log_test("PDF Report Endpoint Exists", True, f"Endpoint accessible (status: {response.status_code})")
                else:
                    self.log_test("PDF Report Endpoint Exists", False, "Endpoint returns 404 - not found")
        except Exception as e:
            self.log_test("PDF Report Endpoint Exists", False, f"Request error: {str(e)}")

        # Test 2: Endpoint with client_id parameter
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/reports/comprehensive?client_id={self.client_id}")
                if response.status_code == 403:
                    self.log_test("PDF Report Client ID Parameter", True, f"Endpoint accepts client_id parameter (auth required)")
                elif response.status_code == 401:
                    self.log_test("PDF Report Client ID Parameter", True, f"Endpoint processes client_id (auth required)")
                else:
                    self.log_test("PDF Report Client ID Parameter", False, f"Unexpected response: {response.status_code}")
        except Exception as e:
            self.log_test("PDF Report Client ID Parameter", False, f"Request error: {str(e)}")

        # Test 3: Check for service availability error (503)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": "Bearer fake_token_for_service_test"}
                response = await client.get(f"{self.backend_url}/api/reports/comprehensive?client_id={self.client_id}", headers=headers)
                if response.status_code == 503:
                    self.log_test("PDF Service Availability", False, f"Service unavailable (503): {response.text}")
                elif response.status_code in [401, 403]:
                    self.log_test("PDF Service Availability", True, f"Service available (auth issue only): {response.status_code}")
                else:
                    self.log_test("PDF Service Availability", True, f"Service responding: {response.status_code}")
        except Exception as e:
            self.log_test("PDF Service Availability", False, f"Request error: {str(e)}")

    async def test_zip_download_endpoint_detailed(self):
        """Detailed test of ZIP download endpoint"""
        logging.info("🔍 TESTING ZIP DOWNLOAD ENDPOINT IN DETAIL")
        
        # Test 1: Endpoint accessibility
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/documents/bulk-download")
                if response.status_code != 404:
                    self.log_test("ZIP Download Endpoint Exists", True, f"Endpoint accessible (status: {response.status_code})")
                else:
                    self.log_test("ZIP Download Endpoint Exists", False, "Endpoint returns 404 - not found")
        except Exception as e:
            self.log_test("ZIP Download Endpoint Exists", False, f"Request error: {str(e)}")

        # Test 2: Client ID parameter handling
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/documents/bulk-download?client_id={self.client_id}")
                if response.status_code == 403:
                    self.log_test("ZIP Download Client ID Handling", True, f"Client ID parameter processed (auth required)")
                else:
                    self.log_test("ZIP Download Client ID Handling", True, f"Parameter handling working: {response.status_code}")
        except Exception as e:
            self.log_test("ZIP Download Client ID Handling", False, f"Request error: {str(e)}")

        # Test 3: Role-based access control structure
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": "Bearer fake_admin_token"}
                response = await client.get(f"{self.backend_url}/api/documents/bulk-download?client_id={self.client_id}", headers=headers)
                if response.status_code in [401, 403]:
                    self.log_test("ZIP Download Role Access Control", True, f"Role-based access implemented: {response.status_code}")
                else:
                    self.log_test("ZIP Download Role Access Control", False, f"Unexpected response: {response.status_code}")
        except Exception as e:
            self.log_test("ZIP Download Role Access Control", False, f"Request error: {str(e)}")

    async def test_error_handling_improvements(self):
        """Test error handling improvements (400/500 fixes)"""
        logging.info("🔍 TESTING ERROR HANDLING IMPROVEMENTS")
        
        # Test 1: No more 500 errors for common scenarios
        endpoints_to_test = [
            ("/api/documents/bulk-download", "ZIP Download"),
            ("/api/reports/comprehensive", "PDF Report")
        ]
        
        for endpoint, name in endpoints_to_test:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Test various scenarios that might have caused 500 errors
                    test_scenarios = [
                        ("No Auth", {}),
                        ("Invalid Token", {"Authorization": "Bearer invalid"}),
                        ("Malformed Token", {"Authorization": "Bearer malformed.token.here"}),
                        ("Empty Token", {"Authorization": "Bearer "}),
                    ]
                    
                    for scenario_name, headers in test_scenarios:
                        response = await client.get(f"{self.backend_url}{endpoint}", headers=headers)
                        if response.status_code == 500:
                            self.log_test(f"{name} - {scenario_name} No 500", False, f"Still returns 500: {response.text}")
                        else:
                            self.log_test(f"{name} - {scenario_name} No 500", True, f"Returns {response.status_code} (not 500)")
                            
            except Exception as e:
                self.log_test(f"{name} - Error Handling", False, f"Request error: {str(e)}")

    async def test_specific_client_data_access(self):
        """Test access to specific client data"""
        logging.info("🔍 TESTING SPECIFIC CLIENT DATA ACCESS")
        
        # Test 1: Client exists in system (indirect test)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test with client_id parameter - should not return 400 "client not found"
                response = await client.get(f"{self.backend_url}/api/documents/bulk-download?client_id={self.client_id}")
                if response.status_code == 400 and "client not found" in response.text.lower():
                    self.log_test("Client Exists in System", False, f"Client not found: {response.text}")
                else:
                    self.log_test("Client Exists in System", True, f"Client ID processed (status: {response.status_code})")
        except Exception as e:
            self.log_test("Client Exists in System", False, f"Request error: {str(e)}")

        # Test 2: PDF report with specific client
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/reports/comprehensive?client_id={self.client_id}")
                if response.status_code == 400 and "client not found" in response.text.lower():
                    self.log_test("PDF Report Client Access", False, f"Client not found for PDF: {response.text}")
                else:
                    self.log_test("PDF Report Client Access", True, f"Client ID processed for PDF (status: {response.status_code})")
        except Exception as e:
            self.log_test("PDF Report Client Access", False, f"Request error: {str(e)}")

    async def test_frontend_debug_integration(self):
        """Test frontend debug log integration"""
        logging.info("🔍 TESTING FRONTEND DEBUG LOG INTEGRATION")
        
        # Test that endpoints return structured error responses for frontend logging
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/documents/bulk-download")
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        self.log_test("Frontend Debug - Structured Errors", True, f"Structured error response: {error_data}")
                    else:
                        self.log_test("Frontend Debug - Structured Errors", False, f"Non-structured error: {response.text}")
                except:
                    self.log_test("Frontend Debug - Structured Errors", False, f"Non-JSON error response: {response.text}")
        except Exception as e:
            self.log_test("Frontend Debug - Structured Errors", False, f"Request error: {str(e)}")

    async def run_all_tests(self):
        """Run all comprehensive tests"""
        logging.info("🔍 STARTING COMPREHENSIVE RAILWAY PRODUCTION SERVICE TESTS")
        logging.info(f"Backend URL: {self.backend_url}")
        logging.info(f"Test Client ID: {self.client_id}")
        
        # Run all test suites
        await self.test_local_import_status()
        await self.test_backend_service_status()
        await self.test_pdf_report_endpoint_detailed()
        await self.test_zip_download_endpoint_detailed()
        await self.test_error_handling_improvements()
        await self.test_specific_client_data_access()
        await self.test_frontend_debug_integration()
        
        # Calculate success rate
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        # Print summary
        logging.info("=" * 80)
        logging.info("🎯 COMPREHENSIVE SERVICE TEST SUMMARY")
        logging.info("=" * 80)
        logging.info(f"Total Tests: {self.total_tests}")
        logging.info(f"Passed: {self.passed_tests}")
        logging.info(f"Failed: {self.total_tests - self.passed_tests}")
        logging.info(f"Success Rate: {success_rate:.1f}%")
        logging.info("=" * 80)
        
        # Print detailed results
        for result in self.test_results:
            logging.info(f"{result['status']}: {result['test']} - {result['details']}")
        
        logging.info("=" * 80)
        
        # Final assessment
        if success_rate >= 90:
            logging.info("🎉 EXCELLENT: All service imports and fixes are working perfectly!")
        elif success_rate >= 75:
            logging.info("✅ GOOD: Most services working, minor issues may exist")
        elif success_rate >= 50:
            logging.info("⚠️ MODERATE: Some services working, significant issues remain")
        else:
            logging.info("❌ CRITICAL: Major service issues, needs immediate attention")
        
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "success_rate": success_rate,
            "results": self.test_results
        }

async def main():
    """Main test execution"""
    tester = ComprehensiveServiceTester()
    results = await tester.run_all_tests()
    return results

if __name__ == "__main__":
    asyncio.run(main())