#!/usr/bin/env python3
"""
TANSEEQ Screenshot Suite - Setup Validation
===========================================

This script validates that all dependencies and configurations are properly set up
before running the main screenshot suite.
"""

import sys
import os
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_playwright_installation():
    """Check if Playwright is installed"""
    try:
        import playwright
        print(f"✅ Playwright installed: {playwright.__version__}")
        return True
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright")
        return False

def check_playwright_browsers():
    """Check if Playwright browsers are installed"""
    try:
        result = subprocess.run(['playwright', 'install', '--dry-run'], 
                              capture_output=True, text=True)
        if "chromium" in result.stdout.lower():
            print("✅ Playwright browsers available")
            return True
        else:
            print("❌ Playwright browsers not installed. Run: playwright install chromium")
            return False
    except FileNotFoundError:
        print("❌ Playwright CLI not available. Run: pip install playwright")
        return False

def check_backend_url():
    """Check if backend URL is configured"""
    env_file = Path("/app/frontend/.env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if "REACT_APP_BACKEND_URL" in content:
                # Extract URL
                for line in content.split('\n'):
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        url = line.split('=', 1)[1]
                        print(f"✅ Backend URL configured: {url}")
                        return True
        print("❌ REACT_APP_BACKEND_URL not found in .env file")
        return False
    else:
        print("❌ Frontend .env file not found")
        return False

def check_evidence_directory():
    """Check if evidence directory can be created"""
    evidence_dir = Path("/app/evidence")
    try:
        evidence_dir.mkdir(exist_ok=True)
        test_file = evidence_dir / "test_write.txt"
        test_file.write_text("test")
        test_file.unlink()
        print("✅ Evidence directory writable")
        return True
    except Exception as e:
        print(f"❌ Cannot write to evidence directory: {e}")
        return False

def check_test_credentials():
    """Validate test credentials format"""
    credentials = [
        {"email": "admin@tanseeq.com", "password": "ADMIN", "role": "super_admin"},
        {"email": "jihad@tanseeq.com", "password": "jihad123", "role": "user"}
    ]
    
    for cred in credentials:
        if all(key in cred and cred[key] for key in ["email", "password", "role"]):
            print(f"✅ Credentials configured: {cred['email']} ({cred['role']})")
        else:
            print(f"❌ Invalid credentials: {cred}")
            return False
    return True

def check_script_files():
    """Check if all required script files exist"""
    required_files = [
        "/app/tests/playwright_screenshot_suite.py",
        "/app/tests/requirements.txt",
        "/app/run_screenshot_suite.sh"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ Script file exists: {file_path}")
        else:
            print(f"❌ Missing script file: {file_path}")
            all_exist = False
    
    return all_exist

def main():
    """Main validation function"""
    print("🔍 TANSEEQ Screenshot Suite - Setup Validation")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Playwright Installation", check_playwright_installation),
        ("Playwright Browsers", check_playwright_browsers),
        ("Backend URL Configuration", check_backend_url),
        ("Evidence Directory", check_evidence_directory),
        ("Test Credentials", check_test_credentials),
        ("Script Files", check_script_files)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n📋 Checking {check_name}...")
        if check_func():
            passed += 1
        else:
            print(f"   ⚠️  {check_name} check failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Validation Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Ready to run screenshot suite.")
        print("\n🚀 Run the suite with:")
        print("   ./run_screenshot_suite.sh")
        print("   OR")
        print("   cd frontend && yarn test:screenshots")
        print("   OR")
        print("   python tests/playwright_screenshot_suite.py")
        return True
    else:
        print("❌ Some checks failed. Please fix the issues above before running the suite.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)