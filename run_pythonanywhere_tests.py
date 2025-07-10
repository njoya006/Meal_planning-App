#!/usr/bin/env python
"""
Script to run test files on PythonAnywhere console
"""

import os
import sys
import subprocess

# Get the directory of the script
project_dir = os.path.dirname(os.path.abspath(__file__))

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f" {title.upper()} ".center(70, "="))
    print("=" * 70)

def run_test(test_file):
    """Run a specific test file"""
    try:
        print_header(f"Running {test_file}")
        filepath = os.path.join(project_dir, test_file)
        
        if not os.path.exists(filepath):
            print(f"Error: Test file {filepath} does not exist")
            return False
        
        # Run the test script
        result = subprocess.run(
            [sys.executable, filepath],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        
        if result.stderr:
            print("Error output:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running test: {str(e)}")
        return False

def main():
    """Main function to run tests"""
    print_header("Running ChopSmo Backend Tests")
    
    # List of tests to run
    tests = [
        "test_login_functionality.py",
        "test_chef_assistant.py"
    ]
    
    success_count = 0
    
    for test in tests:
        if run_test(test):
            success_count += 1
    
    print_header("Test Results Summary")
    print(f"Tests run: {len(tests)}")
    print(f"Tests passed: {success_count}")
    print(f"Tests failed: {len(tests) - success_count}")

if __name__ == "__main__":
    main()
