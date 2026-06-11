import time
import logging
from typing import Callable, Any, Type, Tuple, TypeVar, Optional
from functools import wraps
from config import config

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryExhaustedError(Exception):
    """Raised when all retries are exhausted."""

    pass


def retry(
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
    backoff_factor: Optional[float] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry decorator with exponential backoff.

    Args:
        exceptions: Tuple of exceptions to catch and retry upon.
        max_attempts: Maximum number of attempts before failing.
        base_delay: Initial delay in seconds before first retry.
        backoff_factor: Multiplier for delay after each retry.

    Returns:
        Decorated function.
    """

    _max_attempts = (
        max_attempts if max_attempts is not None else config.RETRY_DEFAULT_MAX_ATTEMPTS
    )
    _base_delay = (
        base_delay if base_delay is not None else config.RETRY_DEFAULT_BASE_DELAY
    )
    _backoff_factor = (
        backoff_factor
        if backoff_factor is not None
        else config.RETRY_DEFAULT_BACKOFF_FACTOR
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = _base_delay
            for attempt in range(1, _max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == _max_attempts:
                        logger.error(
                            f"Attempt {attempt}/{_max_attempts} failed for {func.__name__}: {e}. Max retries exhausted."
                        )
                        raise RetryExhaustedError(
                            f"Max retries exhausted for {func.__name__}"
                        ) from e
                    logger.warning(
                        f"Attempt {attempt}/{_max_attempts} failed for {func.__name__}: {e}. Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    delay *= _backoff_factor
            # Fallback raise, should not be reached
            raise RetryExhaustedError("Unexpected retry exhaustion")

        return wrapper

    return decorator


def fallback(
    fallback_func: Callable[..., T],
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Fallback decorator to call a secondary function on failure.

    Args:
        fallback_func: The function to call if the main function fails.
            It must accept the same arguments as the main function.
        exceptions: Tuple of exceptions to catch and trigger fallback.

    Returns:
        Decorated function.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                logger.error(
                    f"Function {func.__name__} failed: {e}. Executing fallback {fallback_func.__name__}..."
                )
                return fallback_func(*args, **kwargs)

        return wrapper

    return decorator
