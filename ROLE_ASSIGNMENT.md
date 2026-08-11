# Phân công công việc nhóm — Day 13 Observability

Tài liệu này dùng để phân công 3 thành viên và kiểm tra tiến độ trước khi nộp bài.

> Thay `Thành viên 1`, `Thành viên 2`, `Thành viên 3` bằng tên thật của các thành viên.

## Tổng quan phân công

| Thành viên | Role | Phạm vi chính |
|---|---|---|
| Thành viên 1 | Logging & PII | Correlation ID, JSON log, metadata và che dữ liệu nhạy cảm |
| Thành viên 2 | Tracing & Prompt Version | Langfuse, trace, prompt v1/v2, label và rollback |
| Thành viên 3 | Dashboard, Incident & Report | Dashboard, SLO, alert, điều tra challenge và báo cáo |

---

## Role 1 — Logging & PII

### Mục tiêu

Đảm bảo mỗi request có thể truy vết được bằng `correlation_id`, log có đủ metadata và không làm lộ PII.

### File cần đọc

- `README.md`
- `CHECKPOINTS.md`
- `RULES.md`
- `SETUP.md`
- `docs/GUIDE.md`
- `config/logging_schema.json`
- Các test liên quan trong `tests/`

### File cần kiểm tra hoặc chỉnh sửa

- `app/middleware.py`
- `app/main.py`
- `app/logging_config.py`
- `app/pii.py`
- Có thể bổ sung test trong `tests/test_pii.py` và các test logging liên quan.

### Công việc chi tiết

1. Hoàn thiện correlation ID trong middleware:
   - Đọc `x-request-id` từ request nếu có.
   - Tạo ID mới nếu request không gửi ID.
   - Bind ID vào `structlog.contextvars`.
   - Xóa context sau khi request kết thúc để không bị leak sang request khác.
   - Trả correlation ID trong response header.
   - Trả thời gian xử lý trong response header nếu contract yêu cầu.

2. Bổ sung metadata vào log:
   - `user_id_hash`
   - `session_id`
   - `feature`
   - `model`
   - `env`

3. Hoàn thiện JSON logging:
   - Log đúng schema.
   - Các event chính phải có correlation ID.
   - Không ghi dữ liệu nhạy cảm nguyên văn.

4. Hoàn thiện PII redaction:
   - Email.
   - Số điện thoại.
   - Số thẻ thử nghiệm.
   - Kiểm tra thứ tự processor để PII được che trước khi render JSON.

5. Chạy kiểm tra:

```bash
python scripts/validate_logs.py
python -m pytest -q tests/test_pii.py tests/test_validate_logs.py
```

### Tiêu chí hoàn thành

- `validate_logs.py` đạt ít nhất `80/100`.
- Mỗi request có correlation ID hợp lệ.
- Log có đủ metadata bắt buộc.
- Không còn email, số điện thoại hoặc số thẻ nguyên văn trong log.
- Test liên quan chạy thành công.

### Evidence cần bàn giao

Lưu trong `submission/evidence/`:

- Kết quả cuối của `validate_logs.py`.
- Ảnh hoặc file log JSON có correlation ID.
- Ảnh hoặc file log chứng minh PII đã được redact.
- Nếu có, ảnh response header chứa correlation ID.

### Commit đề xuất

```text
feat: implement correlation id middleware
feat: add request metadata and pii redaction
test: cover logging and pii behavior
```

---

## Role 2 — Tracing & Prompt Version

### Mục tiêu

Tạo trace đầy đủ trên Langfuse và chứng minh hệ thống sử dụng được nhiều phiên bản prompt, có label và rollback.

### File cần đọc

- `README.md`
- `SETUP.md`
- `CHECKPOINTS.md`
- `RULES.md`
- `docs/PROMPT_VERSIONING.md`
- `docs/grading-evidence.md`

### File cần kiểm tra hoặc chỉnh sửa

