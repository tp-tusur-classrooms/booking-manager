import asyncio
from collections.abc import Awaitable, Callable
from typing import Self

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(
        self: Self, app: FastAPI, default_timeout: float | None = None
    ) -> None:
        super().__init__(app)
        self.default_timeout = default_timeout

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        route_timeout = self.default_timeout
        route = request.scope.get("route")
        if route is not None:
            endpoint = getattr(route, "endpoint", None)
            if endpoint and hasattr(endpoint, "_timeout"):
                route_timeout = endpoint._timeout

        if route_timeout is not None:
            # uvicorn handing check
            return await asyncio.wait_for(call_next(request), timeout=route_timeout)
        else:
            return await call_next(request)
