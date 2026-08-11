from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import structlog
from structlog.contextvars import merge_contextvars

from .pii import scrub_value

LOG_PATH = Path(os.getenv("LOG_PATH", "data/logs.jsonl"))

# Các field do hệ thống observability sinh ra, không bao giờ chứa PII và không
# được phép biến dạng: timestamp, level, correlation ID hay user hash.
SAFE_KEYS = frozenset(
    {
        "ts",
        "timestamp",
        "level",
        "service",
        "env",
        "model",
        "correlation_id",
        "user_id_hash",
    }
)


class JsonlFileProcessor:
    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        rendered = structlog.processors.JSONRenderer()(logger, method_name, event_dict)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(rendered + "\n")
        return event_dict



def scrub_event(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Redact PII trên toàn bộ event trước khi render JSON.

    Chạy sau ``format_exc_info`` nên message, metadata lồng nhau và cả traceback
    của exception đều đi qua bộ lọc; không có đường nào ghi ra file mà bỏ qua nó.
    """
    for key, value in list(event_dict.items()):
        if key in SAFE_KEYS:
            continue
        event_dict[key] = scrub_value(value)
    return event_dict



def configure_logging() -> None:
    logging.basicConfig(format="%(message)s", level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # PII phải bị che trước khi bất kỳ sink nào (file hoặc console) nhận dữ liệu.
            scrub_event,
            JsonlFileProcessor(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )



def get_logger() -> structlog.typing.FilteringBoundLogger:
    return structlog.get_logger()
