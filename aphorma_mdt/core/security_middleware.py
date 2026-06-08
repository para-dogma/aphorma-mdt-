"""OWASP Security Middleware for AphormA-MDT"""
from fastapi import Request, HTTPException
from fastapi.middleware import Middleware
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import re
import html
from typing import List, Set

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        
        # Remove server header
        if 'server' in response.headers:
            del response.headers['server']
        
        return response

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize input to prevent injection attacks"""
    
    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|EXEC|EXECUTE)\b.*\b(FROM|INTO|TABLE|WHERE|SET)\b)",
        r"(--|;|\/\*|\*\/|xp_)",
        r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)"
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",        r"<embed[^>]*>"
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"/etc/passwd",
        r"/etc/shadow",
        r"/proc/self"
    ]
    
    def __init__(self, app, max_body_size: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_body_size = max_body_size
    
    def _check_patterns(self, value: str, patterns: List[str], attack_type: str) -> None:
        """Check value against patterns"""
        if not value:
            return
        
        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail=f"Potential {attack_type} attack detected"
                )
    
    def _sanitize_string(self, value: str) -> str:
        """Sanitize string value"""
        # Remove null bytes
        value = value.replace('\x00', '')
        # HTML encode
        value = html.escape(value)
        return value
    
    def _validate_query_params(self, params: dict) -> None:
        """Validate query parameters"""
        for key, value in params.items():
            if isinstance(value, str):
                self._check_patterns(value, self.SQL_INJECTION_PATTERNS, "SQL injection")
                self._check_patterns(value, self.XSS_PATTERNS, "XSS")
                self._check_patterns(value, self.PATH_TRAVERSAL_PATTERNS, "path traversal")
    
    def _validate_path(self, path: str) -> None:
        """Validate request path"""
        self._check_patterns(path, self.PATH_TRAVERSAL_PATTERNS, "path traversal")
    
    async def dispatch(self, request: Request, call_next):
        # Validate path
        self._validate_path(request.url.path)        
        # Validate query parameters
        self._validate_query_params(dict(request.query_params))
        
        # Check content length
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > self.max_body_size:
            raise HTTPException(
                status_code=413,
                detail="Request body too large"
            )
        
        # Validate headers
        user_agent = request.headers.get('user-agent', '')
        if not user_agent:
            raise HTTPException(
                status_code=400,
                detail="Missing User-Agent header"
            )
        
        response = await call_next(request)
        return response

class CORSConfig:
    """CORS configuration"""
    
    ALLOWED_ORIGINS: Set[str] = {
        "http://localhost:3000",
        "http://localhost:8000",
        "https://your-domain.com"  # Change in production
    }
    
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = [
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "Accept",
        "Origin"
    ]
    MAX_AGE: int = 600  # 10 minutes

def create_security_middleware() -> List[Middleware]:
    """Create security middleware stack"""
    return [
        Middleware(SecurityHeadersMiddleware),
        Middleware(InputValidationMiddleware)
    ]
