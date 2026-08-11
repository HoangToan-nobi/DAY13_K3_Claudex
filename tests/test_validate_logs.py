from __future__ import annotations

import json
from pathlib import Path

from scripts import validate_logs

BASE_RECORD = {
    "ts": "2026-08-10T00:00:00Z",
    "level": "info",
    "service": "api",
    "event": "request_received",
    "correlation_id": "req-12345678",
    "user_id_hash": "u_abc123def456",
    "session_id": "session-01",
    "feature": "monitoring",
    "model": "fake-llm",
    "env": "dev",
}


def write_records(log_path: Path, records: list[dict]) -> None:
    log_path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def test_validator_detects_raw_vietnamese_phone(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    log_path = tmp_path / "logs.jsonl"
    record = {
        "ts": "2026-08-10T00:00:00Z",
        "level": "info",
        "service": "api",
        "event": "request_received",
        "correlation_id": "req-12345678",
        "user_id_hash": "abc123",
        "session_id": "session-01",
        "feature": "monitoring",
        "model": "fake-llm",
        "payload": {"message_preview": "Contact 090 123 4567"},
    }
    log_path.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
    monkeypatch.setattr(validate_logs, "LOG_PATH", log_path)

    validate_logs.main()

    output = capsys.readouterr().out
    assert "Potential PII leaks detected: 1" in output
    assert "phone_vn" in output
    assert "[FAILED] PII scrubbing" in output


def test_validator_scores_full_marks_for_enriched_scrubbed_logs(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    log_path = tmp_path / "logs.jsonl"
    write_records(
        log_path,
        [
            {
                **BASE_RECORD,
                "correlation_id": "req-1a2b3c4d",
                "payload": {
                    "message_preview": (
                        "Mail [REDACTED_EMAIL], phone [REDACTED_PHONE_VN], "
                        "card [REDACTED_CREDIT_CARD]"
                    )
                },
            },
            {
                **BASE_RECORD,
                "event": "response_sent",
                "correlation_id": "req-5e6f7a8b",
                "latency_ms": 1534,
                "tokens_in": 220,
                "tokens_out": 130,
                "cost_usd": 0.0026,
                "quality_score": 0.9,
            },
        ],
    )
    monkeypatch.setattr(validate_logs, "LOG_PATH", log_path)

    validate_logs.main()

    output = capsys.readouterr().out
    assert "Potential PII leaks detected: 0" in output
    assert "Unique correlation IDs found: 2" in output
    assert "Estimated Score: 100/100" in output


def test_validator_detects_raw_card_number(monkeypatch, tmp_path: Path, capsys) -> None:
    log_path = tmp_path / "logs.jsonl"
    write_records(
        log_path,
        [{**BASE_RECORD, "payload": {"message_preview": "card 4111 1111 1111 1111"}}],
    )
    monkeypatch.setattr(validate_logs, "LOG_PATH", log_path)

    validate_logs.main()

    output = capsys.readouterr().out
    assert "credit_card" in output
    assert "[FAILED] PII scrubbing" in output
