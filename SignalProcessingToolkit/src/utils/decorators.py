from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def timed(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        pct = elapsed * 1000
        logger.debug("%s took %.4f ms", func.__name__, pct)
        return result

    return wrapper


def log_call(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.debug("Calling %s with args=%s kwargs=%s", func.__name__, args, kwargs)
        return func(*args, **kwargs)

    return wrapper
