"""
FastAPI Middleware for SpecGap
Provides request tracking, error handling, and performance monitoring.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger("middleware")


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Adds request ID tracking and logs request/response details.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Start timer
        start_time = time.perf_counter()

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )

        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log response
            logger.info(
                f"[{request_id}] {response.status_code} ({duration_ms:.1f}ms)",
                extra={"request_id": request_id, "duration_ms": duration_ms}
            )

            # Add tracking headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

            return response

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[{request_id}] Unhandled error: {str(e)}",
                exc_info=True,
                extra={"request_id": request_id, "duration_ms": duration_ms}
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global error handler that catches unhandled exceptions.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Invalid input",
                    "details": str(e),
                    "error_code": "VALIDATION_ERROR"
                }
            )
        except FileNotFoundError as e:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "Resource not found",
                    "details": str(e),
                    "error_code": "NOT_FOUND"
                }
            )
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Internal server error",
                    "details": str(e) if str(e) else "An unexpected error occurred",
                    "error_code": "INTERNAL_ERROR"
                }
            )


class RateLimitState:
    """Simple in-memory rate limit tracking (use Redis in production)"""

    def __init__(self):
        self.requests: dict = {}  # {ip: [(timestamp, count)]}
        self.window_seconds = 60
        self.max_requests = 30  # 30 requests per minute for AI endpoints

    def is_allowed(self, ip: str, endpoint: str) -> bool:
        """Check if request is allowed"""
        key = f"{ip}:{endpoint}"
        now = time.time()

        # Clean old entries
        if key in self.requests:
            self.requests[key] = [
                (ts, count) for ts, count in self.requests[key]
                if now - ts < self.window_seconds
            ]

        # Count requests in window
        current_count = sum(count for _, count in self.requests.get(key, []))

        if current_count >= self.max_requests:
            return False

        # Add new request
        if key not in self.requests:
            self.requests[key] = []
        self.requests[key].append((now, 1))

        return True


rate_limit_state = RateLimitState()


class AIRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting for AI-intensive endpoints.
    Protects against API abuse and cost overruns.
    """

    AI_ENDPOINTS = [
        "/api/v1/audit/council-session",
        "/api/v1/audit/deep-analysis",
        "/api/v1/audit/full-spectrum",
        "/api/v1/audit/patch-pack",
        # Legacy endpoints (to be deprecated)
        "/audit/council-session",
        "/audit/deep-analysis",
        "/audit/full-spectrum",
        "/audit/patch-pack",
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only rate limit AI endpoints
        if request.url.path not in self.AI_ENDPOINTS:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        # Check rate limit
        if not rate_limit_state.is_allowed(client_ip, request.url.path):
            logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "message": "Rate limit exceeded",
                    "details": "Too many AI analysis requests. Please wait before trying again.",
                    "error_code": "RATE_LIMIT_EXCEEDED"
                },
                headers={"Retry-After": "60"}
            )

        return await call_next(request)

