import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class StructlogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
        )

        start_time = time.time()
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log de sucesso
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_seconds=round(duration, 3),
            )

            response.headers["X-Correlation-ID"] = correlation_id
            return response

        except Exception as exc:
            duration = time.time() - start_time

            logger.error(
                "request_failed",
                duration_seconds=round(duration, 3),
                error=str(exc),
                exc_info=True,
            )
            raise
