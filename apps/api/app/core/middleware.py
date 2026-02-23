"""Demo gate and rate limit middleware."""

import json

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.rate_limit import RATE_LIMITS, PATH_TO_ROUTE, check_rate_limit

PUBLIC_PATHS = {"/", "/health", "/openapi.json", "/docs", "/redoc"}


def _path_matches_route(path: str) -> str | None:
    """Return route key if path is rate-limited."""
    path = path.rstrip("/") or "/"
    return PATH_TO_ROUTE.get(path)


class DemoGateMiddleware(BaseHTTPMiddleware):
    """Require x-demo-key header on non-public routes when DEMO_KEY is set."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.demo_key:
            return await call_next(request)

        path = (request.url.path or "/").rstrip("/") or "/"
        if path in PUBLIC_PATHS:
            return await call_next(request)

        key = request.headers.get("x-demo-key")
        if key != settings.demo_key:
            return Response(
                content='{"detail":"Missing or invalid x-demo-key header"}',
                status_code=401,
                media_type="application/json",
            )
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiting per IP and optional user_id."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        route = _path_matches_route(path)
        if not route:
            return await call_next(request)

        ip = request.client.host if request.client else "0.0.0.0"
        user_id = request.headers.get("x-user-id")

        limit, window_seconds = RATE_LIMITS[route]
        window_name = "hour" if window_seconds == 3600 else "day"

        allowed, retry_after = check_rate_limit(ip, path, user_id)

        if not allowed:
            body = json.dumps({
                "detail": "Rate limit exceeded",
                "retry_after_seconds": retry_after,
                "limit": limit,
                "window": window_name,
            })
            return Response(
                content=body,
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
