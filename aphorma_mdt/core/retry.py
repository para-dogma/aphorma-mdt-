"""
Retry Logic with Exponential Backoff
Handles transient failures gracefully
"""
import time
import random
from functools import wraps
from typing import Callable, Tuple, Type, Optional

class RetryError(Exception):
    """Raised when all retries exhausted"""
    def __init__(self, message: str, last_exception: Exception = None):
        super().__init__(message)
        self.last_exception = last_exception

def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Retry decorator with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to delay
        retryable_exceptions: Tuple of exceptions that should trigger retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e                    
                    if attempt == max_attempts:
                        raise RetryError(
                            f"Failed after {max_attempts} attempts: {str(e)}",
                            last_exception=e
                        )
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )
                    
                    # Add jitter
                    if jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    print(f"Attempt {attempt} failed: {str(e)}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
            
            return None
        return wrapper
    return decorator

def retry_async(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """
    Async retry decorator
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        raise RetryError(
                            f"Failed after {max_attempts} attempts: {str(e)}",
                            last_exception=e
                        )
                    
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)                    await asyncio.sleep(delay)
            
            return None
        return wrapper
    return decorator

# Pre-configured retry strategies
retry_immediate = retry(max_attempts=3, base_delay=0.1, max_delay=1.0)
retry_standard = retry(max_attempts=5, base_delay=1.0, max_delay=30.0)
retry_patient = retry(max_attempts=10, base_delay=2.0, max_delay=120.0)