- `app/tracing.py`
- `app/agent.py`
- `app/prompt_management.py`
- `app/mock_llm.py`
- `app/main.py` nếu cần kiểm tra metadata trace.
- Có thể bổ sung test trong `tests/test_agent_prompt_trace.py`, `tests/test_prompt_management.py` và `tests/test_tracing_adapter.py`.

### Công việc chi tiết

1. Cấu hình Langfuse trong `.env` local:
   - `LANGFUSE_PUBLIC_KEY`
   - `LANGFUSE_SECRET_KEY`
   - `LANGFUSE_HOST`
   - `LANGFUSE_PROMPT_NAME`
   - `LANGFUSE_PROMPT_LABEL`

   Không commit file `.env` hoặc API key.

2. Tạo tối thiểu 10 traces có metadata.

3. Kiểm tra trace có các trường:
   - `prompt_name`
   - `prompt_label`
   - `prompt_version`
   - `prompt_source`
   - `correlation_id`

4. Tạo hoặc cấu hình hai prompt version:
   - Prompt baseline, ví dụ `v1`.
   - Prompt candidate, ví dụ `v2`.

5. Chạy cùng một input với cả hai prompt version và lưu trace ID tương ứng.

6. Thực hiện một thao tác đổi label hoặc rollback.

7. Xác nhận trace sau thao tác hiển thị đúng prompt name, label và version.

8. Chạy test liên quan:

```bash
python -m pytest -q tests/test_agent_prompt_trace.py tests/test_prompt_management.py tests/test_tracing_adapter.py
```

### Tiêu chí hoàn thành

- Có ít nhất 10 trace thật trên Langfuse.
- Có trace waterfall đầy đủ.
- Có prompt v1 và v2.
- Trace hiển thị đúng name, label và version.
- Có bằng chứng đổi label hoặc rollback.
- Không hard-code version giả để vượt kiểm tra.

### Evidence cần bàn giao

Lưu trong `submission/evidence/`:

- Danh sách tối thiểu 10 trace ID.
- Ảnh một trace waterfall.
- Ảnh prompt version v1 và trace tương ứng.
- Ảnh prompt version v2 và trace tương ứng.
- Ảnh hoặc bằng chứng đổi label/rollback.
- Ghi chú ngắn giải thích span đáng chú ý nếu có.

### Commit đề xuất

```text
feat: configure tracing metadata
feat: add prompt version and label workflow
docs: add tracing evidence
```

---

## Role 3 — Dashboard, Incident & Report

### Mục tiêu

Xây dựng dashboard theo đúng contract, hoàn thiện SLO/alert/runbook, điều tra challenge và tổng hợp báo cáo nộp bài.

### File cần đọc

- `README.md`
- `CHECKPOINTS.md`
- `SUBMISSION.md`
- `RUBRIC.md`
- `docs/dashboard-spec.md`
- `docs/DASHBOARD_SETUP.md`
- `docs/grading-evidence.md`
- `docs/alerts.md`

### File cần kiểm tra hoặc chỉnh sửa

- `config/dashboard.yaml`
- `config/slo.yaml`
- `config/alert_rules.yaml`
- `docs/alerts.md`
- `scripts/validate_dashboard.py`
- `scripts/inject_incident.py`
- `scripts/load_test.py`
- `submission/REPORT.md`

### Công việc Dashboard

Dashboard phải có 6 nhóm thông tin:

1. Latency P50/P95/P99 từ `response_sent.latency_ms`.
2. Traffic từ event `request_received`.
3. Error rate và breakdown theo `error_type`.
4. Cost từ `response_sent.cost_usd`.
5. Tổng `tokens_in` và `tokens_out`.
6. Quality proxy từ `response_sent.quality_score`.

Yêu cầu trình bày:

- Time range 60 phút.
- Refresh 30 giây nếu công cụ hỗ trợ.
- Có đơn vị đo.
- Có threshold hoặc SLO line.
- Screenshot phải nhìn rõ panel và time range.

