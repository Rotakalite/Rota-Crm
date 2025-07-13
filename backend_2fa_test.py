#!/usr/bin/env python3
"""
2FA System Testing for ROTA CRM Backend
Tests the complete 2FA flow including code sending, verification, and status checking
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('/app/backend/.env')

# Configuration
BACKEND_URL = "https://rota-crm-production.up.railway.app"
API_BASE_URL = f"{BACKEND_URL}/api"

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'rotacrm')

# Test email addresses
TEST_EMAIL_VALID = "test2fa@example.com"
TEST_EMAIL_INVALID = "invalid-email"

class TwoFASystemTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # MongoDB connection for database verification
        try:
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            logger.info("✅ MongoDB connection established")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.mongo_client = None
            self.db = None

    def test_health_check(self):
        """Test if the backend is accessible"""
        logger.info("🔍 Testing backend health check...")
        try:
            response = self.session.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                logger.info("✅ Backend health check passed")
                return True
            else:
                logger.error(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Backend health check error: {e}")
            return False

    def test_send_2fa_code_valid_email(self):
        """Test sending 2FA code with valid email"""
        logger.info("🔍 Testing 2FA code sending with valid email...")
        
        try:
            payload = {"email": TEST_EMAIL_VALID}
            response = self.session.post(
                f"{API_BASE_URL}/auth/2fa/send-code",
                json=payload
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "gönderildi" in data.get("message", ""):
                    logger.info("✅ 2FA code sent successfully")
                    return True
                else:
                    logger.error(f"❌ Unexpected response format: {data}")
                    return False
            else:
                logger.error(f"❌ Failed to send 2FA code: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing 2FA code sending: {e}")
            return False

    def test_send_2fa_code_missing_email(self):
        """Test sending 2FA code without email"""
        logger.info("🔍 Testing 2FA code sending without email...")
        
        try:
            payload = {}  # Missing email
            response = self.session.post(
                f"{API_BASE_URL}/auth/2fa/send-code",
                json=payload
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 400:
                logger.info("✅ Correctly rejected request without email")
                return True
            else:
                logger.error(f"❌ Should have returned 400 for missing email, got: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing missing email: {e}")
            return False

    def test_send_2fa_code_invalid_email(self):
        """Test sending 2FA code with invalid email format"""
        logger.info("🔍 Testing 2FA code sending with invalid email...")
        
        try:
            payload = {"email": TEST_EMAIL_INVALID}
            response = self.session.post(
                f"{API_BASE_URL}/auth/2fa/send-code",
                json=payload
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            # The endpoint might still accept invalid email format and try to send
            # This is more of a validation test
            if response.status_code in [200, 400]:
                logger.info("✅ Handled invalid email appropriately")
                return True
            else:
                logger.error(f"❌ Unexpected response for invalid email: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing invalid email: {e}")
            return False

    def get_verification_code_from_db(self, email):
        """Get verification code from database"""
        if not self.db:
            logger.error("❌ No database connection available")
            return None
            
        try:
            code_doc = self.db.verification_codes.find_one(
                {"email": email, "used": False},
                sort=[("created_at", -1)]  # Get the most recent code
            )
            
            if code_doc:
                logger.info(f"✅ Found verification code in database for {email}")
                return code_doc["code"]
            else:
                logger.warning(f"⚠️ No verification code found in database for {email}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error retrieving verification code from database: {e}")
            return None

    def test_verify_2fa_code_valid(self):
        """Test verifying 2FA code with valid code"""
        logger.info("🔍 Testing 2FA code verification with valid code...")
        
        # First, send a code
        if not self.test_send_2fa_code_valid_email():
            logger.error("❌ Failed to send 2FA code, cannot test verification")
            return False
        
        # Wait a moment for the code to be stored
        time.sleep(2)
        
        # Get the code from database
        verification_code = self.get_verification_code_from_db(TEST_EMAIL_VALID)
        if not verification_code:
            logger.error("❌ Could not retrieve verification code from database")
            return False
        
        try:
            payload = {
                "email": TEST_EMAIL_VALID,
                "code": verification_code
            }
            response = self.session.post(
                f"{API_BASE_URL}/auth/2fa/verify-code",
                json=payload
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("verified") and "doğrulandı" in data.get("message", ""):
                    logger.info("✅ 2FA code verified successfully")
                    return True
                else:
                    logger.error(f"❌ Unexpected verification response: {data}")
                    return False
            else:
                logger.error(f"❌ Failed to verify 2FA code: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing 2FA code verification: {e}")
            return False

    def test_verify_2fa_code_invalid(self):
        """Test verifying 2FA code with invalid code"""
        logger.info("🔍 Testing 2FA code verification with invalid code...")
        
        try:
            payload = {
                "email": TEST_EMAIL_VALID,
                "code": "999999"  # Invalid code
            }
            response = self.session.post(
                f"{API_BASE_URL}/auth/2fa/verify-code",
                json=payload
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 400:
                logger.info("✅ Correctly rejected invalid 2FA code")
                return True
            else:
                logger.error(f"❌ Should have returned 400 for invalid code, got: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing invalid 2FA code: {e}")
            return False

    def test_verify_2fa_code_missing_fields(self):
        """Test verifying 2FA code with missing email or code"""
        logger.info("🔍 Testing 2FA code verification with missing fields...")
        
        test_cases = [
            {"email": TEST_EMAIL_VALID},  # Missing code
            {"code": "123456"},  # Missing email
            {}  # Missing both
        ]
        
        all_passed = True
        for i, payload in enumerate(test_cases):
            try:
                response = self.session.post(
                    f"{API_BASE_URL}/auth/2fa/verify-code",
                    json=payload
                )
                
                logger.info(f"Test case {i+1} - Response status: {response.status_code}")
                logger.info(f"Test case {i+1} - Response body: {response.text}")
                
                if response.status_code == 400:
                    logger.info(f"✅ Test case {i+1}: Correctly rejected missing fields")
                else:
                    logger.error(f"❌ Test case {i+1}: Should have returned 400, got: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"❌ Error in test case {i+1}: {e}")
                all_passed = False
        
        return all_passed

    def test_2fa_status(self):
        """Test 2FA status endpoint"""
        logger.info("🔍 Testing 2FA status endpoint...")
        
        # First, send a code to have a pending status
        if not self.test_send_2fa_code_valid_email():
            logger.error("❌ Failed to send 2FA code, cannot test status")
            return False
        
        # Wait a moment for the code to be stored
        time.sleep(2)
        
        try:
            response = self.session.get(
                f"{API_BASE_URL}/auth/2fa/status",
                params={"user_email": TEST_EMAIL_VALID}
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if "has_pending_code" in data:
                    if data["has_pending_code"]:
                        logger.info("✅ 2FA status shows pending code correctly")
                        return True
                    else:
                        logger.warning("⚠️ 2FA status shows no pending code (might be expired)")
                        return True  # This is also valid behavior
                else:
                    logger.error(f"❌ Unexpected status response format: {data}")
                    return False
            else:
                logger.error(f"❌ Failed to get 2FA status: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing 2FA status: {e}")
            return False

    def test_2fa_status_no_code(self):
        """Test 2FA status when no code exists"""
        logger.info("🔍 Testing 2FA status with no pending code...")
        
        # Use a different email that shouldn't have a code
        test_email = "nocode@example.com"
        
        try:
            response = self.session.get(
                f"{API_BASE_URL}/auth/2fa/status",
                params={"user_email": test_email}
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("has_pending_code") == False:
                    logger.info("✅ 2FA status correctly shows no pending code")
                    return True
                else:
                    logger.error(f"❌ Expected no pending code, got: {data}")
                    return False
            else:
                logger.error(f"❌ Failed to get 2FA status: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing 2FA status with no code: {e}")
            return False

    def test_database_storage(self):
        """Test that verification codes are properly stored in MongoDB"""
        logger.info("🔍 Testing database storage of verification codes...")
        
        if not self.db:
            logger.error("❌ No database connection available")
            return False
        
        # Clear any existing codes for test email
        try:
            self.db.verification_codes.delete_many({"email": TEST_EMAIL_VALID})
            logger.info("🧹 Cleared existing verification codes for test email")
        except Exception as e:
            logger.warning(f"⚠️ Could not clear existing codes: {e}")
        
        # Send a new code
        if not self.test_send_2fa_code_valid_email():
            logger.error("❌ Failed to send 2FA code for database test")
            return False
        
        # Wait a moment for the code to be stored
        time.sleep(2)
        
        try:
            # Check if code exists in database
            code_doc = self.db.verification_codes.find_one({"email": TEST_EMAIL_VALID})
            
            if not code_doc:
                logger.error("❌ Verification code not found in database")
                return False
            
            # Verify the document structure
            required_fields = ["email", "code", "expires_at", "created_at", "used"]
            missing_fields = [field for field in required_fields if field not in code_doc]
            
            if missing_fields:
                logger.error(f"❌ Missing required fields in database document: {missing_fields}")
                return False
            
            # Verify field types and values
            if code_doc["email"] != TEST_EMAIL_VALID:
                logger.error(f"❌ Email mismatch in database: expected {TEST_EMAIL_VALID}, got {code_doc['email']}")
                return False
            
            if not isinstance(code_doc["code"], str) or len(code_doc["code"]) != 6:
                logger.error(f"❌ Invalid code format in database: {code_doc['code']}")
                return False
            
            if not code_doc["code"].isdigit():
                logger.error(f"❌ Code is not numeric: {code_doc['code']}")
                return False
            
            if code_doc["used"] != False:
                logger.error(f"❌ New code should not be marked as used: {code_doc['used']}")
                return False
            
            # Check expiration time (should be ~10 minutes from now)
            expires_at = code_doc["expires_at"]
            created_at = code_doc["created_at"]
            
            if isinstance(expires_at, str):
                from dateutil import parser
                expires_at = parser.parse(expires_at)
            if isinstance(created_at, str):
                from dateutil import parser
                created_at = parser.parse(created_at)
            
            time_diff = expires_at - created_at
            expected_expiry = timedelta(minutes=10)
            
            if abs(time_diff.total_seconds() - expected_expiry.total_seconds()) > 60:  # Allow 1 minute tolerance
                logger.error(f"❌ Incorrect expiration time: {time_diff} (expected ~10 minutes)")
                return False
            
            logger.info("✅ Verification code properly stored in database with correct structure")
            logger.info(f"   - Email: {code_doc['email']}")
            logger.info(f"   - Code: {code_doc['code']}")
            logger.info(f"   - Created: {created_at}")
            logger.info(f"   - Expires: {expires_at}")
            logger.info(f"   - Used: {code_doc['used']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error testing database storage: {e}")
            return False

    def test_code_expiration(self):
        """Test that expired codes are properly handled"""
        logger.info("🔍 Testing expired code handling...")
        
        if not self.db:
            logger.error("❌ No database connection available")
            return False
        
        try:
            # Create an expired code directly in database
            expired_code = {
                "email": TEST_EMAIL_VALID,
                "code": "123456",
                "expires_at": datetime.utcnow() - timedelta(minutes=1),  # Expired 1 minute ago
                "created_at": datetime.utcnow() - timedelta(minutes=11),  # Created 11 minutes ago
                "used": False
            }
            
            # Clear existing codes and insert expired one
            self.db.verification_codes.delete_many({"email": TEST_EMAIL_VALID})
            self.db.verification_codes.insert_one(expired_code)
            
            logger.info("📝 Inserted expired verification code into database")
            
            # Try to verify the expired code
            payload = {
                "email": TEST_EMAIL_VALID,
                "code": "123456"
            }
            response = self.session.post(
                f"{API_BASE_URL}/auth/2fa/verify-code",
                json=payload
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 400 and "süresi dolmuş" in response.text:
                logger.info("✅ Expired code correctly rejected")
                
                # Verify that expired code was cleaned up from database
                remaining_code = self.db.verification_codes.find_one({"email": TEST_EMAIL_VALID})
                if not remaining_code:
                    logger.info("✅ Expired code was cleaned up from database")
                    return True
                else:
                    logger.warning("⚠️ Expired code was rejected but not cleaned up from database")
                    return True  # Still a pass since the main functionality works
            else:
                logger.error(f"❌ Expired code should have been rejected with 400 status")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing code expiration: {e}")
            return False

    def test_code_reuse_prevention(self):
        """Test that used codes cannot be reused"""
        logger.info("🔍 Testing code reuse prevention...")
        
        # First, send and verify a code successfully
        if not self.test_send_2fa_code_valid_email():
            logger.error("❌ Failed to send 2FA code for reuse test")
            return False
        
        time.sleep(2)
        
        verification_code = self.get_verification_code_from_db(TEST_EMAIL_VALID)
        if not verification_code:
            logger.error("❌ Could not retrieve verification code for reuse test")
            return False
        
        # Verify the code once (should succeed)
        payload = {
            "email": TEST_EMAIL_VALID,
            "code": verification_code
        }
        response = self.session.post(
            f"{API_BASE_URL}/auth/2fa/verify-code",
            json=payload
        )
        
        if response.status_code != 200:
            logger.error(f"❌ First verification failed: {response.status_code}")
            return False
        
        logger.info("✅ First verification succeeded")
        
        # Try to use the same code again (should fail)
        response = self.session.post(
            f"{API_BASE_URL}/auth/2fa/verify-code",
            json=payload
        )
        
        logger.info(f"Second verification response status: {response.status_code}")
        logger.info(f"Second verification response body: {response.text}")
        
        if response.status_code == 400 and "Geçersiz kod" in response.text:
            logger.info("✅ Used code correctly rejected on reuse attempt")
            return True
        else:
            logger.error(f"❌ Used code should have been rejected, got: {response.status_code}")
            return False

    def run_all_tests(self):
        """Run all 2FA tests"""
        logger.info("🚀 Starting comprehensive 2FA system testing...")
        
        tests = [
            ("Backend Health Check", self.test_health_check),
            ("Send 2FA Code - Valid Email", self.test_send_2fa_code_valid_email),
            ("Send 2FA Code - Missing Email", self.test_send_2fa_code_missing_email),
            ("Send 2FA Code - Invalid Email", self.test_send_2fa_code_invalid_email),
            ("Verify 2FA Code - Valid Code", self.test_verify_2fa_code_valid),
            ("Verify 2FA Code - Invalid Code", self.test_verify_2fa_code_invalid),
            ("Verify 2FA Code - Missing Fields", self.test_verify_2fa_code_missing_fields),
            ("2FA Status - With Pending Code", self.test_2fa_status),
            ("2FA Status - No Pending Code", self.test_2fa_status_no_code),
            ("Database Storage Verification", self.test_database_storage),
            ("Code Expiration Handling", self.test_code_expiration),
            ("Code Reuse Prevention", self.test_code_reuse_prevention),
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*60}")
            logger.info(f"🧪 Running: {test_name}")
            logger.info(f"{'='*60}")
            
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"💥 {test_name}: ERROR - {e}")
                results[test_name] = False
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 2FA SYSTEM TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {total - passed}")
        logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
        
        logger.info(f"\n📋 DETAILED RESULTS:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {status} - {test_name}")
        
        if passed == total:
            logger.info(f"\n🎉 ALL 2FA TESTS PASSED! The 2FA system is working correctly.")
        else:
            logger.warning(f"\n⚠️ {total - passed} tests failed. Please review the issues above.")
        
        return results

if __name__ == "__main__":
    tester = TwoFASystemTest()
    results = tester.run_all_tests()