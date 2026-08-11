from __future__ import annotations

import re
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

REQUEST_ID_HEADER = "x-request-id"
RESPONSE_TIME_HEADER = "x-response-time-ms"

# Correlation ID đến từ client là input không tin cậy: chỉ nhận ký tự an toàn cho
# header/log và giới hạn độ dài, nếu không thì cấp ID mới.
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")


def new_correlation_id() -> str:
    """Sinh correlation ID mới theo format req-<8-char-hex> từ UUID4."""
    return f"req-{uuid.uuid4().hex[:8]}"


def resolve_correlation_id(incoming: str | None) -> str:
    """Giữ lại x-request-id hợp lệ của client, ngược lại cấp ID mới."""
    if incoming:
        candidate = incoming.strip()
        if _SAFE_REQUEST_ID.match(candidate):
            return candidate
    return new_correlation_id()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Dọn context trước khi bind để ID của request trước không rò sang request sau.
        clear_contextvars()

        correlation_id = resolve_correlation_id(request.headers.get(REQUEST_ID_HEADER))
        bind_contextvars(correlation_id=correlation_id)
        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            # Chạy cả ở nhánh thành công lẫn nhánh exception.
            clear_contextvars()

        response.headers[REQUEST_ID_HEADER] = correlation_id
        response.headers[RESPONSE_TIME_HEADER] = f"{elapsed_ms:.2f}"
        return response
