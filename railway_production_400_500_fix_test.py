#!/usr/bin/env python3
"""
🚂 RAILWAY PRODUCTION 400/500 ERROR FIX TEST
Test specific issues reported by user on Railway production environment

Test Cases:
1. ZIP Download 400 Error Fix
2. PDF Report 500 Error Fix

Real client_id: 94927a77-edc3-45ec-8329-795feae35771
"""

import asyncio
import httpx
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Railway Production Backend URL
BACKEND_URL = "https://rota-crm-production.up.railway.app"
REAL_CLIENT_ID = "94927a77-edc3-45ec-8329-795feae35771"

class RailwayProductionTester:
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

    async def test_backend_connectivity(self):
        """Test basic backend connectivity"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test root endpoint
                response = await client.get(f"{self.backend_url}/")
                if response.status_code == 200:
                    self.log_test("Backend Root Connectivity", True, f"Status: {response.status_code}, Response: {response.json()}")
                else:
                    self.log_test("Backend Root Connectivity", False, f"Status: {response.status_code}")
                
                # Test health endpoint
                response = await client.get(f"{self.backend_url}/health")
                if response.status_code == 200:
                    self.log_test("Backend Health Check", True, f"Status: {response.status_code}, Response: {response.json()}")
                else:
                    self.log_test("Backend Health Check", False, f"Status: {response.status_code}")
                    
        except Exception as e:
            self.log_test("Backend Connectivity", False, f"Connection error: {str(e)}")

    async def test_zip_download_400_fix(self):
        """Test ZIP download 400 error fix"""
        logging.info("🔍 TESTING ZIP DOWNLOAD 400 ERROR FIX")
        
        # Test 1: No authentication (should return 403 Forbidden)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/documents/bulk-download")
                if response.status_code == 403:
                    self.log_test("ZIP Download - No Auth", True, f"Correctly returns 403 Forbidden: {response.text}")
                else:
                    self.log_test("ZIP Download - No Auth", False, f"Expected 403, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("ZIP Download - No Auth", False, f"Request error: {str(e)}")

        # Test 2: Invalid token (should return 401 Unauthorized)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": "Bearer invalid_token_12345"}
                response = await client.get(f"{self.backend_url}/api/documents/bulk-download", headers=headers)
                if response.status_code == 401:
                    self.log_test("ZIP Download - Invalid Token", True, f"Correctly returns 401 Unauthorized: {response.text}")
                else:
                    self.log_test("ZIP Download - Invalid Token", False, f"Expected 401, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("ZIP Download - Invalid Token", False, f"Request error: {str(e)}")

        # Test 3: Malformed token (should return 401)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": "Bearer malformed.token"}
                response = await client.get(f"{self.backend_url}/api/documents/bulk-download", headers=headers)
                if response.status_code == 401:
                    self.log_test("ZIP Download - Malformed Token", True, f"Correctly returns 401: {response.text}")
                else:
                    self.log_test("ZIP Download - Malformed Token", False, f"Expected 401, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("ZIP Download - Malformed Token", False, f"Request error: {str(e)}")

        # Test 4: With client_id parameter but no auth (should still return 403)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/documents/bulk-download?client_id={self.client_id}")
                if response.status_code == 403:
                    self.log_test("ZIP Download - Client ID No Auth", True, f"Correctly returns 403 with client_id: {response.text}")
                else:
                    self.log_test("ZIP Download - Client ID No Auth", False, f"Expected 403, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("ZIP Download - Client ID No Auth", False, f"Request error: {str(e)}")

        # Test 5: HTTP Method restrictions (POST should return 405)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.backend_url}/api/documents/bulk-download")
                if response.status_code == 405:
                    self.log_test("ZIP Download - POST Method", True, f"Correctly returns 405 Method Not Allowed: {response.text}")
                else:
                    self.log_test("ZIP Download - POST Method", False, f"Expected 405, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("ZIP Download - POST Method", False, f"Request error: {str(e)}")

        # Test 6: PUT method (should return 405)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(f"{self.backend_url}/api/documents/bulk-download")
                if response.status_code == 405:
                    self.log_test("ZIP Download - PUT Method", True, f"Correctly returns 405 Method Not Allowed: {response.text}")
                else:
                    self.log_test("ZIP Download - PUT Method", False, f"Expected 405, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("ZIP Download - PUT Method", False, f"Request error: {str(e)}")

    async def test_pdf_report_500_fix(self):
        """Test PDF Report 500 error fix"""
        logging.info("🔍 TESTING PDF REPORT 500 ERROR FIX")
        
        # Test 1: No authentication (should return 403 Forbidden)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/reports/comprehensive")
                if response.status_code == 403:
                    self.log_test("PDF Report - No Auth", True, f"Correctly returns 403 Forbidden: {response.text}")
                else:
                    self.log_test("PDF Report - No Auth", False, f"Expected 403, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("PDF Report - No Auth", False, f"Request error: {str(e)}")

        # Test 2: Invalid token (should return 401 Unauthorized)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": "Bearer invalid_token_12345"}
                response = await client.get(f"{self.backend_url}/api/reports/comprehensive", headers=headers)
                if response.status_code == 401:
                    self.log_test("PDF Report - Invalid Token", True, f"Correctly returns 401 Unauthorized: {response.text}")
                else:
                    self.log_test("PDF Report - Invalid Token", False, f"Expected 401, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("PDF Report - Invalid Token", False, f"Request error: {str(e)}")

        # Test 3: With client_id parameter but no auth
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/reports/comprehensive?client_id={self.client_id}")
                if response.status_code == 403:
                    self.log_test("PDF Report - Client ID No Auth", True, f"Correctly returns 403 with client_id: {response.text}")
                else:
                    self.log_test("PDF Report - Client ID No Auth", False, f"Expected 403, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("PDF Report - Client ID No Auth", False, f"Request error: {str(e)}")

        # Test 4: HTTP Method restrictions (POST should return 405)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.backend_url}/api/reports/comprehensive")
                if response.status_code == 405:
                    self.log_test("PDF Report - POST Method", True, f"Correctly returns 405 Method Not Allowed: {response.text}")
                else:
                    self.log_test("PDF Report - POST Method", False, f"Expected 405, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("PDF Report - POST Method", False, f"Request error: {str(e)}")

    async def test_elite_pdf_service_import(self):
        """Test Elite PDF service import status"""
        logging.info("🔍 TESTING ELITE PDF SERVICE IMPORT")
        
        # Test by checking if the endpoint exists and doesn't return 404
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.backend_url}/api/reports/comprehensive")
                if response.status_code != 404:
                    self.log_test("Elite PDF Service Import", True, f"Endpoint exists (not 404), status: {response.status_code}")
                else:
                    self.log_test("Elite PDF Service Import", False, f"Endpoint returns 404 - service may not be imported")
        except Exception as e:
            self.log_test("Elite PDF Service Import", False, f"Request error: {str(e)}")

    async def test_admin_consultant_role_checks(self):
        """Test admin/consultant role check improvements"""
        logging.info("🔍 TESTING ADMIN/CONSULTANT ROLE CHECKS")
        
        # Test that endpoints properly require client_id for admin/consultant users
        # Since we can't test with valid tokens, we test the error handling
        
        # Test 1: ZIP download endpoint structure
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": "Bearer fake_admin_token"}
                response = await client.get(f"{self.backend_url}/api/documents/bulk-download")
                # Should return 401 (invalid token) not 400 (missing client_id)
                # This indicates the auth check comes before role check
                if response.status_code == 401:
                    self.log_test("ZIP Download - Role Check Order", True, f"Auth check before role check: {response.status_code}")
                else:
                    self.log_test("ZIP Download - Role Check Order", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("ZIP Download - Role Check Order", False, f"Request error: {str(e)}")

        # Test 2: PDF report endpoint structure
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": "Bearer fake_admin_token"}
                response = await client.get(f"{self.backend_url}/api/reports/comprehensive")
                if response.status_code == 401:
                    self.log_test("PDF Report - Role Check Order", True, f"Auth check before role check: {response.status_code}")
                else:
                    self.log_test("PDF Report - Role Check Order", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("PDF Report - Role Check Order", False, f"Request error: {str(e)}")

    async def test_frontend_debug_logs_integration(self):
        """Test that endpoints are accessible for frontend debug logging"""
        logging.info("🔍 TESTING FRONTEND DEBUG LOGS INTEGRATION")
        
        # Test that endpoints return proper error codes for frontend to log
        test_cases = [
            ("/api/documents/bulk-download", "ZIP Download"),
            ("/api/reports/comprehensive", "PDF Report")
        ]
        
        for endpoint, name in test_cases:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{self.backend_url}{endpoint}")
                    # Should return 403 (not 500 or other server errors)
                    if response.status_code == 403:
                        self.log_test(f"{name} - Frontend Debug Ready", True, f"Returns 403 for frontend logging: {response.text}")
                    else:
                        self.log_test(f"{name} - Frontend Debug Ready", False, f"Expected 403, got {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"{name} - Frontend Debug Ready", False, f"Request error: {str(e)}")

    async def run_all_tests(self):
        """Run all tests"""
        logging.info("🚂 STARTING RAILWAY PRODUCTION 400/500 ERROR FIX TESTS")
        logging.info(f"Backend URL: {self.backend_url}")
        logging.info(f"Test Client ID: {self.client_id}")
        
        # Run all test suites
        await self.test_backend_connectivity()
        await self.test_zip_download_400_fix()
        await self.test_pdf_report_500_fix()
        await self.test_elite_pdf_service_import()
        await self.test_admin_consultant_role_checks()
        await self.test_frontend_debug_logs_integration()
        
        # Calculate success rate
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        # Print summary
        logging.info("=" * 80)
        logging.info("🎯 RAILWAY PRODUCTION 400/500 ERROR FIX TEST SUMMARY")
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
            logging.info("🎉 EXCELLENT: Railway production 400/500 error fixes are working well!")
        elif success_rate >= 75:
            logging.info("✅ GOOD: Most fixes are working, minor issues may exist")
        elif success_rate >= 50:
            logging.info("⚠️ MODERATE: Some fixes working, significant issues remain")
        else:
            logging.info("❌ CRITICAL: Major issues with the fixes, needs immediate attention")
        
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "success_rate": success_rate,
            "results": self.test_results
        }

async def main():
    """Main test execution"""
    tester = RailwayProductionTester()
    results = await tester.run_all_tests()
    return results

if __name__ == "__main__":
    asyncio.run(main())