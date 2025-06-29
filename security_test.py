import unittest
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import test modules
sys.path.append(os.path.dirname(__file__))
from client_security_live_test import TestClientDataSecurityLive, run_client_security_live_tests

def run_security_tests():
    """Run all security tests"""
    logger.info("Starting security tests...")
    
    # Run client security live tests
    client_security_result = run_client_security_live_tests()
    
    # Overall result
    if client_security_result:
        logger.info("✅ ALL SECURITY TESTS PASSED")
        return True
    else:
        logger.error("❌ SOME SECURITY TESTS FAILED")
        return False

if __name__ == "__main__":
    success = run_security_tests()
    sys.exit(0 if success else 1)