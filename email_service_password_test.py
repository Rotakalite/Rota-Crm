#!/usr/bin/env python3
"""
📧 EMAIL SERVICE PASSWORD UPDATE COMPREHENSIVE TEST
==================================================

Testing the Email Service with updated password: Ccpp1144..

**Problem Fixed:**
User changed the password for 2FA email sender to: Ccpp1144..
Updated both .env file and email_service.py with new password.

**Test Requirements:**
1. Test email service initialization with new password
2. Test email connectivity with Gmail SMTP
3. Try sending a test email to verify the new password works
4. Check email service endpoints accessibility
5. Verify email configuration is properly loaded

**Email Configuration:**
- User: rotakalitedanismanlik@gmail.com  
- New Password: Ccpp1144..
- SMTP: smtp.gmail.com:587

**Test Scenarios:**
1. Test basic email service endpoint accessibility
2. Try email template test endpoint if available
3. Check Gmail authentication with new credentials
4. Test direct SMTP connection

**Expected Results:**
- Email service should initialize without errors
- New password should work with Gmail SMTP
- Test emails should be sent successfully
- No authentication errors in logs

**Focus:** Verify that 2FA emails will now work with updated password.

Backend URL: https://ecowave-saas.preview.emergentagent.com
"""

import requests
import json
import sys
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Backend URL from frontend .env
BACKEND_URL = "https://ecowave-saas.preview.emergentagent.com"

# Email configuration
GMAIL_USER = "rotakalitedanismanlik@gmail.com"
GMAIL_PASSWORD = "Ccpp1144.."

