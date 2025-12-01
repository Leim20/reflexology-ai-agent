"""
Rate Limiter for Google Sheets API
Prevents hitting quota limits proactively using token bucket algorithm

Google Sheets quota: ~100 requests per 100 seconds (60 per 60 seconds)
"""

import time
import threading
from datetime import datetime, timedelta
from collections import deque
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for Google Sheets API.

    Tracks API calls and prevents exceeding quota limits.
    Google Sheets: 60 requests per 60 seconds
    """

    def __init__(self, max_requests_per_minute: int = 60, critical_threshold: float = 0.5):
        """
        Initialize rate limiter.

        Args:
            max_requests_per_minute: Google Sheets quota (default 60)
            critical_threshold: Alert when usage exceeds this % (default 50%)
        """
        self.max_requests = max_requests_per_minute
        self.critical_threshold = critical_threshold
        self.request_times = deque(maxlen=max_requests_per_minute)
        self.lock = threading.Lock()
        logger.info(f"[RateLimiter] Initialized with {max_requests_per_minute} requests/minute quota")

    def should_wait(self) -> bool:
        """
        Check if we're approaching quota limit.

        Returns:
            bool: True if should wait before next API call
        """
        with self.lock:
            now = datetime.now()
            # Remove requests older than 60 seconds
            while self.request_times and self.request_times[0] < now - timedelta(seconds=60):
                self.request_times.popleft()

            # Calculate current usage percentage
            usage = len(self.request_times) / self.max_requests
            return usage >= self.critical_threshold

    def get_wait_time(self) -> float:
        """
        Get how long to wait before next request (in seconds).

        Returns:
            float: Seconds to wait (0 if no wait needed)
        """
        with self.lock:
            if len(self.request_times) < self.max_requests:
                return 0

            # Wait until oldest request leaves the 60-second window
            oldest = self.request_times[0]
            now = datetime.now()
            window_end = oldest + timedelta(seconds=60)

            wait_seconds = (window_end - now).total_seconds()
            return max(0, wait_seconds + 0.1)  # +0.1 for safety margin

    def record_request(self):
        """Record that an API request was made."""
        with self.lock:
            self.request_times.append(datetime.now())

    def wait_if_needed(self):
        """Block until safe to make next API request."""
        wait_time = self.get_wait_time()
        if wait_time > 0:
            logger.warning(f"[RateLimiter] Quota approaching, waiting {wait_time:.2f}s before next request")
            time.sleep(wait_time)

    def get_current_usage(self) -> float:
        """
        Get current quota usage as percentage.

        Returns:
            float: Usage percentage (0-100)
        """
        with self.lock:
            now = datetime.now()
            # Remove old requests
            while self.request_times and self.request_times[0] < now - timedelta(seconds=60):
                self.request_times.popleft()

            return (len(self.request_times) / self.max_requests) * 100

    def get_remaining_requests(self) -> int:
        """
        Get remaining requests available this minute.

        Returns:
            int: Number of requests still available
        """
        with self.lock:
            now = datetime.now()
            # Remove old requests
            while self.request_times and self.request_times[0] < now - timedelta(seconds=60):
                self.request_times.popleft()

            return self.max_requests - len(self.request_times)


def wait_with_backoff(attempt: int) -> int:
    """
    Calculate exponential backoff wait time.

    Attempt 1 → 2 seconds
    Attempt 2 → 4 seconds
    Attempt 3 → 8 seconds
    Attempt 4 → 16 seconds

    Args:
        attempt: Attempt number (1, 2, 3, ...)

    Returns:
        int: Seconds to wait
    """
    wait_seconds = 2 ** attempt
    logger.info(f"[Backoff] Attempt {attempt}: waiting {wait_seconds} seconds")
    return wait_seconds


# Global rate limiter instance
_global_rate_limiter: Optional[RateLimiter] = None
_limiter_lock = threading.Lock()


def get_rate_limiter() -> RateLimiter:
    """
    Get or create global rate limiter instance.

    Returns:
        RateLimiter: Global rate limiter
    """
    global _global_rate_limiter

    if _global_rate_limiter is None:
        with _limiter_lock:
            if _global_rate_limiter is None:
                _global_rate_limiter = RateLimiter()
                logger.info("[RateLimiter] Global rate limiter created")

    return _global_rate_limiter


def throttle_if_busy() -> bool:
    """
    Check if system is busy and throttle if needed.

    Returns:
        bool: True if throttled, False if allowed to proceed immediately
    """
    limiter = get_rate_limiter()
    if limiter.should_wait():
        logger.info("[RateLimiter] System busy, applying throttle")
        limiter.wait_if_needed()
        return True
    return False


def track_api_call():
    """Track that an API call was made."""
    limiter = get_rate_limiter()
    limiter.record_request()


def get_quota_status() -> dict:
    """
    Get current quota status.

    Returns:
        dict: Status information with usage, remaining, etc.
    """
    limiter = get_rate_limiter()
    usage = limiter.get_current_usage()
    remaining = limiter.get_remaining_requests()

    return {
        'usage_percent': usage,
        'remaining_requests': remaining,
        'max_requests': limiter.max_requests,
        'approaching_limit': usage >= limiter.critical_threshold * 100,
        'timestamp': datetime.now().isoformat()
    }


# Convenience function for retry logic
def should_retry(attempt: int, max_attempts: int = 3) -> bool:
    """
    Determine if should retry based on attempt number.

    Args:
        attempt: Current attempt number (1, 2, 3, ...)
        max_attempts: Maximum number of attempts allowed

    Returns:
        bool: True if should retry
    """
    return attempt < max_attempts


def sleep_with_backoff(attempt: int):
    """
    Sleep with exponential backoff.

    Args:
        attempt: Current attempt number (1, 2, 3, ...)
    """
    wait_seconds = wait_with_backoff(attempt)
    time.sleep(wait_seconds)


def retry_on_quota_error(func):
    """
    Decorator that retries API calls on quota errors (429) with exponential backoff.
    
    Usage:
        @retry_on_quota_error
        def my_api_call():
            return sheet.get_all_values()
    """
    def wrapper(*args, **kwargs):
        from gspread.exceptions import APIError
        
        for attempt in range(1, 4):  # 3 attempts
            try:
                return func(*args, **kwargs)
            except APIError as e:
                # Check if it's a quota error (429)
                if "[429]" in str(e):
                    if attempt < 3:
                        wait_time = wait_with_backoff(attempt)
                        logger.warning(f"[Quota 429] Attempt {attempt}/3 failed. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"[Quota 429] All 3 attempts failed. Raising error.")
                        raise
                else:
                    # Not a quota error, raise immediately
                    raise
    
    return wrapper