Chạy kiểm tra:

```bash
python scripts/validate_dashboard.py
```

Kết quả cần đạt:

```text
HỢP LỆ: 6/6 panel
```

### Công việc SLO, Alert và Runbook

- Kiểm tra SLO trong `config/slo.yaml`.
- Thay các giá trị `TODO` trong `config/alert_rules.yaml`.
- Tạo alert cho latency, error rate, cost hoặc quality.
- Mỗi alert cần có severity, condition, owner và runbook.
- Hoàn thiện hướng dẫn xử lý trong `docs/alerts.md`.

### Công việc điều tra challenge

File challenge chính thức là `config/challenge.json`. Không tự sửa file này.

Chạy:

```bash
python scripts/inject_incident.py
python scripts/load_test.py --challenge --concurrency 5
```

Điều tra theo thứ tự:

1. Dùng metrics xác định triệu chứng.
2. Mở trace bất thường trong khoảng thời gian đó.
3. Xác định span chậm hoặc lỗi.
4. Tìm log có cùng `correlation_id`.
5. Viết root cause dựa trên metric, trace và log.
6. Đề xuất fix action.
7. Đề xuất preventive measure.

### Công việc báo cáo

Hoàn thiện `submission/REPORT.md`, gồm:

- Thông tin nhóm.
- Repository URL.
- Commit SHA cuối.
- Điểm validator.
- Số lượng trace.
- Evidence logging, tracing và dashboard.
- SLO, alert và runbook.
- Challenge ID, triệu chứng, trace ID, log line, root cause, fix và preventive measure.
- Bảng đóng góp của cả 3 thành viên.

### Tiêu chí hoàn thành

- Validator dashboard đạt `6/6 panel`.
- Dashboard có đủ 6 nhóm chỉ số.
- Alert không còn `TODO`.
- Runbook đã hoàn thiện.
- Điều tra challenge có đủ metric, trace ID và log line.
- `REPORT.md` dẫn đúng evidence bằng đường dẫn tương đối.

### Evidence cần bàn giao

Lưu trong `submission/evidence/`:

- Kết quả `validate_dashboard.py`.
- Screenshot dashboard.
- Screenshot hoặc file SLO/alert/runbook.
- Metric thể hiện incident.
- Trace ID liên quan.
- Log line hoặc correlation ID liên quan.
- Evidence root cause và cách xử lý.

### Commit đề xuất

```text
feat: complete dashboard and alert configuration
docs: add incident runbook
docs: complete final submission report
```

---

## Checklist chung trước khi nộp

Mỗi thành viên cần:

- Có commit riêng trên GitHub.
- Ghi rõ phần việc và commit SHA trong `submission/REPORT.md`.
- Không commit `.env`, API key, secret, `.venv` hoặc PII.
- Chạy test và kiểm tra thay đổi của mình.
- Bàn giao evidence cho người phụ trách báo cáo.

Chạy các lệnh cuối:

```bash
python -m pytest -q
python scripts/validate_logs.py
python scripts/validate_dashboard.py
git status --short
```

Khi nộp bài, cần có:

- Repository URL.
- Commit SHA cuối.
- `submission/REPORT.md` đầy đủ.
- Evidence trong `submission/evidence/`.
- Dashboard và challenge evidence có thể kiểm chứng.

## Phân chia điểm liên quan đến các role

| Role | Phần điểm chính có thể chứng minh |
|---|---|
| Logging & PII | 10 điểm triển khai kỹ thuật + điểm cá nhân |
| Tracing & Prompt Version | 10 điểm triển khai kỹ thuật + điểm cá nhân |
| Dashboard, Incident & Report | 10 điểm dashboard + 10 điểm incident + hỗ trợ 20 điểm demo |

Điểm cá nhân vẫn phụ thuộc vào khả năng giải thích phần mình làm và commit/PR có thể kiểm tra trên GitHub.
