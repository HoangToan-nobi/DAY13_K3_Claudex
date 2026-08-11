# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: `DAY13_2A202601273_HOANGSYTOAN`
- Repository URL: `https://github.com/HoangToan-nobi/DAY13_2A202601273_HOANGSYTOAN`
- Commit SHA cuối: `[CẦN BỔ SUNG SAU COMMIT CUỐI]`
- Thành viên và vai trò:
  - `Toàn` — Logging & PII
  - `plxgplxgplxg` — Tracing & Prompt Version
  - `dalex0512` — Dashboard, Incident & Report

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: `100/100` — [validation-results.txt](evidence/validation-results.txt)
- Tổng số traces: `[CHỜ EVIDENCE TỪ THÀNH VIÊN 2; yêu cầu ≥ 10]`
- Số PII leak còn lại: `0` theo validator và kiểm tra thủ công email/test card.
- Link/đường dẫn dashboard: [dashboard-runtime.svg](evidence/dashboard-runtime.svg) và [dashboard contract](../config/dashboard.yaml).

## 3. Logging và tracing

- Evidence correlation ID: [challenge-investigation.txt](evidence/challenge-investigation.txt) — `req-cd9d477f` và bốn request challenge liên quan.
- Evidence PII redaction: [validation-results.txt](evidence/validation-results.txt) — validator phát hiện `0` leak; kiểm tra `@` và test card `4111` đều `0` hit.
- Evidence trace waterfall: `[CHỜ THÀNH VIÊN 2 BÀN GIAO]`
- Giải thích một span đáng chú ý: Với challenge `rag_slow`, span retrieval cần thể hiện phần lớn mức tăng khoảng 2.5 giây. Cần đối chiếu nhận định này với waterfall Langfuse thật trước khi nộp.

## 4. Prompt versioning

- Prompt name: `[CHỜ THÀNH VIÊN 2]`
- Version/label baseline: `[CHỜ THÀNH VIÊN 2]`
- Version/label candidate: `[CHỜ THÀNH VIÊN 2]`
- Trace ID của mỗi version: `[CHỜ THÀNH VIÊN 2]`
- Bằng chứng đổi label hoặc rollback: `[CHỜ THÀNH VIÊN 2]`

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.` — [validation-results.txt](evidence/validation-results.txt)
- Evidence dashboard: [dashboard-runtime.svg](evidence/dashboard-runtime.svg), được render từ `data/logs.jsonl` với time range 60 phút, đủ đơn vị và threshold.
- SLO đã chọn và lý do: P95 ≤ 3000 ms (99.5%), error rate ≤ 2% (99.0%), daily cost ≤ 2.5 USD (100%) và quality trung bình ≥ 0.75 (95%) trong cửa sổ 28 ngày. Các ngưỡng cân bằng trải nghiệm phản hồi, độ tin cậy, ngân sách và chất lượng; đồng thời khớp threshold trên dashboard.
- Alert rules và runbook: `../config/alert_rules.yaml` và `../docs/alerts.md`. Ba cảnh báo symptom-based bao phủ latency, error rate và chi phí.

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`
- Triệu chứng từ metrics: Baseline P95 `151 ms`; sau challenge P95 `2652 ms`, tăng `2501 ms` (~17.56 lần) và vượt threshold `2000 ms`. Error/cost/quality không tăng bất thường tương ứng.
- Trace ID liên quan: Chạy script `scripts/generate_traces.py` với Langfuse key trong `.env` để sinh trace, sau đó điền Trace ID từ Langfuse dashboard tương ứng với request bị chậm (latency ~2650ms) vào đây.
- Log line/correlation ID liên quan: `req-cd9d477f`, `response_sent.latency_ms=2652`; chi tiết cả năm request tại [challenge-investigation.txt](evidence/challenge-investigation.txt).
- Root cause: Challenge chính thức bật `rag_slow`; nhánh incident trong `retrieve()` thêm delay 2.5 giây. Mức delay này khớp log 2651–2652 ms trên cả năm request `refund`, trong khi cost và quality gần baseline.
- Fix action: Tắt đường dependency lỗi, áp timeout nghiêm ngặt cho retrieval và trả fallback an toàn khi vượt latency budget.
- Preventive measure: Thêm child span cho retrieval/generation, dependency latency metric, circuit breaker và test timeout; giữ alert P95 và chạy lại cùng workload để xác nhận phục hồi.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| `Toàn` | Correlation ID, JSON logging, metadata và PII redaction | `e931dc3` | Bảo toàn context request và scrub PII trước khi ghi log. |
| `plxgplxgplxg` | Trace correlation metadata và test liên quan | `f06f615` | Liên kết correlation ID giữa log và trace. |
| `dalex0512` | Dashboard contract/spec, SLO, alerts, runbook, incident và tổng hợp report | `97cc025`; `[SHA PHẦN HOÀN THIỆN NÀY SAU COMMIT]` | Thiết kế alert theo triệu chứng và điều tra theo Metrics → Traces → Logs. |

## 8. Checklist evidence còn thiếu trước khi nộp

- [x] Kết quả cuối `validate_logs.py` và kiểm tra PII.
- [ ] Danh sách ≥ 10 traces, waterfall và prompt version/rollback từ Thành viên 2.
- [x] Dashboard runtime đủ 6 panel, time range 60 phút, đơn vị và threshold.
- [ ] Metric trước/sau challenge và log đã có; còn thiếu trace ID Langfuse cùng request.
- [ ] Repository URL, tên thành viên, commit/PR và commit SHA cuối.
