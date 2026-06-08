"""
Rate Limiter using Redis
Protects API from abuse and DDoS attacks
"""
from typing import Optional, Dict
import time
import redis
from fastapi import HTTPException, status, Request
from functools import wraps

class RateLimiter:
    """
    Redis-based rate limiter
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            self.enabled = True
        except redis.ConnectionError:
            self.redis_client = None
            self.enabled = False
            print("⚠️  Redis not available, rate limiting disabled")
        
        self.default_limit = 100  # requests per window
        self.default_window = 60  # seconds
    
    def is_rate_limited(
        self, 
        identifier: str, 
        limit: int = None, 
        window: int = None
    ) -> bool:
        """
        Check if identifier is rate limited
        Returns True if rate limited, False otherwise
        """
        if not self.enabled:
            return False
        
        limit = limit or self.default_limit
        window = window or self.default_window
        
        key = f"rate_limit:{identifier}"
        
        try:
            current = self.redis_client.get(key)
                        if current is None:
                self.redis_client.setex(key, window, 1)
                return False
            
            current_count = int(current)
            
            if current_count >= limit:
                return True
            
            self.redis_client.incr(key)
            return False
        except redis.RedisError:
            return False
    
    def get_rate_limit_info(
        self, 
        identifier: str, 
        limit: int = None, 
        window: int = None
    ) -> Dict:
        """
        Get rate limit information for identifier
        """
        if not self.enabled:
            return {"limit": limit or self.default_limit, "remaining": limit or self.default_limit, "reset_in": 0}
        
        limit = limit or self.default_limit
        window = window or self.default_window
        
        key = f"rate_limit:{identifier}"
        current = self.redis_client.get(key)
        ttl = self.redis_client.ttl(key)
        
        return {
            "limit": limit,
            "remaining": max(0, limit - (int(current) if current else 0)),
            "reset_in": max(0, ttl) if ttl > 0 else window
        }
    
    def reset_rate_limit(self, identifier: str) -> bool:
        """Reset rate limit for identifier"""
        if not self.enabled:
            return False
        
        key = f"rate_limit:{identifier}"
        return self.redis_client.delete(key) > 0

rate_limiter = RateLimiter()

def rate_limit(limit: int = 100, window: int = 60):    """Rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request is None:
                request = kwargs.get('request')
            
            identifier = request.client.host if request else "default"
            
            if rate_limiter.is_rate_limited(identifier, limit, window):
                info = rate_limiter.get_rate_limit_info(identifier, limit, window)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": str(info["remaining"]),
                        "X-RateLimit-Reset": str(info["reset_in"])
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
