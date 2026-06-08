"""Advanced Rate Limiting with Redis"""
import redis
import time
from typing import Dict, Optional, Tuple
from fastapi import Request, HTTPException
from fastapi.middleware import Middleware
from fastapi.middleware.base import BaseHTTPMiddleware
import os

class RateLimiter:
    def __init__(self, redis_url: str = None):
        self.redis = redis.Redis.from_url(
            redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True
        )
    
    def is_rate_limited(self, identifier: str, limit: int, window: int) -> Tuple[bool, Dict]:
        """
        Check if identifier is rate limited
        Returns: (is_limited, info_dict)
        """
        key = f"ratelimit:{identifier}"
        current = self.redis.incr(key)
        
        if current == 1:
            self.redis.expire(key, window)
        
        ttl = self.redis.ttl(key)
        remaining = max(0, limit - current)
        
        return current > limit, {
            'limit': limit,
            'remaining': remaining,
            'reset': ttl,
            'current': current
        }
    
    def get_rate_limit_headers(self, info: Dict) -> Dict[str, str]:
        """Get rate limit headers"""
        return {
            'X-RateLimit-Limit': str(info['limit']),
            'X-RateLimit-Remaining': str(info['remaining']),
            'X-RateLimit-Reset': str(info['reset'])
        }

# Rate limiting middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: RateLimiter = None):        super().__init__(app)
        self.limiter = limiter or RateLimiter()
        
        # Default limits
        self.limits = {
            '/api/': (100, 60),  # 100 requests per minute
            '/api/tokens/mint': (10, 60),  # 10 per minute
            '/api/auth/login': (5, 300),  # 5 per 5 minutes
            '/metrics': (60, 60),  # 60 per minute
        }
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP or user_id)
        client_id = request.client.host if request.client else 'unknown'
        
        # Try to get user from auth header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            client_id = f"user:{hash(auth_header)}"
        
        # Find matching limit
        path = request.url.path
        limit_config = None
        for prefix, config in self.limits.items():
            if path.startswith(prefix):
                limit_config = config
                break
        
        if limit_config:
            limit, window = limit_config
            identifier = f"{client_id}:{path}"
            
            is_limited, info = self.limiter.is_rate_limited(
                identifier, limit, window
            )
            
            if is_limited:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests",
                    headers=self.limiter.get_rate_limit_headers(info)
                )
            
            response = await call_next(request)
            
            # Add rate limit headers
            for header, value in self.limiter.get_rate_limit_headers(info).items():
                response.headers[header] = value
            
            return response        
        return await call_next(request)

# Create global limiter instance
rate_limiter = RateLimiter()
