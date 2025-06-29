import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the test modules
sys.path.append(os.path.dirname(__file__))
from backend_test_subfolder import run_hierarchical_folder_tests

def main():
    """Run all tests for the hierarchical folder system with sub-folders"""
    logger.info("Starting tests for hierarchical folder system with sub-folders...")
    
    # Run hierarchical folder tests
    success = run_hierarchical_folder_tests()
    
    if success:
        logger.info("All tests PASSED")
        return 0
    else:
        logger.error("Some tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())