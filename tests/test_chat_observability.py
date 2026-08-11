from __future__ import annotations

import json
from pathlib import Path

import pytest
import structlog
from fastapi.testclient import TestClient

from app import logging_config
from app.main import app
from app.pii import hash_user_id

ENRICHMENT_FIELDS = {"correlation_id", "user_id_hash", "session_id", "feature", "model", "env"}


def read_events(log_path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def api_events(log_path: Path) -> list[dict]:
    return [event for event in read_events(log_path) if event.get("service") == "api"]


@pytest.fixture()
def log_path(monkeypatch, tmp_path: Path) -> Path:
    path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", path)
    structlog.contextvars.clear_contextvars()
    return path


def test_chat_response_log_exposes_quality_for_dashboard(log_path: Path) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "user_id": "student-01",
                "session_id": "session-01",
                "feature": "qa",
                "message": "Explain observability",
            },
        )

    assert response.status_code == 200
    events = read_events(log_path)
    response_event = next(event for event in events if event["event"] == "response_sent")
    assert response_event["quality_score"] == response.json()["quality_score"]


def test_request_logs_carry_full_metadata_and_hashed_user(log_path: Path) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "user_id": "student-01",
                "session_id": "session-01",
                "feature": "qa",
                "message": "Explain observability",
            },
        )

    assert response.status_code == 200
    events = api_events(log_path)
    assert {event["event"] for event in events} == {"request_received", "response_sent"}

    for event in events:
        assert ENRICHMENT_FIELDS.issubset(event.keys())
        assert event["user_id_hash"] == hash_user_id("student-01")
        assert event["session_id"] == "session-01"
        assert event["feature"] == "qa"
        assert event["model"]
        assert "student-01" not in json.dumps(event)

    response_event = next(event for event in events if event["event"] == "response_sent")
    assert isinstance(response_event["latency_ms"], int)


def test_incoming_x_request_id_is_reused_and_returned(log_path: Path) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/chat",
            headers={"x-request-id": "req-from-client-01"},
            json={
                "user_id": "student-01",
                "session_id": "session-01",
                "feature": "qa",
                "message": "Explain observability",
            },
        )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-from-client-01"
    assert float(response.headers["x-response-time-ms"]) >= 0
    assert response.json()["correlation_id"] == "req-from-client-01"
    assert {event["correlation_id"] for event in api_events(log_path)} == {"req-from-client-01"}


def test_missing_x_request_id_gets_a_generated_id_per_request(log_path: Path) -> None:
    payload = {
        "user_id": "student-01",
        "session_id": "session-01",
        "feature": "qa",
        "message": "Explain observability",
    }

    with TestClient(app) as client:
        first = client.post("/chat", json=payload)
        second = client.post("/chat", json=payload)

    first_id = first.json()["correlation_id"]
    second_id = second.json()["correlation_id"]

    assert first_id.startswith("req-") and len(first_id) == len("req-") + 8
    assert first_id != second_id, "correlation ID của request trước không được rò sang request sau"
    assert first.headers["x-request-id"] == first_id
    assert second.headers["x-request-id"] == second_id

    events = api_events(log_path)
    assert {event["correlation_id"] for event in events} == {first_id, second_id}
    # Mỗi request phải có đúng 2 log (received + sent) dùng chung một correlation ID.
    assert [event["correlation_id"] for event in events].count(first_id) == 2


def test_failed_request_logs_error_type_and_clears_context(log_path: Path, monkeypatch) -> None:
    from app import main

    def boom(**_: object) -> None:
        raise RuntimeError("Vector store timeout for alice@example.com")

    monkeypatch.setattr(main.agent, "run", boom)

    payload = {
        "user_id": "student-01",
        "session_id": "session-01",
        "feature": "qa",
        "message": "Explain observability",
    }

    with TestClient(app, raise_server_exceptions=False) as client:
        failed = client.post("/chat", json=payload)

    assert failed.status_code == 500
    assert failed.headers["x-request-id"]

    failed_event = next(
        event for event in api_events(log_path) if event["event"] == "request_failed"
    )
    assert failed_event["error_type"] == "RuntimeError"
    assert ENRICHMENT_FIELDS.issubset(failed_event.keys())
    assert "alice@example.com" not in json.dumps(failed_event)
    assert "REDACTED_EMAIL" in failed_event["payload"]["detail"]

    # Context phải sạch sau exception: không còn dữ liệu request nào bị bind lại.
    assert structlog.contextvars.get_contextvars() == {}


def test_pii_is_redacted_before_reaching_the_log_file(log_path: Path) -> None:
    message = "Mail alice@example.com, phone 0987654321, card 4111 1111 1111 1111"

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={
                "user_id": "student-02",
                "session_id": "session-02",
                "feature": "qa",
                "message": message,
            },
        )

    assert response.status_code == 200
    raw = log_path.read_text(encoding="utf-8")
    assert "alice@example.com" not in raw
    assert "0987654321" not in raw
    assert "4111 1111 1111 1111" not in raw

    preview = next(
        event for event in api_events(log_path) if event["event"] == "request_received"
    )["payload"]["message_preview"]
    assert "REDACTED_EMAIL" in preview
