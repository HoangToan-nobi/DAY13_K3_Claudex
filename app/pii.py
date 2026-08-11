from __future__ import annotations

import hashlib
import re
from typing import Any

# Thứ tự pattern rất quan trọng: chuỗi dài/đặc thù phải được redact trước để
# pattern ngắn hơn không cắt nhỏ và làm lộ phần còn lại của cùng một giá trị PII.
#   email -> credit_card (13-19 chữ số) -> cccd (12 chữ số) -> phone_vn -> phone quốc tế
PII_PATTERNS: dict[str, str] = {
    "email": r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
    # Thẻ thử nghiệm: 13-19 chữ số, cho phép nhóm bằng khoảng trắng hoặc dấu gạch.
    "credit_card": r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)",
    "cccd": r"(?<!\d)\d{12}(?!\d)",
    # Số Việt Nam: 0xxxxxxxxx / +84xxxxxxxxx, chấp nhận khoảng trắng, dấu chấm, gạch.
    "phone_vn": r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)",
    # Số quốc tế dạng phổ biến: +1 415 555 0198, (415) 555-0198, 415.555.0198
    "phone": r"(?<!\d)(?:\+\d{1,3}[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)",
}

_COMPILED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (name, re.compile(pattern)) for name, pattern in PII_PATTERNS.items()
)


def scrub_text(text: str) -> str:
    """Che mọi PII đã biết trong một chuỗi, giữ nguyên phần văn bản còn lại."""
    safe = text
    for name, pattern in _COMPILED_PATTERNS:
        safe = pattern.sub(f"[REDACTED_{name.upper()}]", safe)
    return safe


def scrub_value(value: Any) -> Any:
    """Scrub đệ quy cho dict/list lồng nhau mà không đổi kiểu dữ liệu gốc.

    Chỉ nội dung chuỗi bị thay đổi; int/float/bool/None và các số liệu
    observability (latency_ms, tokens, cost...) được giữ nguyên tuyệt đối.
    """
    if isinstance(value, str):
        return scrub_text(value)
    if isinstance(value, dict):
        return {key: scrub_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [scrub_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(scrub_value(item) for item in value)
    if isinstance(value, set):
        return {scrub_value(item) for item in value}
    return value


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    """Hash ổn định cho cùng một user nhưng không thể suy ngược ra user ID.

    Tiền tố ``u_`` giữ cho giá trị luôn khác một dãy số thuần, tránh việc hash
    bị các detector PII (ví dụ CCCD 12 chữ số) nhận nhầm là dữ liệu nhạy cảm.
    """
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
    return f"u_{digest}"
