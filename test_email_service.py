import unittest
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the backend directory to the path so we can import modules
backend_dir = Path("/app/backend")
sys.path.append(str(backend_dir))

# Import the email service
try:
    from services.email_service import email_service
    logger.info("✅ Successfully imported email_service")
except Exception as e:
    logger.error(f"❌ Failed to import email_service: {e}")
    email_service = None

class TestEmailService(unittest.TestCase):
    """Test class for email service"""
    
    def test_email_service_exists(self):
        """Test that email_service exists"""
        self.assertIsNotNone(email_service, "email_service should not be None")
    
    def test_send_email_method_exists(self):
        """Test that email_service has send_email method"""
        self.assertTrue(hasattr(email_service, "send_email"), "email_service should have send_email method")
        self.assertTrue(callable(getattr(email_service, "send_email")), "send_email should be callable")

if __name__ == "__main__":
    unittest.main()