"""Security checks on application startup"""
import os
import sys
import hashlib
from typing import List, Tuple

class SecurityChecker:
    def __init__(self):
        self.issues: List[str] = []
        self.warnings: List[str] = []
    
    def check_jwt_secret(self) -> Tuple[bool, str]:
        """Check JWT secret strength"""
        secret = os.getenv('JWT_SECRET_KEY', '')
        
        if not secret:
            return False, "JWT_SECRET_KEY not set"
        
        if secret in ['dev-secret', 'change-me', 'secret', 'test']:
            return False, "JWT_SECRET_KEY is using default value"
        
        if len(secret) < 32:
            return False, "JWT_SECRET_KEY too short (min 32 chars)"
        
        return True, "JWT secret OK"
    
    def check_debug_mode(self) -> Tuple[bool, str]:
        """Check debug mode is off in production"""
        debug = os.getenv('APP_DEBUG', 'false').lower()
        
        if debug == 'true':
            return False, "APP_DEBUG is enabled in production"
        
        return True, "Debug mode disabled"    
    def check_database_url(self) -> Tuple[bool, str]:
        """Check database URL is configured"""
        db_url = os.getenv('DATABASE_URL', '')
        
        if not db_url:
            return False, "DATABASE_URL not set"
        
        if 'localhost' in db_url and os.getenv('APP_ENV') == 'production':
            return False, "Database pointing to localhost in production"
        
        return True, "Database URL OK"
    
    def check_redis_password(self) -> Tuple[bool, str]:
        """Check Redis has password"""
        redis_url = os.getenv('REDIS_URL', '')
        
        if 'redis://' in redis_url and '@' not in redis_url:
            return False, "Redis URL has no password"
        
        return True, "Redis password set"
    
    def run_all_checks(self) -> dict:
        """Run all security checks"""
        checks = [
            self.check_jwt_secret(),
            self.check_debug_mode(),
            self.check_database_url(),
            self.check_redis_password()
        ]
        
        passed = sum(1 for ok, _ in checks if ok)
        total = len(checks)
        
        return {
            'passed': passed,
            'total': total,
            'score': f"{passed}/{total}",
            'details': checks,
            'ready_for_production': passed == total
        }

security_checker = SecurityChecker()
