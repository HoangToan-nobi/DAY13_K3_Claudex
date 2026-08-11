from app.pii import hash_user_id, scrub_text, scrub_value


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_international_phone_formats() -> None:
    phone_numbers = (
        "+1 415 555 0198",
        "(415) 555-0198",
        "415.555.0198",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Call {phone_number} now")
        assert phone_number not in out
        assert "REDACTED_PHONE" in out


def test_scrub_test_card_numbers_between_13_and_19_digits() -> None:
    cards = (
        "4111 1111 1111 1111",
        "4111111111111111",
        "4111-1111-1111-1111",
        "4222222222222",  # 13 chữ số
        "4111111111111111111",  # 19 chữ số
    )

    for card in cards:
        out = scrub_text(f"card {card} end")
        assert card not in out
        assert "REDACTED_CREDIT_CARD" in out


def test_scrub_keeps_observability_numbers_intact() -> None:
    safe = "latency_ms=1534 tokens_in=220 cost_usd=0.0031 ts=2026-08-11T02:46:03.850723Z"
    assert scrub_text(safe) == safe
    assert "REDACTED" not in scrub_text("correlation_id=req-1a2b3c4d level=info")


def test_scrub_value_handles_nested_structures_without_changing_types() -> None:
    payload = {
        "message": "mail bob@example.com",
        "latency_ms": 1200,
        "quality_score": 0.9,
        "enabled": True,
        "missing": None,
        "contacts": [
            {"phone": "0901234567"},
            ["card 4111 1111 1111 1111"],
        ],
    }

    out = scrub_value(payload)

    assert out["latency_ms"] == 1200
    assert out["quality_score"] == 0.9
    assert out["enabled"] is True
    assert out["missing"] is None
    assert "REDACTED_EMAIL" in out["message"]
    assert "REDACTED_PHONE_VN" in out["contacts"][0]["phone"]
    assert "REDACTED_CREDIT_CARD" in out["contacts"][1][0]
    assert isinstance(out["contacts"][1], list)


def test_hash_user_id_is_stable_and_hides_the_raw_id() -> None:
    hashed = hash_user_id("u_team_01")

    assert hashed == hash_user_id("u_team_01")
    assert hashed != hash_user_id("u_team_02")
    assert "u_team_01" not in hashed
    # Không bao giờ là dãy số thuần nên detector CCCD/thẻ không bắt nhầm hash.
    assert hashed.startswith("u_")
    assert "REDACTED" not in scrub_text(hashed)
