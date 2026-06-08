"""
Circuit Breaker Pattern
Prevents cascading failures in distributed systems
"""
import time
from functools import wraps
from typing import Callable, Optional
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """
    Circuit Breaker implementation
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None        self.half_open_calls = 0
    
    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker is OPEN. Retry after {self.recovery_timeout}s"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = 0
        
        self.success_count += 1
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:            self.state = CircuitState.OPEN
    
    def get_state(self) -> dict:
        """Get circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time
        }
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_calls = 0

# Global circuit breakers for different services
circuit_breakers = {
    "database": CircuitBreaker(failure_threshold=5, recovery_timeout=30),
    "redis": CircuitBreaker(failure_threshold=3, recovery_timeout=60),
    "blockchain": CircuitBreaker(failure_threshold=3, recovery_timeout=120),
    "external_api": CircuitBreaker(failure_threshold=5, recovery_timeout=60)
}

def with_circuit_breaker(service_name: str = "default"):
    """
    Decorator to add circuit breaker to function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cb = circuit_breakers.get(service_name)
            if not cb:
                cb = CircuitBreaker()
                circuit_breakers[service_name] = cb
            
            return cb.call(func, *args, **kwargs)
        return wrapper
    return decorator

def get_circuit_breaker_stats() -> dict:
    """Get all circuit breaker statistics"""
    return {
        name: cb.get_state()
        for name, cb in circuit_breakers.items()
    }
