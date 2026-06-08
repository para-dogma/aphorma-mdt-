"""
Security Middleware
Provides CORS, Security Headers, and other security features
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Remove server header
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)
        
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests for audit and debugging
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        print(f"[{request.method}] {request.url.path} - Client: {request.client.host}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        print(f"[{request.method}] {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

def setup_security(app: FastAPI, allowed_origins: list = None):
    """
    Setup all security middleware for FastAPI app
    """
    # CORS Configuration
    if allowed_origins is None:
        allowed_origins = ["*"]  # In production, specify exact origins
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security Headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Request Logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # Trusted Hosts (prevent host header attacks)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # In production, specify exact hosts
    )
    
    print("✅ Security middleware configured")
