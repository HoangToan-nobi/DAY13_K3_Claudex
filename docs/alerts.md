# Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: `high_latency_p95`
- Severity: `warning`
- SLI/SLO liên quan: P95 latency không vượt quá 3000 ms; target 99.5% trong cửa sổ 28 ngày.
- Điều kiện và thời gian duy trì: `latency_p95_ms > 3000` liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: Phản hồi chat chậm, dễ timeout và làm giảm trải nghiệm trên mọi feature bị ảnh hưởng.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel Latency, xác định thời điểm bắt đầu và feature có P95/P99 tăng mạnh.
  2. Mở trace trong cùng khoảng thời gian, so sánh waterfall và xác định span chiếm phần lớn latency.
  3. Dùng `correlation_id` của trace để lọc `data/logs.jsonl`, kiểm tra event và metadata của request chậm.
- Mitigation tạm thời: Giảm concurrency hoặc traffic tới feature bị ảnh hưởng; vô hiệu incident/dependency lỗi nếu đã xác nhận; trả fallback response khi dependency vượt timeout.
- Owner: `on-call-engineer`

## Alert 2

- Tên: `elevated_error_rate`
- Severity: `critical`
- SLI/SLO liên quan: Error rate dưới 2%; target 99.0% trong cửa sổ 28 ngày.
- Điều kiện và thời gian duy trì: `error_rate_pct > 5` liên tục trong 3 phút.
- Ảnh hưởng tới người dùng: Request thất bại hoặc trả HTTP 500, người dùng không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel Errors và breakdown theo `error_type` để xác định loại lỗi chiếm ưu thế.
  2. Mở các trace lỗi trong khoảng thời gian cảnh báo, xác định span và feature liên quan.
  3. Lọc log bằng `correlation_id`, đối chiếu `request_received` với `request_failed` và nội dung lỗi đã được scrub PII.
- Mitigation tạm thời: Cô lập feature/dependency lỗi, bật fallback hoặc retry có giới hạn; rollback thay đổi gần nhất nếu bằng chứng cho thấy có liên quan.
- Owner: `on-call-engineer`

## Alert 3

- Tên: `cost_budget_exceeded`
- Severity: `warning`
- SLI/SLO liên quan: Tổng chi phí không vượt 2.5 USD/ngày; target 100% trong cửa sổ 28 ngày.
- Điều kiện và thời gian duy trì: `daily_cost_usd > 2.5`.
- Ảnh hưởng tới người dùng: Không nhất thiết gây lỗi ngay, nhưng có nguy cơ cạn ngân sách và phải giới hạn dịch vụ.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel Cost và Tokens để xác định thời điểm, feature và chiều token tăng bất thường.
  2. Mở trace có cost cao, kiểm tra model, prompt version và usage input/output.
  3. Dùng `correlation_id` đối chiếu log `response_sent`, xác nhận `cost_usd`, `tokens_in` và `tokens_out`.
- Mitigation tạm thời: Giới hạn output token/rate, chuyển sang model phù hợp hơn hoặc tạm thời vô hiệu feature gây tăng chi phí sau khi xác nhận.
- Owner: `team-lead`

## Nguyên tắc xử lý chung

Mọi kết luận incident phải lưu đủ thời điểm, giá trị metric, trace ID và log/correlation ID. Không ghi dữ liệu đầu vào chứa PII vào ticket hoặc evidence. Sau mitigation, chạy lại cùng workload để xác nhận chỉ số trở về dưới ngưỡng rồi mới đóng incident.
