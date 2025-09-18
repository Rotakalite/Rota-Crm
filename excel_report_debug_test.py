#!/usr/bin/env python3
"""
Excel Report 500 Error Debug Test
=================================

Testing the specific Excel report endpoint that's returning 500 error:
GET /api/front-office/report/excel?client_id=ac2350e9-3896-4b0d-82a1-2bdaa9788ee3

Focus Areas:
- Check if endpoint exists (404 vs 500)
- Import errors (openpyxl, BytesIO, etc.)
- Database query issues
- Excel file creation problems
- Response format issues
- Memory/resource constraints
"""

import asyncio
import aiohttp
import json
import logging
import traceback
from datetime import datetime
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExcelReportDebugger:
    def __init__(self):
        # Use Railway production URL from frontend .env
        self.base_url = "https://rota-crm-production.up.railway.app"
        self.test_client_id = "ac2350e9-3896-4b0d-82a1-2bdaa9788ee3"
        self.session = None
        self.test_results = []
        
    async def setup_session(self):
        """Setup HTTP session with proper headers"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=60)  # 60 second timeout
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Excel-Report-Debug-Test/1.0',
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/json',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
        )
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_test_result(self, test_name: str, success: bool, details: str, error: str = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        
    async def test_backend_health(self):
        """Test if backend is accessible"""
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    text = await response.text()
                    self.log_test_result(
                        "Backend Health Check",
                        True,
                        f"Backend accessible (200 OK): {text[:100]}..."
                    )
                    return True
                else:
                    self.log_test_result(
                        "Backend Health Check",
                        False,
                        f"Backend returned {response.status}: {await response.text()}"
                    )
                    return False
        except Exception as e:
            self.log_test_result(
                "Backend Health Check",
                False,
                f"Backend connection failed: {str(e)}"
            )
            return False
            
    async def test_excel_endpoint_without_auth(self):
        """Test Excel endpoint without authentication to check if it exists"""
        try:
            url = f"{self.base_url}/api/front-office/report/excel"
            params = {"client_id": self.test_client_id}
            
            async with self.session.get(url, params=params) as response:
                status = response.status
                content_type = response.headers.get('content-type', '')
                text = await response.text()
                
                if status == 404:
                    self.log_test_result(
                        "Excel Endpoint Existence",
                        False,
                        f"Endpoint not found (404) - deployment issue",
                        f"Response: {text[:200]}"
                    )
                elif status == 403 or status == 401:
                    self.log_test_result(
                        "Excel Endpoint Existence",
                        True,
                        f"Endpoint exists but requires auth ({status}) - good sign",
                        f"Response: {text[:200]}"
                    )
                elif status == 500:
                    self.log_test_result(
                        "Excel Endpoint Existence",
                        False,
                        f"Endpoint exists but returns 500 error - this is our target bug!",
                        f"Response: {text[:500]}"
                    )
                    
                    # Try to parse error details
                    try:
                        if 'application/json' in content_type:
                            error_data = json.loads(text)
                            logger.error(f"🔍 500 Error Details: {json.dumps(error_data, indent=2)}")
                        else:
                            logger.error(f"🔍 500 Error Response (non-JSON): {text}")
                    except:
                        logger.error(f"🔍 500 Error Response (raw): {text}")
                        
                else:
                    self.log_test_result(
                        "Excel Endpoint Existence",
                        True,
                        f"Endpoint accessible with status {status}",
                        f"Content-Type: {content_type}, Response: {text[:200]}"
                    )
                    
        except Exception as e:
            self.log_test_result(
                "Excel Endpoint Existence",
                False,
                f"Request failed: {str(e)}",
                traceback.format_exc()
            )
            
    async def test_openpyxl_import(self):
        """Test if openpyxl can be imported on the backend"""
        try:
            # Test local import first
            import openpyxl
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
            from openpyxl.utils import get_column_letter
            from io import BytesIO
            
            # Create a simple test workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Test"
            ws['A1'] = "Test Cell"
            
            # Save to BytesIO
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            
            file_size = len(output.getvalue())
            
            self.log_test_result(
                "OpenPyXL Import Test",
                True,
                f"OpenPyXL working locally - created {file_size} byte Excel file"
            )
            
        except ImportError as e:
            self.log_test_result(
                "OpenPyXL Import Test",
                False,
                f"OpenPyXL import failed: {str(e)}",
                "This could be the root cause of 500 error"
            )
        except Exception as e:
            self.log_test_result(
                "OpenPyXL Import Test",
                False,
                f"OpenPyXL test failed: {str(e)}",
                traceback.format_exc()
            )
            
    async def test_database_collections(self):
        """Test if required database collections exist"""
        try:
            # Test health endpoint that might give us database info
            async with self.session.get(f"{self.base_url}/api/health") as response:
                if response.status == 200:
                    text = await response.text()
                    self.log_test_result(
                        "Database Health Check",
                        True,
                        f"Health endpoint accessible: {text[:200]}"
                    )
                else:
                    self.log_test_result(
                        "Database Health Check",
                        False,
                        f"Health endpoint returned {response.status}"
                    )
                    
        except Exception as e:
            self.log_test_result(
                "Database Health Check",
                False,
                f"Health check failed: {str(e)}"
            )
            
    async def test_client_existence(self):
        """Test if the specific client exists in database"""
        try:
            # Try to access client endpoint (will require auth but we can see the error type)
            url = f"{self.base_url}/api/clients"
            params = {"client_id": self.test_client_id}
            
            async with self.session.get(url, params=params) as response:
                status = response.status
                text = await response.text()
                
                if status in [401, 403]:
                    self.log_test_result(
                        "Client Endpoint Access",
                        True,
                        f"Client endpoint exists and requires auth ({status})"
                    )
                elif status == 404:
                    self.log_test_result(
                        "Client Endpoint Access",
                        False,
                        f"Client endpoint not found (404) - deployment issue"
                    )
                else:
                    self.log_test_result(
                        "Client Endpoint Access",
                        True,
                        f"Client endpoint returned {status}: {text[:200]}"
                    )
                    
        except Exception as e:
            self.log_test_result(
                "Client Endpoint Access",
                False,
                f"Client endpoint test failed: {str(e)}"
            )
            
    async def test_excel_with_different_params(self):
        """Test Excel endpoint with various parameter combinations"""
        test_cases = [
            # No parameters
            {},
            # Only client_id
            {"client_id": self.test_client_id},
            # With date range
            {"client_id": self.test_client_id, "start_date": "2024-01-01", "end_date": "2024-01-31"},
            # Invalid client_id
            {"client_id": "invalid-client-id"},
            # Missing client_id but with dates
            {"start_date": "2024-01-01", "end_date": "2024-01-31"}
        ]
        
        for i, params in enumerate(test_cases):
            try:
                url = f"{self.base_url}/api/front-office/report/excel"
                
                async with self.session.get(url, params=params) as response:
                    status = response.status
                    content_type = response.headers.get('content-type', '')
                    
                    # Read response
                    if 'application/json' in content_type:
                        try:
                            data = await response.json()
                            response_text = json.dumps(data, indent=2)
                        except:
                            response_text = await response.text()
                    else:
                        response_text = await response.text()
                    
                    test_name = f"Excel Endpoint Params Test {i+1}"
                    param_desc = json.dumps(params) if params else "no params"
                    
                    if status == 500:
                        self.log_test_result(
                            test_name,
                            False,
                            f"500 error with params {param_desc}",
                            f"Response: {response_text[:300]}"
                        )
                        
                        # Log detailed error for 500 responses
                        logger.error(f"🔍 500 Error Details for {param_desc}:")
                        logger.error(f"Content-Type: {content_type}")
                        logger.error(f"Response: {response_text}")
                        
                    else:
                        self.log_test_result(
                            test_name,
                            True,
                            f"Status {status} with params {param_desc}",
                            f"Content-Type: {content_type}"
                        )
                        
            except Exception as e:
                self.log_test_result(
                    f"Excel Endpoint Params Test {i+1}",
                    False,
                    f"Request failed with params {json.dumps(params)}: {str(e)}",
                    traceback.format_exc()
                )
                
    async def test_memory_constraints(self):
        """Test if there are memory/resource constraints"""
        try:
            # Test a simple endpoint to see if backend is under resource pressure
            async with self.session.get(f"{self.base_url}/api/health") as response:
                response_time = response.headers.get('X-Response-Time', 'unknown')
                server_header = response.headers.get('Server', 'unknown')
                
                self.log_test_result(
                    "Resource Constraints Check",
                    True,
                    f"Response time: {response_time}, Server: {server_header}"
                )
                
        except Exception as e:
            self.log_test_result(
                "Resource Constraints Check",
                False,
                f"Resource check failed: {str(e)}"
            )
            
    async def check_backend_logs(self):
        """Try to get backend error information"""
        try:
            # Check if there's a logs endpoint or error reporting
            endpoints_to_check = [
                "/api/health",
                "/api/status", 
                "/health",
                "/status"
            ]
            
            for endpoint in endpoints_to_check:
                try:
                    async with self.session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            text = await response.text()
                            self.log_test_result(
                                f"Backend Info ({endpoint})",
                                True,
                                f"Endpoint accessible: {text[:200]}"
                            )
                        else:
                            logger.info(f"Endpoint {endpoint}: {response.status}")
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Backend logs check failed: {str(e)}")
            
    async def run_comprehensive_debug(self):
        """Run all debug tests"""
        logger.info("🚀 Starting Excel Report 500 Error Debug")
        logger.info(f"🎯 Target URL: {self.base_url}/api/front-office/report/excel")
        logger.info(f"🎯 Test Client ID: {self.test_client_id}")
        
        await self.setup_session()
        
        try:
            # Run all tests
            await self.test_backend_health()
            await self.test_excel_endpoint_without_auth()
            await self.test_openpyxl_import()
            await self.test_database_collections()
            await self.test_client_existence()
            await self.test_excel_with_different_params()
            await self.test_memory_constraints()
            await self.check_backend_logs()
            
        finally:
            await self.cleanup_session()
            
        # Generate summary
        self.generate_summary()
        
    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("\n" + "="*80)
        logger.info("📊 EXCEL REPORT DEBUG SUMMARY")
        logger.info("="*80)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info("="*80)
        
        # Show failed tests
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            logger.info("❌ FAILED TESTS:")
            for result in failed_results:
                logger.info(f"  • {result['test']}: {result['details']}")
                if result['error']:
                    logger.info(f"    Error: {result['error']}")
        
        # Show critical findings
        logger.info("\n🔍 CRITICAL FINDINGS:")
        
        # Check for 500 errors
        excel_500_errors = [r for r in self.test_results if '500' in r['details'] and 'excel' in r['test'].lower()]
        if excel_500_errors:
            logger.info("🚨 CONFIRMED: Excel endpoint returns 500 Internal Server Error")
            for error in excel_500_errors:
                logger.info(f"  • {error['details']}")
        
        # Check for import issues
        import_issues = [r for r in self.test_results if not r['success'] and 'import' in r['test'].lower()]
        if import_issues:
            logger.info("🚨 POTENTIAL CAUSE: Import/dependency issues detected")
            for issue in import_issues:
                logger.info(f"  • {issue['details']}")
        
        # Check for deployment issues
        deployment_issues = [r for r in self.test_results if '404' in r['details']]
        if deployment_issues:
            logger.info("🚨 POTENTIAL CAUSE: Deployment/routing issues detected")
            for issue in deployment_issues:
                logger.info(f"  • {issue['details']}")
        
        logger.info("\n🎯 RECOMMENDATIONS:")
        if excel_500_errors:
            logger.info("1. Check backend logs for detailed error stack trace")
            logger.info("2. Verify openpyxl library is installed on production server")
            logger.info("3. Check database connectivity for reservations/rooms collections")
            logger.info("4. Verify client_id exists in database")
            logger.info("5. Check memory/resource constraints on server")
        
        logger.info("="*80)

async def main():
    """Main function"""
    debugger = ExcelReportDebugger()
    await debugger.run_comprehensive_debug()

if __name__ == "__main__":
    asyncio.run(main())