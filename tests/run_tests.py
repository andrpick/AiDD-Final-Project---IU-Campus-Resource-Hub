#!/usr/bin/env python3
"""
Test runner script for Indiana University Campus Resource Hub.

This script runs all tests in the tests directory with verbose output.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run all tests using pytest."""
    # Get the project root directory (parent of tests folder)
    project_root = Path(__file__).parent.parent
    tests_dir = Path(__file__).parent
    
    # Change to project root directory
    import os
    os.chdir(project_root)
    
    # Build pytest command
    pytest_args = [
        sys.executable, '-m', 'pytest',
        str(tests_dir),
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--color=yes',  # Colored output
    ]
    
    # Add coverage if pytest-cov is available
    try:
        import pytest_cov
        pytest_args.extend([
            '--cov=src',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',  # Coverage reports will be generated in htmlcov/ (gitignored)
        ])
        print("Running tests with coverage...")
        print("Note: Coverage reports will be generated in htmlcov/ directory (gitignored)")
    except ImportError:
        print("Running tests (coverage not available)...")
        print("Install pytest-cov to enable coverage reporting: pip install pytest-cov")
    
    # Run pytest
    print(f"Running tests from: {tests_dir}")
    print(f"Project root: {project_root}")
    print("-" * 80)
    
    result = subprocess.run(pytest_args)
    
    print("-" * 80)
    if result.returncode == 0:
        print("[SUCCESS] All tests passed!")
    else:
        print(f"[FAILED] Tests failed with exit code {result.returncode}")
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())

