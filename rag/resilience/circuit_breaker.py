"""
Circuit breaker pattern implementation for handling failures gracefully.
"""

import time
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for handling failures gracefully.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, calls pass through
    - OPEN: Calls are blocked, circuit is broken
    - HALF_OPEN: Limited calls allowed to test recovery
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting recovery
            expected_exception: Exception type to monitor
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN state")
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}"
                )

        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except self.expected_exception as e:
            self.on_failure()
            raise

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN state")
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}"
                )

        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except self.expected_exception as e:
            self.on_failure()
            raise

    def on_success(self):
        """Handle successful function execution."""
        self.failure_count = 0
        self.state = "CLOSED"
        logger.debug("Circuit breaker reset to CLOSED state")

    def on_failure(self):
        """Handle function failure."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning(f"Circuit breaker failure count: {self.failure_count}")
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")

    def get_state(self) -> Dict[str, Any]:
        """
        Get current circuit breaker state.
        
        Returns:
            Dictionary with circuit breaker state information
        """
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }

    def reset(self):
        """Reset circuit breaker to CLOSED state."""
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset") 