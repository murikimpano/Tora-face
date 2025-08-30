#!/usr/bin/env python3
"""
TORA FACE - Advanced Security Verification Script
Performs comprehensive security checks on the system with automated recommendations
"""

import os
import sys
import re
import json
import hashlib
from datetime import datetime

class SecurityChecker:
    REQUIRED_ENV_VARS = [
        'SECRET_KEY',
        'JWT_SECRET_KEY',
        'FIREBASE_PROJECT_ID',
        'FIREBASE_API_KEY',
        'FIREBASE_AUTH_DOMAIN'
    ]
    
    SENSITIVE_FILES = [
        '.env',
        'src/firebase/auth.py',
        'src/ai/face_recognition.py'
    ]
    
    VULNERABLE_PACKAGES_PATTERNS = [
        r'flask==0\.',  # Old Flask versions
        r'requests==2\.2[0-5]\.',  # Old requests versions
        r'pillow==.*[0-7]\.'  # Old Pillow versions
    ]
    
    VALIDATION_PATTERNS = [
        r'validate_email',
        r'validate_password',
        r'allowed_file',
        r'secure_filename'
    ]
    
    HTTPS_PATTERNS = [
        r'force_https',
        r'HTTPS_ONLY',
        r'ssl_context',
        r'talisman'
    ]
    
    ERROR_HANDLING_PATTERNS = ['try:', 'except', 'logger.error']

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        self.errors = []
        self.score = 0

    def log_result(self, check_name, passed, message=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
        if message:
            print(f"   {message}")
        if passed:
            self.checks_passed += 1
        else:
            self.checks_failed += 1
            self.errors.append(f"{check_name}: {message}")

    def check_env_variables(self):
        print("\n🔍 Checking Environment Variables...")
        all_set = True
        for var in self.REQUIRED_ENV_VARS:
            val = os.getenv(var)
            if not val or re.match(r'your[-_a-z]*', str(val), re.IGNORECASE):
                self.log_result(f"Environment variable {var}", False, "Not set or using placeholder value")
                all_set = False
        if all_set:
            self.log_result("Environment variables", True, "All required variables are set")
        
        # Detect extra/unnecessary env vars
        all_env = set(os.environ.keys())
        extra_vars = all_env - set(self.REQUIRED_ENV_VARS)
        if extra_vars:
            self.warnings.append(f"Extra environment variables detected: {', '.join(extra_vars)}")

    def check_secret_keys(self):
        print("\n🔐 Checking Secret Keys Strength...")
        def strong_key(key):
            return len(key) >= 32 and any(c.isupper() for c in key) and any(c.islower() for c in key) and any(c.isdigit() for c in key)
        
        secret = os.getenv('SECRET_KEY', '')
        jwt_secret = os.getenv('JWT_SECRET_KEY', '')
        self.log_result("SECRET_KEY strength", strong_key(secret), "At least 32 chars, mixed case & numbers")
        self.log_result("JWT_SECRET_KEY strength", strong_key(jwt_secret), "At least 32 chars, mixed case & numbers")

    def check_file_permissions(self):
        print("\n📁 Checking File Permissions...")
        for file_path in self.SENSITIVE_FILES:
            if os.path.exists(file_path):
                perm = oct(os.stat(file_path).st_mode)[-3:]
                if perm[2] in ['4','5','6','7']:
                    self.log_result(f"File permissions for {file_path}", False, f"Readable by others ({perm})")
                    # Attempt auto-fix
                    try:
                        os.chmod(file_path, 0o600)
                        self.warnings.append(f"Permissions of {file_path} automatically set to 600")
                    except Exception:
                        self.warnings.append(f"Could not auto-fix permissions for {file_path}")
                else:
                    self.log_result(f"File permissions for {file_path}", True, f"Permissions are secure ({perm})")
            else:
                self.log_result(f"File exists: {file_path}", False, "File not found")

    def check_dependencies(self):
        print("\n📦 Checking Dependencies...")
        if os.path.exists('requirements.txt'):
            with open('requirements.txt') as f:
                content = f.read()
            found_vuln = any(re.search(p, content, re.IGNORECASE) for p in self.VULNERABLE_PACKAGES_PATTERNS)
            self.log_result("Dependency vulnerabilities", not found_vuln, "Check for known vulnerable package versions")
        else:
            self.log_result("Requirements file", False, "requirements.txt not found")

    def check_input_validation(self):
        print("\n🛡️ Checking Input Validation...")
        validation_found = False
        files = ['src/routes/auth.py', 'src/routes/face_recognition.py']
        for file_path in files:
            if os.path.exists(file_path):
                with open(file_path) as f:
                    content = f.read()
                if any(re.search(p, content) for p in self.VALIDATION_PATTERNS):
                    validation_found = True
                    break
        self.log_result("Input validation", validation_found, "Validation functions found in codebase")

    def check_https(self):
        print("\n🔒 Checking HTTPS Configuration...")
        file_path = 'src/main.py'
        https_configured = False
        if os.path.exists(file_path):
            with open(file_path) as f:
                content = f.read()
            if any(re.search(p, content, re.IGNORECASE) for p in self.HTTPS_PATTERNS):
                https_configured = True
        self.log_result("HTTPS enforcement", https_configured, "HTTPS should be enforced in production")

    def check_error_handling(self):
        print("\n⚠️ Checking Error Handling...")
        found = False
        files = ['src/routes/auth.py', 'src/routes/face_recognition.py']
        for file_path in files:
            if os.path.exists(file_path):
                content = open(file_path).read()
                if all(p in content for p in ['try:', 'except']):
                    found = True
                    break
        self.log_result("Error handling", found, "Proper try-except blocks found")

    def check_logging(self):
        print("\n📝 Checking Logging Configuration...")
        logging_found = False
        files = ['src/main.py', 'src/firebase/auth.py', 'src/ai/face_recognition.py']
        for file_path in files:
            if os.path.exists(file_path):
                content = open(file_path).read()
                if 'logging' in content:
                    logging_found = True
                    break
        self.log_result("Logging configuration", logging_found, "Logging should be configured")

    def check_firebase(self):
        print("\n🔥 Checking Firebase Security...")
        file_path = 'src/static/js/firebase-config.js'
        if os.path.exists(file_path):
            content = open(file_path).read()
            if 'your-api-key-here' in content:
                self.log_result("Firebase config", False, "Placeholder API keys detected")
            else:
                self.log_result("Firebase config", True, "Firebase configuration seems correct")
        else:
            self.log_result("Firebase config file", False, "File not found")

    def generate_report(self):
        total = self.checks_passed + self.checks_failed
        if total > 0:
            self.score = (self.checks_passed / total) * 100
        
        print("\n" + "="*60)
        print("🛡️ TORA FACE Security Report")
        print("="*60)
        print(f"Date: {datetime.now()}")
        print(f"Checks Passed: {self.checks_passed}")
        print(f"Checks Failed: {self.checks_failed}")
        print(f"Score: {self.score:.1f}%")
        if self.errors:
            print("\n❌ SECURITY ISSUES FOUND:")
            for e in self.errors:
                print(f" • {e}")
        if self.warnings:
            print("\n⚠️ WARNINGS:")
            for w in self.warnings:
                print(f" • {w}")
        
        # Save report
        filename = f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write("TORA FACE Security Report\n")
            f.write(f"Date: {datetime.now()}\n")
            f.write(f"Score: {self.score:.1f}%\n")
            f.write(f"Checks Passed: {self.checks_passed}\n")
            f.write(f"Checks Failed: {self.checks_failed}\n\n")
            if self.errors:
                f.write("SECURITY ISSUES:\n")
                for e in self.errors:
                    f.write(f"- {e}\n")
            if self.warnings:
                f.write("\nWARNINGS:\n")
                for w in self.warnings:
                    f.write(f"- {w}\n")
        print(f"\n📄 Report saved to: {filename}")

    def run_all(self):
        print("🔍 Starting TORA FACE Advanced Security Scan...")
        self.check_env_variables()
        self.check_secret_keys()
        self.check_file_permissions()
        self.check_dependencies()
        self.check_input_validation()
        self.check_https()
        self.check_error_handling()
        self.check_logging()
        self.check_firebase()
        self.generate_report()


if __name__ == "__main__":
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        load_dotenv()
    checker = SecurityChecker()
    checker.run_all()