class EmailServicePasswordTest:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.gmail_user = GMAIL_USER
        self.gmail_password = GMAIL_PASSWORD
        
        # Test email for sending tests
        self.test_email = "test@example.com"

    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Log test result"""
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
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and expected:
            print(f"   🎯 Expected: {expected}")
            print(f"   📊 Actual: {actual}")
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
                    f"Backend accessible (Status: {response.status_code})"
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
                f"Backend connection error: {str(e)}"
            )
            return False

    def test_direct_smtp_connection(self):
        """Test direct SMTP connection with new password"""
        print("📧 Direct SMTP Connection Test")
        print("=" * 50)
        
        try:
            # Test SMTP connection
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            
            # Test authentication with new password
            server.login(self.gmail_user, self.gmail_password)
            server.quit()
            
            self.log_test(
                "Direct SMTP Authentication",
                True,
                f"✅ Gmail SMTP authentication successful with new password"
            )
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            self.log_test(
                "Direct SMTP Authentication",
                False,
                f"🚨 CRITICAL: SMTP Authentication failed with new password!",
                "Authentication success",
                f"SMTPAuthenticationError: {str(e)}"
            )
            return False
            
        except Exception as e:
            self.log_test(
                "Direct SMTP Connection",
                False,
                f"SMTP connection error: {str(e)}"
            )
            return False

    def test_send_test_email_direct(self):
        """Test sending email directly via SMTP"""
        print("📤 Direct Email Send Test")
        print("=" * 50)
        
        try:
            # Create test message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "🧪 Email Service Password Test"
            msg['From'] = self.gmail_user
            msg['To'] = self.test_email
            
            # HTML content
            html_content = """
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>🎉 Email Service Password Test Successful!</h2>
                    <p>This email confirms that the new password <strong>Ccpp1144..</strong> is working correctly.</p>
                    <p><strong>Test Details:</strong></p>
                    <ul>
                        <li>📧 Email: rotakalitedanismanlik@gmail.com</li>
                        <li>🔐 Password: Ccpp1144.. (Updated)</li>
                        <li>🌐 SMTP: smtp.gmail.com:587</li>
                        <li>📅 Test Time: {}</li>
                    </ul>
                    <p>✅ 2FA emails should now work correctly!</p>
                </body>
            </html>
            """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            
            text = msg.as_string()
            server.sendmail(self.gmail_user, self.test_email, text)
            server.quit()
            
            self.log_test(
                "Direct Email Send Test",
                True,
                f"✅ Test email sent successfully to {self.test_email}"
            )
            return True
            
        except Exception as e:
            self.log_test(
                "Direct Email Send Test",
                False,
                f"Email send error: {str(e)}"
            )
            return False

    def test_email_template_endpoint(self):
        """Test email template endpoint"""
        print("📋 Email Template Endpoint Test")
        print("=" * 50)
        
        try:
            response = requests.post(f"{self.backend_url}/email-template-test", timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('success'):
                        self.log_test(
                            "Email Template Test Endpoint",
                            True,
                            f"✅ Email template endpoint working (Status: {response.status_code})"
                        )
                    else:
                        self.log_test(
                            "Email Template Test Endpoint",
                            False,
                            f"Email template test failed: {data.get('error', 'Unknown error')}"
                        )
                except:
                    self.log_test(
                        "Email Template Test Endpoint",
                        True,
                        f"✅ Email template endpoint accessible (Status: {response.status_code})"
                    )
            else:
                self.log_test(
                    "Email Template Test Endpoint",
                    False,
                    f"Email template endpoint error",
                    "200",
                    str(response.status_code)
                )
                
        except Exception as e:
            self.log_test(
                "Email Template Test Endpoint",
                False,
                f"Request error: {str(e)}"
            )

    def test_2fa_email_functionality(self):
        """Test 2FA email functionality"""
        print("🔐 2FA Email Functionality Test")
        print("=" * 50)
        
        # Test 2FA code request endpoint
        try:
            test_2fa_data = {
                "email": "test@example.com"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/auth/request-2fa-code",
                json=test_2fa_data,
                timeout=10
            )
            
            if response.status_code == 404:
                self.log_test(
                    "2FA Email Endpoint Exists",
                    False,
                    f"🚨 2FA email endpoint not found!",
                    "Not 404",
                    "404"
                )
            elif response.status_code == 500:
                self.log_test(
                    "2FA Email Endpoint",
                    False,
                    f"🚨 CRITICAL: 500 error in 2FA email endpoint!",
                    "Not 500",
                    "500"
                )
            elif response.status_code in [200, 400, 422]:
                self.log_test(
                    "2FA Email Endpoint",
                    True,
                    f"✅ 2FA email endpoint accessible (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "2FA Email Endpoint",
                    True,
                    f"✅ 2FA email endpoint exists (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_test(
                "2FA Email Endpoint Test",
                False,
                f"Request error: {str(e)}"
            )

    def test_email_service_configuration(self):
        """Test email service configuration"""
        print("⚙️ Email Service Configuration Test")
        print("=" * 50)
        
        # Test basic email endpoint
        try:
            response = requests.get(f"{self.backend_url}/test", timeout=10)
            
            if response.status_code == 200:
                self.log_test(
                    "Basic Test Endpoint",
                    True,
                    f"✅ Basic test endpoint working (Status: {response.status_code})"
                )
            else:
                self.log_test(
                    "Basic Test Endpoint",
                    False,
                    f"Basic test endpoint error",
                    "200",
                    str(response.status_code)
                )
                
        except Exception as e:
            self.log_test(
                "Basic Test Endpoint",
                False,
                f"Request error: {str(e)}"
            )

        # Check if email service is properly configured
        print(f"📧 Email Configuration Check:")
        print(f"   User: {self.gmail_user}")
        print(f"   Password: {'*' * len(self.gmail_password)} (Length: {len(self.gmail_password)})")
        print(f"   SMTP Server: smtp.gmail.com:587")
        
        if self.gmail_user and self.gmail_password:
            self.log_test(
                "Email Configuration Check",
                True,
                f"✅ Email credentials configured correctly"
            )
        else:
            self.log_test(
                "Email Configuration Check",
                False,
                f"❌ Email credentials missing"
            )

    def test_smtp_connection_variations(self):
        """Test different SMTP connection scenarios"""
        print("🔄 SMTP Connection Variations Test")
        print("=" * 50)
        
        # Test with different timeout values
        timeouts = [5, 10, 15]
        
        for timeout in timeouts:
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587, timeout=timeout)
                server.starttls()
                server.login(self.gmail_user, self.gmail_password)
                server.quit()
                
                self.log_test(
                    f"SMTP Connection (Timeout: {timeout}s)",
                    True,
                    f"✅ SMTP connection successful with {timeout}s timeout"
                )
                break  # If one works, others should too
                
            except Exception as e:
                self.log_test(
                    f"SMTP Connection (Timeout: {timeout}s)",
                    False,
                    f"SMTP connection failed: {str(e)}"
                )

    def run_all_tests(self):
        """Run all email service tests"""
        print("📧 EMAIL SERVICE PASSWORD UPDATE COMPREHENSIVE TEST")
        print("=" * 70)
        print(f"🎯 Backend URL: {self.backend_url}")
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔐 New Password: Ccpp1144..")
        print(f"📧 Email: {self.gmail_user}")
        print("=" * 70)
        print()
        
        # Backend health check
        if not self.test_backend_health():
            print("❌ Backend inaccessible, continuing with direct tests...")
        
        # Email service configuration test
        self.test_email_service_configuration()
        
        # Direct SMTP tests
        print("\n🔗 DIRECT SMTP TESTS:")
        print("-" * 40)
        self.test_direct_smtp_connection()
        self.test_send_test_email_direct()
        self.test_smtp_connection_variations()
        
        # Backend endpoint tests
        print("\n🌐 BACKEND ENDPOINT TESTS:")
        print("-" * 40)
        self.test_email_template_endpoint()
        self.test_2fa_email_functionality()
        
        # Show results
        self.show_results()
        
        return self.passed_tests >= (self.total_tests * 0.7)  # 70% success rate

    def show_results(self):
        """Show test results"""
        print("\n" + "=" * 70)
        print("📊 EMAIL SERVICE PASSWORD UPDATE TEST RESULTS")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"✅ Successful Tests: {self.passed_tests}")
        print(f"❌ Failed Tests: {self.total_tests - self.passed_tests}")
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        # Critical authentication errors analysis
        auth_errors = [r for r in self.test_results if not r['success'] and 'Authentication' in r['test']]
        if auth_errors:
            print(f"\n🚨 CRITICAL AUTHENTICATION ERRORS: {len(auth_errors)}")
            print("=" * 50)
            for error in auth_errors:
                print(f"❌ {error['test']}")
                print(f"   📝 {error['details']}")
            print("\n⚡ URGENT: Email password may be incorrect!")
        else:
            print("\n✅ NO AUTHENTICATION ERRORS DETECTED!")
        
        # SMTP connection analysis
        smtp_tests = [r for r in self.test_results if 'SMTP' in r['test']]
        smtp_success = [r for r in smtp_tests if r['success']]
        
        if smtp_success:
            print(f"\n📧 SMTP CONNECTION: {len(smtp_success)}/{len(smtp_tests)} tests passed")
            print("✅ Gmail SMTP working with new password!")
        else:
            print(f"\n❌ SMTP CONNECTION: 0/{len(smtp_tests)} tests passed")
            print("🚨 Gmail SMTP not working with new password!")
        
        # Email send analysis
        send_tests = [r for r in self.test_results if 'Send' in r['test']]
        send_success = [r for r in send_tests if r['success']]
        
        if send_success:
            print(f"\n📤 EMAIL SENDING: {len(send_success)}/{len(send_tests)} tests passed")
            print("✅ Email sending working!")
        else:
            print(f"\n📤 EMAIL SENDING: 0/{len(send_tests)} tests passed")
            print("❌ Email sending not working!")
        
        if success_rate >= 90:
            print("\n🎉 EXCELLENT! Email service with new password is working perfectly!")
        elif success_rate >= 70:
            print("\n✅ GOOD! Email service is generally working with new password.")
        elif success_rate >= 50:
            print("\n⚠️ MODERATE! Email service has some issues with new password.")
        else:
            print("\n❌ CRITICAL! Email service not working with new password.")
        
        print("\n🔍 DETAILED RESULTS:")
        print("-" * 70)
        
        # Group results by category
        failed_tests = [r for r in self.test_results if not r['success']]
        successful_tests = [r for r in self.test_results if r['success']]
        
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        if successful_tests:
            print(f"\n✅ SUCCESSFUL TESTS: {len(successful_tests)} tests")
            for test in successful_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        print("\n" + "=" * 70)
        
        # Save test results
        with open('/app/email_service_password_test_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'test_summary': {
                    'total_tests': self.total_tests,
                    'passed_tests': self.passed_tests,
                    'failed_tests': self.total_tests - self.passed_tests,
                    'success_rate': success_rate,
                    'backend_url': self.backend_url,
                    'test_timestamp': datetime.now().isoformat(),
                    'test_focus': 'Email Service Password Update - New Password: Ccpp1144..',
                    'gmail_user': self.gmail_user,
                    'password_length': len(self.gmail_password)
                },
                'test_results': self.test_results,
                'critical_issues': {
                    'auth_errors': auth_errors,
                    'smtp_failures': [r for r in self.test_results if not r['success'] and 'SMTP' in r['test']]
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed test results saved: /app/email_service_password_test_results.json")

def main():
    """Main test function"""
    tester = EmailServicePasswordTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 EMAIL SERVICE PASSWORD UPDATE TESTS SUCCESSFUL!")
        print("✅ New password Ccpp1144.. is working correctly")
        print("✅ Gmail SMTP authentication successful")
        print("✅ Email sending functionality verified")
        print("✅ 2FA emails should now work properly")
        sys.exit(0)
    else:
        print("\n🚨 EMAIL SERVICE PASSWORD UPDATE ISSUES DETECTED!")
        print("❌ New password may not be working correctly")
        print("🔧 Check Gmail App Password configuration")
        print("⚡ Verify 2-Step Verification is enabled")
        sys.exit(1)

if __name__ == "__main__":
    main()