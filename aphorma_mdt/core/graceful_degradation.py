"""
Graceful Degradation
Provides fallback mechanisms when services fail
"""
from typing import Callable, Optional, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class DegradedModeError(Exception):
    """Raised when service is in degraded mode"""
    pass

def with_fallback(
    fallback_func: Optional[Callable] = None,
    fallback_value: Any = None,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to provide fallback on failure
    
    Args:
        fallback_func: Function to call on failure
        fallback_value: Value to return on failure
        exceptions: Exceptions that should trigger fallback
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:                return func(*args, **kwargs)
            except exceptions as e:
                logger.warning(
                    f"Function {func.__name__} failed: {str(e)}. Using fallback."
                )
                
                if fallback_func:
                    return fallback_func(*args, **kwargs)
                elif fallback_value is not None:
                    return fallback_value
                else:
                    raise DegradedModeError(
                        f"Service {func.__name__} unavailable and no fallback configured"
                    )
        return wrapper
    return decorator

class FallbackCache:
    """
    Cache for fallback values
    """
    def __init__(self):
        self.cache = {}
        self.ttl = 300  # 5 minutes default TTL
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached fallback value"""
        import time
        cached = self.cache.get(key)
        
        if cached:
            value, timestamp = cached
            if time.time() - timestamp < self.ttl:
                return value
        
        return None
    
    def set(self, key: str, value: Any):
        """Set fallback value"""
        import time
        self.cache[key] = (value, time.time())
    
    def clear(self, key: str = None):
        """Clear fallback cache"""
        if key:
            self.cache.pop(key, None)
        else:
            self.cache.clear()

# Global fallback cachefallback_cache = FallbackCache()

def cached_fallback(ttl: int = 300):
    """
    Decorator to cache function result as fallback
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try cache first
            cached = fallback_cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Using cached fallback for {func.__name__}")
                return cached
            
            # Execute and cache
            try:
                result = func(*args, **kwargs)
                fallback_cache.set(cache_key, result)
                return result
            except Exception as e:
                logger.error(f"Fallback function {func.__name__} failed: {str(e)}")
                raise DegradedModeError(f"All fallbacks failed for {func.__name__}")
        return wrapper
    return decorator

def degrade_gracefully(
    primary: Callable,
    fallback: Callable = None,
    fallback_value: Any = None
):
    """
    Execute primary function, degrade to fallback on failure
    """
    @wraps(primary)
    def wrapper(*args, **kwargs):
        try:
            return primary(*args, **kwargs)
        except Exception as e:
            logger.warning(
                f"Primary function {primary.__name__} failed: {str(e)}. Degrading gracefully."
            )
            
            if fallback:
                return fallback(*args, **kwargs)
            elif fallback_value is not None:
                return fallback_value
            else:                raise DegradedModeError(
                    f"Service {primary.__name__} unavailable"
                )
    return wrapper
