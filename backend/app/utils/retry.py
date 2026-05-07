import asyncio
import functools
import logging
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


def async_retry(max_attempts: int = 3, backoff_factor: float = 2.0):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            delay = 1.0
            last_exc: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_attempts - 1:
                        logger.warning(
                            "Retry attempt %d for %s: %s",
                            attempt + 1,
                            func.__name__,
                            exc,
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator
