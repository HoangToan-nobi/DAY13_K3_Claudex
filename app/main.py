from __future__ import annotations

import os
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from structlog.contextvars import bind_contextvars, clear_contextvars

from .agent import LabAgent
from .incidents import disable, enable, status
from .logging_config import configure_logging, get_logger
from .metrics import record_error, snapshot
from .middleware import CorrelationIdMiddleware, new_correlation_id
from .pii import hash_user_id, summarize_text
from .schemas import ChatRequest, ChatResponse
from .tracing import tracing_enabled

configure_logging()
log = get_logger()
app = FastAPI(title="Day 13 Observability Lab")
app.add_middleware(CorrelationIdMiddleware)
agent = LabAgent()


def current_env() -> str:
    return os.getenv("APP_ENV", "dev")


@app.on_event("startup")
async def startup() -> None:
    log.info(
        "app_started",
        service=os.getenv("APP_NAME", "day13-observability-lab"),
        env=current_env(),
        correlation_id="startup",
        payload={"tracing_enabled": tracing_enabled()},
    )


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "tracing_enabled": tracing_enabled(), "incidents": status()}


@app.get("/metrics")
async def metrics() -> dict:
    return snapshot()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    # Correlation ID do middleware cấp; fallback chỉ dùng khi handler được gọi
    # ngoài luồng HTTP (unit test gọi trực tiếp) để log không bao giờ mất ID.
    correlation_id = getattr(request.state, "correlation_id", None) or new_correlation_id()
    request.state.correlation_id = correlation_id

    # Bind trước dòng request_received để mọi log của request cùng mang metadata này.
    bind_contextvars(
        correlation_id=correlation_id,
        user_id_hash=hash_user_id(body.user_id),
        session_id=body.session_id,
        feature=body.feature,
        model=agent.model,
        env=current_env(),
    )
    started = time.perf_counter()
    try:
        log.info(
            "request_received",
            service="api",
            payload={"message_preview": summarize_text(body.message)},
        )
        try:
            result = agent.run(
                user_id=body.user_id,
                feature=body.feature,
                session_id=body.session_id,
                message=body.message,
            )
            log.info(
                "response_sent",
                service="api",
                latency_ms=result.latency_ms,
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
                cost_usd=result.cost_usd,
                quality_score=result.quality_score,
                payload={"answer_preview": summarize_text(result.answer)},
            )
            return ChatResponse(
                answer=result.answer,
                correlation_id=correlation_id,
                latency_ms=result.latency_ms,
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
                cost_usd=result.cost_usd,
                quality_score=result.quality_score,
            )
        except Exception as exc:
            error_type = type(exc).__name__
            record_error(error_type)
            log.error(
                "request_failed",
                service="api",
                error_type=error_type,
                latency_ms=int((time.perf_counter() - started) * 1000),
                payload={"detail": str(exc), "message_preview": summarize_text(body.message)},
            )
            raise HTTPException(status_code=500, detail=error_type) from exc
    finally:
        # Context của request phải được dọn ở cả nhánh thành công lẫn exception.
        clear_contextvars()


@app.post("/incidents/{name}/enable")
async def enable_incident(name: str) -> JSONResponse:
    try:
        enable(name)
        log.warning("incident_enabled", service="control", env=current_env(), payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/incidents/{name}/disable")
async def disable_incident(name: str) -> JSONResponse:
    try:
        disable(name)
        log.warning("incident_disabled", service="control", env=current_env(), payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
