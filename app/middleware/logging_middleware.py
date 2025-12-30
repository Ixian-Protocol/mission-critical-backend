"""
Request logging middleware.
"""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process each request and log details.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response from the application
        """
        # Generate request ID for tracking
        request_id = str(time.time())
        request.state.request_id = request_id

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"[ID: {request_id}]"
        )

        # Process request and measure time
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"[ID: {request_id}] Status: {response.status_code} "
            f"Duration: {process_time:.3f}s"
        )

        return response
