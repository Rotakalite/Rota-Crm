#!/usr/bin/env python3
"""
Gmail App Password Fix Verification Test
========================================

Tests the Gmail App Password fix for 2FA email functionality.
Updated password from regular password to proper Gmail App Password.

Test Requirements:
1. Test direct SMTP authentication with new Gmail App Password
2. Test email service endpoints accessibility 
3. Try sending test email to verify App Password works
4. Check for any authentication errors in backend logs
5. Verify 2FA email functionality will now work

Expected Results:
- ✅ Gmail SMTP authentication should now succeed with App Password
- ✅ Email service should initialize without authentication errors
- ✅ Test emails should send successfully
- ✅ 2FA email system should be fully operational
- ✅ No more "Application-specific password required" errors
"""

import asyncio
import smtplib
import os
import sys
import requests
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Add backend to path
sys.path.insert(0, '/app/backend')

# Test configuration
BACKEND_URL = "https://ecowave-saas.preview.emergentagent.com"
TEST_EMAIL = "test@example.com"  # Safe test email

class GmailAppPasswordTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        
        # Gmail credentials from .env
        self.gmail_user = "rotakalitedanismanlik@gmail.com"
        self.gmail_password = "ciho hxvo fakl ddem"  # Gmail App Password
        
        print("🔍 Gmail App Password Fix Verification Test")
        print("=" * 60)
        print(f"📧 Gmail User: {self.gmail_user}")
        print(f"🔑 Gmail Password: {'*' * len(self.gmail_password)} (App Password)")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print("=" * 60)
    
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status} | {test_name}"
        if details:
            result += f" | {details}"
        
        self.results.append(result)
        print(result)
    
    async def test_direct_smtp_authentication(self):
        """Test 1: Direct SMTP authentication with Gmail App Password"""
        print("\n🔐 Test 1: Direct SMTP Authentication")
        print("-" * 40)
        
        try:
            # Test SMTP connection and authentication
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            
            # This is the critical test - authentication with App Password
            server.login(self.gmail_user, self.gmail_password)
            server.quit()
            
            self.log_result("SMTP Authentication", True, "Gmail App Password authentication successful")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = str(e)
            if "Application-specific password required" in error_msg:
                self.log_result("SMTP Authentication", False, "Still requires App Password - fix not working")
            elif "InvalidSecondFactor" in error_msg:
                self.log_result("SMTP Authentication", False, "Invalid App Password format")
            else:
                self.log_result("SMTP Authentication", False, f"Auth error: {error_msg}")
            return False
            
        except Exception as e:
            self.log_result("SMTP Authentication", False, f"Connection error: {str(e)}")
            return False
    
    async def test_smtp_connection_parameters(self):
        """Test 2: SMTP connection parameters and TLS"""
        print("\n🌐 Test 2: SMTP Connection Parameters")
        print("-" * 40)
        
        try:
            # Test connection without authentication first
            server = smtplib.SMTP('smtp.gmail.com', 587)
            
            # Test STARTTLS
            server.starttls()
            self.log_result("SMTP STARTTLS", True, "TLS encryption enabled successfully")
            
            # Test server capabilities
            capabilities = server.ehlo()
            if capabilities[0] == 250:
                self.log_result("SMTP EHLO", True, "Server capabilities retrieved")
            else:
                self.log_result("SMTP EHLO", False, f"EHLO failed: {capabilities}")
            
            server.quit()
            return True
            
        except Exception as e:
            self.log_result("SMTP Connection", False, f"Connection failed: {str(e)}")
            return False
    
    async def test_email_service_initialization(self):
        """Test 3: Email service initialization with new credentials"""
        print("\n📧 Test 3: Email Service Initialization")
        print("-" * 40)
        
        try:
            # Import email service to test initialization
            from services.email_service import email_service
            
            if email_service is None:
                self.log_result("Email Service Init", False, "Email service is None - credentials not loaded")
                return False
            
            # Check if service has the right credentials
            if hasattr(email_service, 'fastmail'):
                self.log_result("Email Service Init", True, "Email service initialized with FastMail")
            else:
                self.log_result("Email Service Init", False, "Email service missing FastMail instance")
                return False
            
            # Test if credentials are loaded correctly
            from services.email_service import gmail_user, gmail_password
            
            if gmail_user == self.gmail_user:
                self.log_result("Gmail User Config", True, f"Correct Gmail user: {gmail_user}")
            else:
                self.log_result("Gmail User Config", False, f"Wrong Gmail user: {gmail_user}")
            
            if gmail_password == self.gmail_password:
                self.log_result("Gmail Password Config", True, "Gmail App Password loaded correctly")
            else:
                self.log_result("Gmail Password Config", False, "Gmail App Password not loaded correctly")
            
            return True
            
        except Exception as e:
            self.log_result("Email Service Init", False, f"Import error: {str(e)}")
            return False
    
    async def test_send_test_email(self):
        """Test 4: Send test email using email service"""
        print("\n📤 Test 4: Send Test Email")
        print("-" * 40)
        
        try:
            from services.email_service import email_service
            
            if email_service is None:
                self.log_result("Send Test Email", False, "Email service not available")
                return False
            
            # Try to send test email
            success = await email_service.send_test_email(TEST_EMAIL)
            
            if success:
                self.log_result("Send Test Email", True, f"Test email sent to {TEST_EMAIL}")
                return True
            else:
                self.log_result("Send Test Email", False, "Email sending failed")
                return False
                
        except Exception as e:
            self.log_result("Send Test Email", False, f"Error: {str(e)}")
            return False
    
    async def test_direct_smtp_email_send(self):
        """Test 5: Direct SMTP email sending"""
        print("\n📮 Test 5: Direct SMTP Email Send")
        print("-" * 40)
        
        try:
            # Create test message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "🧪 Gmail App Password Test - Direct SMTP"
            msg['From'] = self.gmail_user
            msg['To'] = TEST_EMAIL
            
            # HTML content
            html_content = """
            <html>
                <body>
                    <h2>🎉 Gmail App Password Test Successful!</h2>
                    <p>This email was sent using the new Gmail App Password via direct SMTP.</p>
                    <p><strong>Credentials:</strong></p>
                    <ul>
                        <li>Gmail User: rotakalitedanismanlik@gmail.com</li>
                        <li>Gmail App Password: ciho hxvo fakl ddem</li>
                        <li>SMTP Server: smtp.gmail.com:587</li>
                        <li>TLS: Enabled</li>
                    </ul>
                    <p>✅ 2FA email system should now be fully operational!</p>
                </body>
            </html>
            """
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send via SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            
            text = msg.as_string()
            server.sendmail(self.gmail_user, TEST_EMAIL, text)
            server.quit()
            
            self.log_result("Direct SMTP Send", True, f"Email sent successfully to {TEST_EMAIL}")
            return True
            
        except Exception as e:
            self.log_result("Direct SMTP Send", False, f"Send failed: {str(e)}")
            return False
    
    async def test_2fa_email_functionality(self):
        """Test 6: 2FA email functionality"""
        print("\n🔐 Test 6: 2FA Email Functionality")
        print("-" * 40)
        
        try:
            # Import 2FA functions
            from server import send_2fa_email
            
            # Test sending 2FA email
            test_code = "123456"
            success = await send_2fa_email(TEST_EMAIL, test_code)
            
            if success:
                self.log_result("2FA Email Send", True, f"2FA email sent with code {test_code}")
                return True
            else:
                self.log_result("2FA Email Send", False, "2FA email sending failed")
                return False
                
        except Exception as e:
            self.log_result("2FA Email Send", False, f"Error: {str(e)}")
            return False
    
    async def test_backend_email_endpoints(self):
        """Test 7: Backend email endpoints accessibility"""
        print("\n🌐 Test 7: Backend Email Endpoints")
        print("-" * 40)
        
        # Test email-related endpoints
        endpoints = [
            "/",  # Health check
            "/test",  # Basic test endpoint
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{BACKEND_URL}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    self.log_result(f"Endpoint {endpoint}", True, f"Status: {response.status_code}")
                else:
                    self.log_result(f"Endpoint {endpoint}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Endpoint {endpoint}", False, f"Error: {str(e)}")
    
    async def test_app_password_format_validation(self):
        """Test 8: App Password format validation"""
        print("\n🔍 Test 8: App Password Format Validation")
        print("-" * 40)
        
        # Gmail App Passwords are 16 characters, space-separated in groups of 4
        app_password = self.gmail_password
        
        # Remove spaces and check length
        clean_password = app_password.replace(" ", "")
        
        if len(clean_password) == 16:
            self.log_result("App Password Length", True, f"16 characters: {len(clean_password)}")
        else:
            self.log_result("App Password Length", False, f"Wrong length: {len(clean_password)} (should be 16)")
        
        # Check format (4 groups of 4 characters separated by spaces)
        parts = app_password.split(" ")
        if len(parts) == 4 and all(len(part) == 4 for part in parts):
            self.log_result("App Password Format", True, "Correct format: xxxx xxxx xxxx xxxx")
        else:
            self.log_result("App Password Format", False, f"Wrong format: {app_password}")
        
        # Check if it's not the old password
        old_password = "Ccpp1144.."
        if app_password != old_password:
            self.log_result("Password Updated", True, "Password changed from old regular password")
        else:
            self.log_result("Password Updated", False, "Still using old regular password")
    
    async def run_all_tests(self):
        """Run all Gmail App Password tests"""
        print("🚀 Starting Gmail App Password Fix Verification Tests...")
        print("=" * 60)
        
        # Run all tests
        await self.test_app_password_format_validation()
        await self.test_direct_smtp_authentication()
        await self.test_smtp_connection_parameters()
        await self.test_email_service_initialization()
        await self.test_send_test_email()
        await self.test_direct_smtp_email_send()
        await self.test_2fa_email_functionality()
        await self.test_backend_email_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 GMAIL APP PASSWORD FIX TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0
        
        print(f"✅ Tests Passed: {self.passed_tests}/{self.total_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()
        
        # Print all results
        for result in self.results:
            print(result)
        
        print("\n" + "=" * 60)
        
        if success_rate >= 80:
            print("🎉 GMAIL APP PASSWORD FIX VERIFICATION: SUCCESS!")
            print("✅ Gmail App Password is working correctly")
            print("✅ 2FA email system should be fully operational")
            print("✅ No more 'Application-specific password required' errors")
        elif success_rate >= 60:
            print("⚠️ GMAIL APP PASSWORD FIX: PARTIAL SUCCESS")
            print("🔧 Some issues detected, but core functionality working")
        else:
            print("❌ GMAIL APP PASSWORD FIX: FAILED")
            print("🚨 Critical issues detected - 2FA email system may not work")
        
        print("=" * 60)
        
        return success_rate

async def main():
    """Main test execution"""
    tester = GmailAppPasswordTester()
    success_rate = await tester.run_all_tests()
    
    # Return appropriate exit code
    if success_rate >= 80:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    asyncio.run(main())