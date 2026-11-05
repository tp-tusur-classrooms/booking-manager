from collections.abc import Callable
from functools import wraps
from typing import Any


def timeout(seconds: float) -> Callable:

    def decorator(func: Callable) -> Callable:
        func._timeout = seconds  # ty: ignore[unresolved-attribute]

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        return wrapper

    return decorator
