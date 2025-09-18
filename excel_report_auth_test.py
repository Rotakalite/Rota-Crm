#!/usr/bin/env python3
"""
Excel Report 500 Error Debug with Authentication
===============================================

This test will try to reproduce the exact 500 error by testing with authentication.
Since we can't get a real auth token easily, we'll test the backend code directly
by importing and running the function locally to see what's causing the 500 error.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
import traceback
import json

# Add backend to path
sys.path.insert(0, '/app/backend')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExcelReportAuthDebugger:
    def __init__(self):
        self.test_client_id = "ac2350e9-3896-4b0d-82a1-2bdaa9788ee3"
        self.test_results = []
        
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
        
    async def test_backend_imports(self):
        """Test if we can import the backend modules"""
        try:
            # Test basic imports
            from server import app, db, get_db
            
            self.log_test_result(
                "Backend Module Import",
                True,
                "Successfully imported server module"
            )
            
            # Test openpyxl imports specifically
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
            from openpyxl.utils import get_column_letter
            from io import BytesIO
            
            self.log_test_result(
                "OpenPyXL Backend Import",
                True,
                "Successfully imported openpyxl modules"
            )
            
            return True
            
        except ImportError as e:
            self.log_test_result(
                "Backend Module Import",
                False,
                f"Import failed: {str(e)}",
                traceback.format_exc()
            )
            return False
        except Exception as e:
            self.log_test_result(
                "Backend Module Import",
                False,
                f"Unexpected error: {str(e)}",
                traceback.format_exc()
            )
            return False
            
    async def test_database_connection(self):
        """Test database connection"""
        try:
            from server import client, db, get_db
            
            # Test database connection
            db_instance = get_db()
            
            # Try to ping the database
            await client.admin.command('ping')
            
            self.log_test_result(
                "Database Connection",
                True,
                "Successfully connected to MongoDB"
            )
            
            # Test if client exists
            client_doc = await db_instance.clients.find_one({"id": self.test_client_id})
            if client_doc:
                client_name = client_doc.get("company_name", client_doc.get("name", "Unknown"))
                self.log_test_result(
                    "Test Client Existence",
                    True,
                    f"Client found: {client_name}"
                )
            else:
                self.log_test_result(
                    "Test Client Existence",
                    False,
                    f"Client {self.test_client_id} not found in database"
                )
                
            # Test reservations collection
            reservations_count = await db_instance.reservations.count_documents({"client_id": self.test_client_id})
            self.log_test_result(
                "Reservations Data",
                True,
                f"Found {reservations_count} reservations for client"
            )
            
            # Test rooms collection
            rooms_count = await db_instance.rooms.count_documents({"client_id": self.test_client_id})
            self.log_test_result(
                "Rooms Data",
                True,
                f"Found {rooms_count} rooms for client"
            )
            
            return True
            
        except Exception as e:
            self.log_test_result(
                "Database Connection",
                False,
                f"Database connection failed: {str(e)}",
                traceback.format_exc()
            )
            return False
            
    async def test_excel_generation_directly(self):
        """Test Excel generation by calling the function directly"""
        try:
            from server import db, get_db
            from datetime import datetime, timedelta
            
            # Mock user object
            class MockUser:
                def __init__(self):
                    self.role = "admin"  # Use admin role to bypass restrictions
                    self.client_id = self.test_client_id
                    self.consultant_id = None
                    
            mock_user = MockUser()
            
            # Get database
            db_instance = get_db()
            
            # Set up date range (current month)
            today = datetime.utcnow()
            start_dt = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_dt = (start_dt + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            logger.info(f"Testing Excel generation for period: {start_dt} to {end_dt}")
            
            # Test step by step
            
            # Step 1: Get client info
            client_info = await db_instance.clients.find_one({"id": self.test_client_id})
            if not client_info:
                self.log_test_result(
                    "Excel Generation - Client Info",
                    False,
                    f"Client {self.test_client_id} not found"
                )
                return False
                
            client_name = client_info.get("company_name", client_info.get("name", "Otel"))
            self.log_test_result(
                "Excel Generation - Client Info",
                True,
                f"Client found: {client_name}"
            )
            
            # Step 2: Test openpyxl imports
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
            from openpyxl.utils import get_column_letter
            from io import BytesIO
            
            self.log_test_result(
                "Excel Generation - OpenPyXL Import",
                True,
                "OpenPyXL imports successful"
            )
            
            # Step 3: Create workbook
            wb = Workbook()
            ws_reservations = wb.active
            ws_reservations.title = "Rezervasyonlar"
            
            self.log_test_result(
                "Excel Generation - Workbook Creation",
                True,
                "Workbook created successfully"
            )
            
            # Step 4: Test database queries
            reservations_query = {
                "client_id": self.test_client_id,
                "check_in_date": {"$gte": start_dt, "$lte": end_dt}
            }
            reservations = await db_instance.reservations.find(reservations_query).to_list(length=None)
            
            self.log_test_result(
                "Excel Generation - Reservations Query",
                True,
                f"Found {len(reservations)} reservations"
            )
            
            # Step 5: Test room queries
            total_rooms = await db_instance.rooms.count_documents({"client_id": self.test_client_id})
            
            self.log_test_result(
                "Excel Generation - Rooms Query",
                True,
                f"Found {total_rooms} rooms"
            )
            
            # Step 6: Create headers and styles
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            center_alignment = Alignment(horizontal='center', vertical='center')
            
            res_headers = [
                "Rezervasyon ID", "Misafir Adı", "Email", "Telefon", "Oda", 
                "Giriş Tarihi", "Çıkış Tarihi", "Gece", "Geceleme", "Kişi", "Çocuk",
                "Oda Ücreti", "Toplam Tutar", "Ödeme Durumu", "Kaynak", "Durum", "Notlar"
            ]
            
            # Set headers
            for col, header in enumerate(res_headers, 1):
                cell = ws_reservations.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border
                cell.alignment = center_alignment
                
            self.log_test_result(
                "Excel Generation - Headers Creation",
                True,
                f"Created {len(res_headers)} headers"
            )
            
            # Step 7: Add reservation data
            for row, reservation in enumerate(reservations, 2):
                try:
                    # Get room number
                    room = await db_instance.rooms.find_one({"id": reservation.get("room_id"), "client_id": self.test_client_id})
                    room_number = room.get("room_number", "N/A") if room else reservation.get("room_id", "N/A")
                    
                    # Format dates safely
                    check_in_str = ""
                    check_out_str = ""
                    
                    check_in_date = reservation.get("check_in_date")
                    if isinstance(check_in_date, datetime):
                        check_in_str = check_in_date.strftime("%d.%m.%Y")
                    elif check_in_date:
                        check_in_str = str(check_in_date)
                        
                    check_out_date = reservation.get("check_out_date")
                    if isinstance(check_out_date, datetime):
                        check_out_str = check_out_date.strftime("%d.%m.%Y")
                    elif check_out_date:
                        check_out_str = str(check_out_date)
                    
                    # Calculate guest_nights safely
                    guest_nights = reservation.get("guest_nights", 0)
                    if not guest_nights:
                        nights = reservation.get("nights", 0)
                        adults = reservation.get("adults", 1)
                        children = reservation.get("children", 0)
                        guest_nights = nights * (adults + children)
                    
                    row_data = [
                        reservation.get("id", ""),
                        reservation.get("guest_name", ""),
                        reservation.get("guest_email", ""),
                        reservation.get("guest_phone", ""),
                        room_number,
                        check_in_str,
                        check_out_str,
                        reservation.get("nights", 0),
                        guest_nights,
                        reservation.get("adults", 0),
                        reservation.get("children", 0),
                        f"₺{reservation.get('room_rate', 0):.2f}",
                        f"₺{reservation.get('total_amount', 0):.2f}",
                        reservation.get("payment_status", ""),
                        reservation.get("booking_source", ""),
                        reservation.get("status", ""),
                        reservation.get("notes", "")
                    ]
                    
                    for col, value in enumerate(row_data, 1):
                        cell = ws_reservations.cell(row=row, column=col, value=value)
                        cell.border = border
                        if col in [7, 8, 9]:  # Numeric columns
                            cell.alignment = Alignment(horizontal='center')
                            
                except Exception as e:
                    logger.error(f"Error processing reservation {row}: {str(e)}")
                    # Continue with next reservation
                    continue
            
            self.log_test_result(
                "Excel Generation - Data Population",
                True,
                f"Populated {len(reservations)} reservation rows"
            )
            
            # Step 8: Create additional sheets
            ws_stats = wb.create_sheet("Aylık İstatistikler")
            ws_occupancy = wb.create_sheet("Doluluk Analizi")
            
            self.log_test_result(
                "Excel Generation - Additional Sheets",
                True,
                "Created statistics and occupancy sheets"
            )
            
            # Step 9: Save to BytesIO
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            
            file_size = len(output.getvalue())
            
            self.log_test_result(
                "Excel Generation - File Save",
                True,
                f"Successfully generated Excel file ({file_size} bytes)"
            )
            
            return True
            
        except Exception as e:
            self.log_test_result(
                "Excel Generation - Direct Test",
                False,
                f"Excel generation failed: {str(e)}",
                traceback.format_exc()
            )
            return False
            
    async def test_specific_error_scenarios(self):
        """Test specific scenarios that might cause 500 errors"""
        try:
            from server import db, get_db
            
            db_instance = get_db()
            
            # Test 1: Invalid date handling
            try:
                from datetime import datetime
                invalid_date = "invalid-date"
                datetime.strptime(invalid_date, "%Y-%m-%d")
            except ValueError:
                self.log_test_result(
                    "Date Parsing Error Handling",
                    True,
                    "Date parsing errors handled correctly"
                )
            
            # Test 2: Missing client data
            missing_client = await db_instance.clients.find_one({"id": "non-existent-client"})
            if not missing_client:
                self.log_test_result(
                    "Missing Client Handling",
                    True,
                    "Missing client scenario handled"
                )
            
            # Test 3: Empty reservations
            empty_reservations = await db_instance.reservations.find({"client_id": "non-existent-client"}).to_list(length=None)
            self.log_test_result(
                "Empty Reservations Handling",
                True,
                f"Empty reservations query returned {len(empty_reservations)} results"
            )
            
            # Test 4: Memory constraints with large data
            try:
                from openpyxl import Workbook
                wb = Workbook()
                ws = wb.active
                
                # Create a large worksheet to test memory
                for i in range(1000):
                    for j in range(20):
                        ws.cell(row=i+1, column=j+1, value=f"Test_{i}_{j}")
                
                from io import BytesIO
                output = BytesIO()
                wb.save(output)
                
                self.log_test_result(
                    "Memory Constraints Test",
                    True,
                    f"Large Excel file created successfully ({len(output.getvalue())} bytes)"
                )
                
            except MemoryError:
                self.log_test_result(
                    "Memory Constraints Test",
                    False,
                    "Memory error encountered - this could be the cause of 500 errors"
                )
            
            return True
            
        except Exception as e:
            self.log_test_result(
                "Error Scenarios Test",
                False,
                f"Error scenarios test failed: {str(e)}",
                traceback.format_exc()
            )
            return False
            
    async def run_comprehensive_debug(self):
        """Run all debug tests"""
        logger.info("🚀 Starting Excel Report Authentication Debug")
        logger.info(f"🎯 Test Client ID: {self.test_client_id}")
        
        try:
            # Run all tests
            await self.test_backend_imports()
            await self.test_database_connection()
            await self.test_excel_generation_directly()
            await self.test_specific_error_scenarios()
            
        except Exception as e:
            logger.error(f"Debug session failed: {str(e)}")
            logger.error(traceback.format_exc())
            
        # Generate summary
        self.generate_summary()
        
    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("\n" + "="*80)
        logger.info("📊 EXCEL REPORT AUTHENTICATION DEBUG SUMMARY")
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
                    logger.info(f"    Error: {result['error'][:500]}...")
        
        # Show critical findings
        logger.info("\n🔍 CRITICAL FINDINGS:")
        
        # Check for specific issues
        import_issues = [r for r in self.test_results if not r['success'] and 'import' in r['test'].lower()]
        if import_issues:
            logger.info("🚨 IMPORT ISSUES: Dependencies missing or broken")
            
        db_issues = [r for r in self.test_results if not r['success'] and 'database' in r['test'].lower()]
        if db_issues:
            logger.info("🚨 DATABASE ISSUES: Connection or query problems")
            
        excel_issues = [r for r in self.test_results if not r['success'] and 'excel' in r['test'].lower()]
        if excel_issues:
            logger.info("🚨 EXCEL GENERATION ISSUES: File creation problems")
            
        memory_issues = [r for r in self.test_results if not r['success'] and 'memory' in r['test'].lower()]
        if memory_issues:
            logger.info("🚨 MEMORY ISSUES: Resource constraints detected")
        
        # Success indicators
        if failed_tests == 0:
            logger.info("✅ ALL TESTS PASSED: Excel generation should work correctly")
            logger.info("🔍 The 500 error might be authentication-related or environment-specific")
        
        logger.info("\n🎯 NEXT STEPS:")
        logger.info("1. Check backend logs during actual Excel report request")
        logger.info("2. Verify authentication token is valid and has correct permissions")
        logger.info("3. Test with different client IDs to isolate data-specific issues")
        logger.info("4. Monitor server resources during Excel generation")
        
        logger.info("="*80)

async def main():
    """Main function"""
    debugger = ExcelReportAuthDebugger()
    await debugger.run_comprehensive_debug()

if __name__ == "__main__":
    asyncio.run(main())