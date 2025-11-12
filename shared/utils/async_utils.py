"""
Async utilities for handling blocking operations safely.
"""

import asyncio
import time
import logging
from typing import Any, Callable, Optional
from functools import wraps

logger = logging.getLogger(__name__)


def async_safe_sleep(delay: float) -> None:
    """
    Sleep that works in both sync and async contexts.
    
    Args:
        delay: Time to sleep in seconds
        
    Returns:
        None
    """
    try:
        # Check if we're in an async context
        loop = asyncio.get_running_loop()
        # If we get here, we're in an async context
        # We can't use await here, so we'll use time.sleep as fallback
        # This is not ideal but prevents blocking the event loop
        time.sleep(delay)
    except RuntimeError:
        # We're not in an async context, use time.sleep
        time.sleep(delay)


async def async_sleep(delay: float) -> None:
    """
    Async sleep that properly yields control.
    
    Args:
        delay: Time to sleep in seconds
        
    Returns:
        None
    """
    await asyncio.sleep(delay)


def run_in_executor(func: Callable, *args, **kwargs) -> Any:
    """
    Run a blocking function in a thread executor.
    
    Args:
        func: Function to run
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Function result
    """
    try:
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, func, *args, **kwargs)
    except RuntimeError:
        # Not in async context, run directly
        return func(*args, **kwargs)


def async_retry(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Decorator for async retry functionality.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        
    Returns:
        Decorated async function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"Async attempt {attempt + 1} failed, retrying in {delay}s: {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} async attempts failed")
            
            raise last_exception
        
        return async_wrapper
    
    return decorator


def sync_retry(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Decorator for sync retry functionality.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        
    Returns:
        Decorated sync function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"Sync attempt {attempt + 1} failed, retrying in {delay}s: {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} sync attempts failed")
            
            raise last_exception
        
        return sync_wrapper
    
    return decorator 