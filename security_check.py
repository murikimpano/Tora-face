#!/usr/bin/env python3
"""
TORA FACE - Security Verification Script
Performs comprehensive security checks on the system
"""

import os
import sys
import requests
import json
import hashlib
import re
from datetime import datetime
import subprocess

class SecurityChecker:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        self.errors = []
        
    def log_result(self, check_name, passed, message=""):
        """Log the result of a security check"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
        if message:
            print(f"   {message}")
        
        if passed:
            self.checks_passed += 1
        else:
            self.checks_failed += 1
            self.errors.append(f"{check_name}: {message}")
    
    def check_environment_variables(self):
        """Check if all required environment variables are set"""
        print("\n🔍 Checking Environment Variables...")
        
        required_vars = [
            'SECRET_KEY',
            'FIREBASE_PROJECT_ID',
            'FIREBASE_API_KEY',
            'FIREBASE_AUTH_DOMAIN'
        ]
        
        all_set = True
        for var in required_vars:
            if not os.getenv(var) or os.getenv(var) == f'your_{var.lower()}':
                self.log_result(f"Environment variable {var}", False, "Not set or using placeholder value")
                all_set = False
        
        if all_set:
            self.log_result("Environment variables", True, "All required variables are set")
    
    def check_secret_key_strength(self):
        """Check if secret keys are strong enough"""
        print("\n🔐 Checking Secret Key Strength...")
        
        secret_key = os.getenv('SECRET_KEY', '')
        jwt_secret = os.getenv('JWT_SECRET_KEY', '')
        
        def is_strong_key(key):
            return (len(key) >= 32 and 
                   any(c.isupper() for c in key) and
                   any(c.islower() for c in key) and
                   any(c.isdigit() for c in key))
        
        self.log_result("SECRET_KEY strength", is_strong_key(secret_key), 
                       "Should be at least 32 characters with mixed case and numbers")
        self.log_result("JWT_SECRET_KEY strength", is_strong_key(jwt_secret),
                       "Should be at least 32 characters with mixed case and numbers")
    
    def check_file_permissions(self):
        """Check file permissions for sensitive files"""
        print("\n📁 Checking File Permissions...")
        
        sensitive_files = [
            '.env',
            'src/firebase/auth.py',
            'src/ai/face_recognition.py'
        ]
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                permissions = oct(stat_info.st_mode)[-3:]
                
                # Check if file is readable by others
                if permissions[2] in ['4', '5', '6', '7']:
                    self.log_result(f"File permissions for {file_path}", False,
                                   f"File is readable by others (permissions: {permissions})")
                else:
                    self.log_result(f"File permissions for {file_path}", True,
                                   f"Permissions are secure ({permissions})")
            else:
                self.log_result(f"File exists: {file_path}", False, "File not found")
    
    def check_dependencies(self):
        """Check for known vulnerable dependencies"""
        print("\n📦 Checking Dependencies...")
        
        try:
            # Check if requirements.txt exists
            if os.path.exists('requirements.txt'):
                with open('requirements.txt', 'r') as f:
                    requirements = f.read()
                
                # Check for potentially vulnerable packages
                vulnerable_patterns = [
                    r'flask==0\.',  # Very old Flask versions
                    r'requests==2\.2[0-5]\.',  # Old requests versions
                    r'pillow==.*[0-7]\.',  # Old Pillow versions
                ]
                
                vulnerabilities_found = False
                for pattern in vulnerable_patterns:
                    if re.search(pattern, requirements, re.IGNORECASE):
                        vulnerabilities_found = True
                        break
                
                self.log_result("Dependency vulnerabilities", not vulnerabilities_found,
                               "Check for known vulnerable package versions")
            else:
                self.log_result("Requirements file", False, "requirements.txt not found")
                
        except Exception as e:
            self.log_result("Dependency check", False, f"Error checking dependencies: {str(e)}")
    
    def check_input_validation(self):
        """Check if input validation is implemented"""
        print("\n🛡️ Checking Input Validation...")
        
        # Check if validation functions exist in the codebase
        validation_files = [
            'src/routes/auth.py',
            'src/routes/face_recognition.py'
        ]
        
        validation_patterns = [
            r'validate_email',
            r'validate_password',
            r'allowed_file',
            r'secure_filename'
        ]
        
        validation_found = False
        for file_path in validation_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    for pattern in validation_patterns:
                        if re.search(pattern, content):
                            validation_found = True
                            break
        
        self.log_result("Input validation", validation_found,
                       "Validation functions found in codebase")
    
    def check_https_configuration(self):
        """Check HTTPS configuration"""
        print("\n🔒 Checking HTTPS Configuration...")
        
        # Check if HTTPS is enforced in the application
        main_file = 'src/main.py'
        if os.path.exists(main_file):
            with open(main_file, 'r') as f:
                content = f.read()
                
            # Look for HTTPS enforcement
            https_patterns = [
                r'force_https',
                r'HTTPS_ONLY',
                r'ssl_context',
                r'talisman'  # Flask-Talisman for security headers
            ]
            
            https_configured = any(re.search(pattern, content, re.IGNORECASE) 
                                 for pattern in https_patterns)
            
            self.log_result("HTTPS enforcement", https_configured,
                           "HTTPS should be enforced in production")
        else:
            self.log_result("Main application file", False, "src/main.py not found")
    
    def check_error_handling(self):
        """Check if proper error handling is implemented"""
        print("\n⚠️ Checking Error Handling...")
        
        # Check for proper error handling in route files
        route_files = [
            'src/routes/auth.py',
            'src/routes/face_recognition.py'
        ]
        
        error_handling_found = False
        for file_path in route_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Look for try-catch blocks and proper error responses
                if ('try:' in content and 'except' in content and 
                    'logger.error' in content):
                    error_handling_found = True
                    break
        
        self.log_result("Error handling", error_handling_found,
                       "Proper try-catch blocks and logging found")
    
    def check_logging_configuration(self):
        """Check if logging is properly configured"""
        print("\n📝 Checking Logging Configuration...")
        
        # Check if logging is configured
        logging_configured = False
        
        # Check main application file
        if os.path.exists('src/main.py'):
            with open('src/main.py', 'r') as f:
                content = f.read()
                if 'logging' in content:
                    logging_configured = True
        
        # Check individual modules
        module_files = [
            'src/firebase/auth.py',
            'src/ai/face_recognition.py'
        ]
        
        for file_path in module_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'logging.basicConfig' in content or 'logger =' in content:
                        logging_configured = True
                        break
        
        self.log_result("Logging configuration", logging_configured,
                       "Logging should be configured for security monitoring")
    
    def check_firebase_security(self):
        """Check Firebase security configuration"""
        print("\n🔥 Checking Firebase Security...")
        
        # Check if Firebase configuration is properly secured
        firebase_config_file = 'src/static/js/firebase-config.js'
        if os.path.exists(firebase_config_file):
            with open(firebase_config_file, 'r') as f:
                content = f.read()
                
            # Check if placeholder values are still being used
            if 'your-api-key-here' in content:
                self.log_result("Firebase configuration", False,
                               "Placeholder values found in Firebase config")
            else:
                self.log_result("Firebase configuration", True,
                               "Firebase config appears to be properly set")
        else:
            self.log_result("Firebase config file", False,
                           "Firebase configuration file not found")
    
    def generate_security_report(self):
        """Generate a comprehensive security report"""
        print("\n" + "="*60)
        print("🛡️  TORA FACE SECURITY REPORT")
        print("="*60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Checks Passed: {self.checks_passed}")
        print(f"Checks Failed: {self.checks_failed}")
        print(f"Total Checks: {self.checks_passed + self.checks_failed}")
        
        if self.checks_failed > 0:
            print("\n❌ SECURITY ISSUES FOUND:")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        # Overall security score
        total_checks = self.checks_passed + self.checks_failed
        if total_checks > 0:
            score = (self.checks_passed / total_checks) * 100
            print(f"\n📊 Security Score: {score:.1f}%")
            
            if score >= 90:
                print("🟢 Excellent security posture")
            elif score >= 75:
                print("🟡 Good security posture with room for improvement")
            elif score >= 50:
                print("🟠 Moderate security posture - address issues before deployment")
            else:
                print("🔴 Poor security posture - DO NOT DEPLOY until issues are resolved")
        
        print("\n" + "="*60)
        
        # Save report to file
        report_file = f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(f"TORA FACE Security Report - {datetime.now()}\n")
            f.write(f"Checks Passed: {self.checks_passed}\n")
            f.write(f"Checks Failed: {self.checks_failed}\n")
            f.write(f"Security Score: {score:.1f}%\n\n")
            
            if self.errors:
                f.write("SECURITY ISSUES:\n")
                for error in self.errors:
                    f.write(f"- {error}\n")
        
        print(f"📄 Detailed report saved to: {report_file}")
    
    def run_all_checks(self):
        """Run all security checks"""
        print("🔍 Starting TORA FACE Security Verification...")
        
        self.check_environment_variables()
        self.check_secret_key_strength()
        self.check_file_permissions()
        self.check_dependencies()
        self.check_input_validation()
        self.check_https_configuration()
        self.check_error_handling()
        self.check_logging_configuration()
        self.check_firebase_security()
        
        self.generate_security_report()

if __name__ == "__main__":
    # Load environment variables
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
    
    checker = SecurityChecker()
    checker.run_all_checks()

