import pytest
import sys

def run_tests():
    print("Running master test suite...")
    
    # Configure pytest arguments
    args = [
        "-v",
        "--cov=main",
        "--cov=resilience",
        "--cov=simulation",
        "--cov-report=term",
        "tests/"
    ]
    
    # Run tests
    exit_code = pytest.main(args)
    
    # Output summary report
    print("\n" + "="*50)
    print("TEST SUMMARY REPORT")
    print("="*50)
    
    if exit_code == 0:
        print("✅ ALL TESTS PASSED SUCCESSFULLY")
    else:
        print(f"❌ TESTS FAILED (Exit code: {exit_code})")
        
    print("="*50)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(run_tests())
