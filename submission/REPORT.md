# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: `[CẦN NHÓM BỔ SUNG]`
- Repository URL: `[CẦN BỔ SUNG SAU KHI PUSH]`
- Commit SHA cuối: `[CẦN BỔ SUNG SAU COMMIT CUỐI]`
- Thành viên và vai trò:
  - `[THÀNH VIÊN 1]` — Logging & PII
  - `[THÀNH VIÊN 2]` — Tracing & Prompt Version
  - `[THÀNH VIÊN 3]` — Dashboard, Incident & Report

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: `[CHỜ EVIDENCE TỪ THÀNH VIÊN 1]`
- Tổng số traces: `[CHỜ EVIDENCE TỪ THÀNH VIÊN 2; yêu cầu ≥ 10]`
- Số PII leak còn lại: `[CHỜ KẾT QUẢ KIỂM TRA CUỐI]`
- Link/đường dẫn dashboard: `../config/dashboard.yaml`; `[BỔ SUNG ẢNH RUNTIME TRONG evidence/]`

## 3. Logging và tracing

- Evidence correlation ID: `[CHỜ THÀNH VIÊN 1 BÀN GIAO]`
- Evidence PII redaction: `[CHỜ THÀNH VIÊN 1 BÀN GIAO]`
- Evidence trace waterfall: `[CHỜ THÀNH VIÊN 2 BÀN GIAO]`
- Giải thích một span đáng chú ý: `[ĐIỀN THEO TRACE THẬT; KHÔNG SUY ĐOÁN]`

## 4. Prompt versioning

- Prompt name: `[CHỜ THÀNH VIÊN 2]`
- Version/label baseline: `[CHỜ THÀNH VIÊN 2]`
- Version/label candidate: `[CHỜ THÀNH VIÊN 2]`
- Trace ID của mỗi version: `[CHỜ THÀNH VIÊN 2]`
- Bằng chứng đổi label hoặc rollback: `[CHỜ THÀNH VIÊN 2]`

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Evidence dashboard: `evidence/dashboard-runtime.png` `[CẦN CHỤP TỪ DASHBOARD RUNTIME]`
- SLO đã chọn và lý do: P95 ≤ 3000 ms (99.5%), error rate ≤ 2% (99.0%), daily cost ≤ 2.5 USD (100%) và quality trung bình ≥ 0.75 (95%) trong cửa sổ 28 ngày. Các ngưỡng cân bằng trải nghiệm phản hồi, độ tin cậy, ngân sách và chất lượng; đồng thời khớp threshold trên dashboard.
- Alert rules và runbook: `../config/alert_rules.yaml` và `../docs/alerts.md`. Ba cảnh báo symptom-based bao phủ latency, error rate và chi phí.

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`
- Triệu chứng từ metrics: `[CHỜ CHẠY CHALLENGE VÀ GHI GIÁ TRỊ BASELINE/INCIDENT THẬT]`
- Trace ID liên quan: `[CHỜ TRACE THẬT TỪ LANGFUSE]`
- Log line/correlation ID liên quan: `[CHỜ LOG THẬT CÙNG TRACE]`
- Root cause: `[CHỈ KẾT LUẬN SAU KHI ĐỐI CHIẾU METRIC → TRACE → LOG]`
- Fix action: `[ĐIỀN THEO ROOT CAUSE ĐÃ CHỨNG MINH]`
- Preventive measure: `[ĐIỀN THEO ROOT CAUSE ĐÃ CHỨNG MINH]`

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| `[THÀNH VIÊN 1]` | Correlation ID, JSON logging, metadata và PII redaction | `[CHỜ SHA/PR]` | `[THÀNH VIÊN 1 BỔ SUNG]` |
| `[THÀNH VIÊN 2]` | Langfuse tracing, prompt v1/v2, label và rollback | `[CHỜ SHA/PR]` | `[THÀNH VIÊN 2 BỔ SUNG]` |
| `[THÀNH VIÊN 3]` | Dashboard contract/spec, SLO, alerts, runbook, incident và tổng hợp report | `[BỔ SUNG SHA/PR SAU COMMIT]` | Thiết kế alert theo triệu chứng và điều tra theo Metrics → Traces → Logs. |

## 8. Checklist evidence còn thiếu trước khi nộp

- [ ] Kết quả cuối `validate_logs.py` và log đã redact từ Thành viên 1.
- [ ] Danh sách ≥ 10 traces, waterfall và prompt version/rollback từ Thành viên 2.
- [ ] Ảnh dashboard runtime đủ 6 panel, time range 60 phút, đơn vị và threshold.
- [ ] Metric trước/sau challenge, trace ID và log có cùng correlation ID.
- [ ] Repository URL, tên thành viên, commit/PR và commit SHA cuối.
