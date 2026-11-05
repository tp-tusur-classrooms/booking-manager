from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
import logging
from typing import Self

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.low.logging import logger


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Логирует все запросы, с их метаданными. Обрабатываются как успешные, так и нет
    """

    def __init__(self: Self, app: FastAPI) -> None:
        super().__init__(app)
        self.metrics_logger = logger.register_logger(
            "middleware.metrics", level=logging.INFO
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = datetime.now(UTC)
        response = await call_next(request)
        duration = (datetime.now(UTC) - start_time).total_seconds()

        self.metrics_logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)"  # noqa: E501
        )
        return response
