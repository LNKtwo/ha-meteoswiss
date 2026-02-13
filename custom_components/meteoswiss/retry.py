"""Retry decorator with exponential backoff."""
from __future__ import annotations

import asyncio
import logging
from typing import Callable, TypeVar

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


async def async_retry_with_backoff(
    max_attempts: int = 4,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
) -> Callable[..., T]:
    """Decorator to retry async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (default: 4)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 10.0)

    Returns:
        Decorated async function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    _LOGGER.debug(
                        "Attempt %d/%d for %s",
                        attempt,
                        max_attempts,
                        func.__name__,
                    )
                    return await func(*args, **kwargs)

                except asyncio.TimeoutError as e:
                    last_exception = e
                    if attempt < max_attempts:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                        _LOGGER.warning(
                            "Timeout on attempt %d for %s, retrying in %.1fs",
                            attempt,
                            func.__name__,
                            delay,
                        )
                        await asyncio.sleep(delay)
                    else:
                        _LOGGER.error(
                            "Max attempts (%d) reached for %s (timeout)",
                            max_attempts,
                            func.__name__,
                        )
                        raise

                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                        _LOGGER.warning(
                            "Error on attempt %d for %s: %s, retrying in %.1fs",
                            attempt,
                            func.__name__,
                            e,
                            delay,
                        )
                        await asyncio.sleep(delay)
                    else:
                        _LOGGER.error(
                            "Max attempts (%d) reached for %s: %s",
                            max_attempts,
                            func.__name__,
                            e,
                        )
                        raise

        return wrapper

    return decorator
