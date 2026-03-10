"""
Retry decorator with exponential backoff and jitter.

Drop-in decorator for any function that makes external API calls
(TickerTrace, Yahoo, Gemini, Tradier, etc). Prevents pipeline failures
from transient network issues.

Usage:
    @retry
    def fetch_data():
        ...
    
    @retry(max_retries=5, initial_delay=2.0)
    def fetch_important_data():
        ...
"""

import functools
import random
import time
import sys


def retry(_func=None, *, max_retries: int = 3, initial_delay: float = 1.0,
          backoff_factor: float = 2.0, max_delay: float = 30.0,
          exceptions: tuple = (Exception,)):
    """
    Retry decorator with exponential backoff and jitter.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiply delay by this factor each retry
        max_delay: Maximum delay cap in seconds
        exceptions: Tuple of exception types to catch and retry on
    
    Can be used as both @retry and @retry(max_retries=5):
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    # Add jitter: ±25% randomization
                    jittered_delay = delay * (0.75 + random.random() * 0.5)
                    jittered_delay = min(jittered_delay, max_delay)
                    
                    print(f"  [RETRY] {func.__name__} attempt {attempt + 1}/{max_retries} "
                          f"failed: {str(e)[:80]}. Retrying in {jittered_delay:.1f}s...",
                          file=sys.stderr)
                    
                    time.sleep(jittered_delay)
                    delay *= backoff_factor
            
            # All retries exhausted
            print(f"  [RETRY] {func.__name__} failed after {max_retries} retries: {last_exception}",
                  file=sys.stderr)
            raise last_exception
        
        return wrapper
    
    # Support both @retry and @retry(max_retries=5)
    if _func is not None:
        return decorator(_func)
    return decorator
