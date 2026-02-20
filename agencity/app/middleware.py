"""
Request ID middleware for Agencity.

Generates a unique request ID per request, attaches it to logs and response headers.
"""

import uuid
import logging
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable for request ID (accessible from anywhere in the call stack)
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Use incoming header or generate a short ID
        req_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:8])
        request_id_var.set(req_id)

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
