# Yêu cầu dashboard

Contract có thể kiểm tra bằng máy nằm tại `config/dashboard.yaml`. Hướng dẫn dựng và kiểm tra runtime nằm tại [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md).

Dashboard chính cần đủ 6 nhóm thông tin:

1. Latency P50/P95/P99.
2. Traffic: request count hoặc QPS.
3. Error rate và breakdown theo loại lỗi.
4. Cost theo thời gian.
5. Tổng token input/output.
6. Quality proxy.

## Đặc tả triển khai

| Panel | Nguồn và phép tính | Đơn vị | Threshold/SLO line |
|---|---|---|---|
| Latency percentiles | `response_sent.latency_ms`; P50/P95/P99 | ms | P95 ≤ 3000 ms |
| Request traffic | đếm `request_received` theo phút | requests/min | ≥ 1 request/min khi chạy workload |
| Error rate and breakdown | `request_failed / request_received * 100`; nhóm theo `error_type` | % | error rate ≤ 2% |
| Cost over time | tổng `response_sent.cost_usd` theo phút và toàn cửa sổ | USD | tổng ≤ 2.5 USD |
| Input and output tokens | tổng riêng `tokens_in` và `tokens_out` | tokens | tổng từng field ≤ 50,000 |
| Quality proxy | trung bình `response_sent.quality_score` | score 0–1 | mean ≥ 0.75 |

Nguồn chuẩn là `data/logs.jsonl`; Langfuse dùng để mở trace liên quan khi một panel báo bất thường. Dashboard mặc định hiển thị 60 phút gần nhất và refresh 30 giây. Query thực thi trên công cụ dashboard phải giữ cùng logic với pseudocode trong `config/dashboard.yaml`.

Tiêu chuẩn trình bày:

- Khoảng thời gian mặc định: 1 giờ.
- Tự refresh mỗi 15–30 giây nếu công cụ hỗ trợ.
- Có threshold hoặc SLO line.
- Ghi rõ đơn vị.
- Chỉ giữ 6–8 panel quan trọng ở lớp chính.
- Screenshot phải nhìn được tên panel và khoảng thời gian.

Kiểm tra contract trước khi chụp evidence:

```bash
python scripts/validate_dashboard.py
```
