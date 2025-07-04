import unittest
import logging
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the backend directory to the path so we can import modules
backend_dir = Path("/app/backend")
sys.path.append(str(backend_dir))

# Import necessary modules
try:
    from server import send_2fa_code, verify_2fa_code, get_2fa_status
    from server import TwoFACodeRequest, TwoFAVerifyRequest, User, UserRole
    from server import db
    logger.info("✅ Successfully imported 2FA endpoints")
except Exception as e:
    logger.error(f"❌ Failed to import 2FA endpoints: {e}")
    raise

# Mock user for testing
mock_user = User(
    id="test_user_id",
    clerk_user_id="test_clerk_user_id",
    email="test@example.com",
    name="Test User",
    role=UserRole.CLIENT,
    client_id="test_client_id",
    created_at=datetime.utcnow()
)

# Mock request for testing
class MockRequest:
    def __init__(self):
        self.state = {}

class Test2FAEndpoints(unittest.TestCase):
    """Test class for 2FA endpoints"""
    
    async def test_send_2fa_code(self):
        """Test send_2fa_code function"""
        logger.info("\n=== Testing send_2fa_code function ===")
        
        # Create mock request
        request = MockRequest()
        
        # Create code request
        code_request = TwoFACodeRequest(email="test@example.com")
        
        try:
            # Call the function
            result = await send_2fa_code(request, code_request, mock_user)
            
            # Check result
            self.assertIsNotNone(result)
            self.assertIn("message", result)
            self.assertIn("email", result)
            self.assertIn("expires_in", result)
            
            # Check that the code was stored in the database
            tfa_code = await db.tfa_codes.find_one({
                "email": "test@example.com",
                "user_id": mock_user.clerk_user_id
            })
            
            self.assertIsNotNone(tfa_code)
            self.assertEqual(tfa_code["email"], "test@example.com")
            self.assertEqual(tfa_code["user_id"], mock_user.clerk_user_id)
            self.assertEqual(len(tfa_code["code"]), 6)  # 6-digit code
            
            # Save the code for the next test
            self.verification_code = tfa_code["code"]
            
            logger.info(f"✅ send_2fa_code test passed, verification code: {self.verification_code}")
            
        except Exception as e:
            logger.error(f"❌ Error testing send_2fa_code: {str(e)}")
            raise
    
    async def test_verify_2fa_code(self):
        """Test verify_2fa_code function"""
        logger.info("\n=== Testing verify_2fa_code function ===")
        
        # Create mock request
        request = MockRequest()
        
        # First, send a code
        await self.test_send_2fa_code()
        
        # Create verify request with the code from the previous test
        verify_request = TwoFAVerifyRequest(
            email="test@example.com",
            code=self.verification_code
        )
        
        try:
            # Call the function
            result = await verify_2fa_code(request, verify_request, mock_user)
            
            # Check result
            self.assertIsNotNone(result)
            self.assertIn("message", result)
            self.assertIn("verified", result)
            self.assertIn("user_id", result)
            self.assertTrue(result["verified"])
            
            logger.info("✅ verify_2fa_code test passed")
            
        except Exception as e:
            logger.error(f"❌ Error testing verify_2fa_code: {str(e)}")
            raise
    
    async def test_get_2fa_status(self):
        """Test get_2fa_status function"""
        logger.info("\n=== Testing get_2fa_status function ===")
        
        try:
            # Call the function
            result = await get_2fa_status(mock_user)
            
            # Check result
            self.assertIsNotNone(result)
            self.assertIn("user_id", result)
            self.assertIn("email", result)
            self.assertIn("has_pending_codes", result)
            self.assertIn("pending_count", result)
            
            logger.info("✅ get_2fa_status test passed")
            
        except Exception as e:
            logger.error(f"❌ Error testing get_2fa_status: {str(e)}")
            raise

def run_tests():
    """Run all tests"""
    logger.info("Starting 2FA tests...")
    
    # Create an event loop
    loop = asyncio.get_event_loop()
    
    # Run the tests
    test = Test2FAEndpoints()
    loop.run_until_complete(test.test_send_2fa_code())
    loop.run_until_complete(test.test_verify_2fa_code())
    loop.run_until_complete(test.test_get_2fa_status())
    
    logger.info("All tests passed!")

if __name__ == "__main__":
    run_tests()