"""Retry utilities with exponential backoff."""
from typing import Type, Tuple, Callable, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryCallState
)
import logging
from requests.exceptions import ConnectionError, HTTPError, Timeout, RequestException

logger = logging.getLogger("stock_data_collector")


# Default retry exceptions
DEFAULT_RETRY_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    ConnectionError,
    HTTPError,
    Timeout,
    RequestException,
    TimeoutError,
)


def is_retryable_http_error(exception: Exception) -> bool:
    """Check if HTTP error is retryable (5xx errors)."""
    if isinstance(exception, HTTPError):
        if hasattr(exception, 'response') and exception.response is not None:
            return 500 <= exception.response.status_code < 600
    return False


def create_retry_decorator(
    max_attempts: int = 3,
    min_wait: int = 4,
    max_wait: int = 10,
    multiplier: int = 1,
    retry_exceptions: Tuple[Type[Exception], ...] = DEFAULT_RETRY_EXCEPTIONS
) -> Callable:
    """Create a retry decorator with custom parameters."""
    
    def should_retry(retry_state: RetryCallState) -> bool:
        """Custom retry logic."""
        if retry_state.outcome is None:
            return True
        
        if retry_state.outcome.failed:
            exception = retry_state.outcome.exception()
            
            # Retry on specified exceptions
            if isinstance(exception, retry_exceptions):
                # Special handling for HTTP errors
                if isinstance(exception, HTTPError):
                    return is_retryable_http_error(exception)
                return True
                
        return False
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
        retry=should_retry,
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )


# Default retry decorator
default_retry = create_retry_decorator()


# API-specific retry decorator with longer waits
api_retry = create_retry_decorator(
    max_attempts=3,
    min_wait=5,
    max_wait=30,
    multiplier=2
)