# HƯỚNG DẪN CHI TIẾT: APPLICATION LOG ANALYZER MCP SERVER

Tài liệu hướng dẫn triển khai, cài đặt và kiểm thử toàn diện giải pháp tích hợp công cụ qua giao thức **Model Context Protocol (MCP)** cho cả 3 cấp độ: **Bài 1 (Dễ)**, **Bài 2 (Trung bình)** và **Bài 3 (Khó)**.

---

## 1. Mô tả Bài toán Thực tế Giải quyết

* **Nghiệp vụ thực tế**: Trong vận hành hệ thống microservices hàng ngày, kỹ sư DevOps / SRE thường phải mở thủ công các file log lớn, dùng lệnh `grep` để tìm kiếm lỗi (`ERROR`, `CRITICAL`), truy vết nguyên nhân sự cố và phân tích stack trace của từng dịch vụ (`api-gateway`, `auth-service`, `order-service`, `payment-service`, `inventory-service`, `worker-service`).
* **Giải pháp MCP Server**: Tự động hóa toàn bộ quy trình này bằng cách biến thao tác đọc, lọc và chẩn đoán log thành các **MCP Tools**. AI Agent (như Claude Code hoặc Chatbot CLI) có thể tự động truy vấn dữ liệu log theo ngữ cảnh, bóc tách stack trace và đề xuất hướng xử lý sự cố.
* **Nguồn dữ liệu thực tế**: File [`data/app.log`](data/app.log) chứa các bản ghi log microservices kèm các khối lỗi Python đa dòng.

---

## 2. Mô tả Chi tiết Input / Output của từng MCP Tool

### Tool 1: `get_recent_errors` (Phiên bản v1 - stdio & HTTP)
Lấy danh sách các lỗi nghiêm trọng (`ERROR`, `CRITICAL`) gần đây nhất từ file log kèm toàn bộ khối stack trace.

* **Input Parameters**:
  | Tham số | Kiểu dữ liệu | Bắt buộc | Mặc định | Mô tả |
  |---|---|---|---|---|
  | `limit` | `integer` | Không | `5` | Số lượng bản ghi lỗi gần nhất cần trích xuất |
  | `service` | `string` | Không | `"ALL"` | Tên microservice cần lọc (`"order-service"`, `"payment-service"`,... hoặc `"ALL"`) |

* **Output Format**: Chuỗi văn bản (`string`) tổng hợp danh sách lỗi và chi tiết traceback:
  ```text
  === [Auth Verified] 2 lỗi gần nhất ===
  [1] 2026-08-28 17:06:52 | ERROR | api-gateway | Trace: req-015a8b
      [2026-08-28 17:06:52] [ERROR] [api-gateway] [req-015a8b] SchemaValidationError: Missing required field 'customer_email'
      Traceback (most recent call last):
        File "/app/middleware/validator.py", line 32, in validate_body
        ...
  ```

---

### Tool 2: `search_logs` (Tìm kiếm log tổng quát)
Tìm kiếm các bản ghi log theo từ khóa bất kỳ (Trace ID, User ID, tên Exception, IP, SKU) và lọc theo cấp độ log.

* **Input Parameters**:
  | Tham số | Kiểu dữ liệu | Bắt buộc | Mặc định | Mô tả |
  |---|---|---|---|---|
  | `keyword` | `string` | **Có** | - | Từ khóa cần tra cứu trong nội dung log |
  | `level` | `string` | Không | `"ALL"` | Cấp độ log cần lọc: `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`, hoặc `"ALL"` |
  | `limit` | `integer` | Không | `20` | Số lượng bản ghi tối đa trả về |

* **Output Format**: Chuỗi văn bản (`string`) liệt kê các dòng log khớp từ khóa.

---

### Tool 3: `get_recent_errors_v2` (Phiên bản v2 - Structured JSON)
Phiên bản nâng cấp trả về dữ liệu có cấu trúc JSON, tự động bóc tách loại Exception (`error_type`) và gợi ý hành động khắc phục (`suggested_action`).

* **Input Parameters**:
  | Tham số | Kiểu dữ liệu | Bắt buộc | Mặc định | Mô tả |
  |---|---|---|---|---|
  | `limit` | `integer` | Không | `5` | Số lượng lỗi cần lấy |
  | `service` | `string` | Không | `"ALL"` | Lọc theo microservice |
  | `include_traceback` | `boolean` | Không | `True` | Có bao gồm mảng stack trace hay không |
  | `format` | `string` | Không | `"json"` | Định dạng dữ liệu (`"json"` hoặc `"summary"`) |

* **Output Format**: Chuỗi JSON có cấu trúc (`Structured JSON`):
  ```json
  {
    "api_version": "2.0",
    "timestamp": "2026-08-28T10:45:11.495260+00:00",
    "total_errors_in_log": 5,
    "returned_count": 1,
    "service_filter": "ALL",
    "errors": [
      {
        "timestamp": "2026-08-28 17:06:52",
        "severity": "ERROR",
        "service": "api-gateway",
        "trace_id": "req-015a8b",
        "error_type": "SchemaValidationError",
        "message": "SchemaValidationError: Missing required field 'customer_email'",
        "suggested_action": "Kiểm tra payload request của API client, đảm bảo đầy đủ các field required.",
        "stack_trace": [
          "Traceback (most recent call last):",
          "  File \"/app/middleware/validator.py\", line 32, in validate_body"
        ]
      }
    ]
  }
  ```

---

## 3. Hướng dẫn Đăng ký MCP Server với Claude Code

Để tích hợp công cụ phân tích log này trực tiếp vào Claude Code trên máy tính của bạn:

### Bước 1: Chạy lệnh đăng ký MCP Server
Mở terminal và chạy lệnh sau (thay đường dẫn tuyệt đối tới file `log_server.py` trên máy của bạn):

```bash
claude mcp add log-analyzer -- python "c:/Users/USER/Desktop/Vin/Day26-MCP-Tools-Integration/lab-solution/01-stdio/log_server.py"
```

### Bước 2: Kiểm tra trong Claude Code
Khởi động Claude Code và kiểm tra danh sách công cụ:
```bash
claude
/mcp
```
*(Bạn sẽ thấy 2 công cụ `get_recent_errors` và `search_logs` đã sẵn sàng hoạt động).*

### Bước 3: Đặt câu hỏi tự nhiên để Claude Code tự gọi tool
* *"Tìm cho tôi 3 lỗi gần nhất trong file log hệ thống và phân tích nguyên nhân."*
* *"Kiểm tra xem user `usr_1042` đã gặp vấn đề gì khi đặt đơn hàng?"*
* *"Hôm nay hệ thống có bị lỗi kết nối cơ sở dữ liệu PostgreSQL hay không?"*

---

## 4. Hướng dẫn Cài đặt & Kiểm thử từng Cấp độ

### Chuẩn bị môi trường:
```bash
# Kích hoạt môi trường ảo
.venv\Scripts\Activate.ps1

# Cài đặt dependencies (nếu chưa có)
pip install -r lab-solution/requirements.txt
```

---

### 4.1. Bài 1 (Dễ): MCP Server qua `stdio`
* **Server**: [`01-stdio/log_server.py`](01-stdio/log_server.py)
* **Kiểm thử giao thức stdio (Không cần API key)**:
  ```bash
  python lab-solution/01-stdio/test_client.py
  ```
* **Trò chuyện với AI Chatbot CLI (Tích hợp Gemini 2.5 Flash)**:
  1. Cấu hình API key trong file `.env`: `GEMINI_API_KEY=AIzaSy...`
  2. Khởi chạy:
     ```bash
     python lab-solution/01-stdio/chat_client.py
     ```

---

### 4.2. Bài 2 (Trung bình): Streamable HTTP + Authentication
* **Server**: [`02-auth/auth_log_server.py`](02-auth/auth_log_server.py)
* **Quy trình kiểm thử 3 kịch bản bảo mật**:
  * **Cửa sổ Terminal 1** (Khởi động Auth Server):
    ```bash
    python lab-solution/02-auth/auth_log_server.py
    ```
  * **Cửa sổ Terminal 2** (Chạy Client Test Suite):
    ```bash
    python lab-solution/02-auth/test_auth_client.py
    ```
* **Kịch bản được chứng minh**:
  1. Token đúng (`Bearer log-reader-secret-token-2026`): 200 OK, gọi tool thành công.
  2. Token sai (`Bearer invalid-token-xyz-12345`): 401 Unauthorized.
  3. Thiếu Token: 401 Unauthorized.
* **File bằng chứng kiểm thử thực tế**: [`02-auth/auth_test_results.json`](02-auth/auth_test_results.json).

---

### 4.3. Bài 3 (Khó): Versioning & Backward Compatibility
* **Server v2**: [`03-versioning/versioned_log_server.py`](03-versioning/versioned_log_server.py)
  * Khai báo Resource `server://info` công bố metadata v2.0.0, danh sách deprecated tools và migration guide.
  * Hỗ trợ đồng thời Tool v1 (plain text) và Tool v2 (Structured JSON).
* **Kiểm thử tự động cả Legacy Client và Modern Client**:
  ```bash
  python lab-solution/03-versioning/modern_client.py
  ```
* **Kết quả**:
  * `legacy_client.py`: Gọi tool v1 thành công, nhận text string (không bị break code).
  * `modern_client.py`: Đọc metadata từ `server://info`, phát hiện v1 deprecated và tự động gọi v2 JSON.
* **File bằng chứng kiểm thử thực tế**: [`03-versioning/versioning_test_results.json`](03-versioning/versioning_test_results.json).

---

## 5. Bảng Checklist Nghiệm thu Toàn diện

| Tiêu chí | Cấp độ | Trạng thái | Minh chứng |
|---|---|---|---|
| MCP Server stdio + 2 tools tự xây | Bài 1 (Dễ) | ĐÃ ĐẠT | [`01-stdio/test_client.py`](01-stdio/test_client.py) |
| Đọc log thực tế, xử lý stack trace đa dòng | Bài 1 (Dễ) | ĐÃ ĐẠT | [`data/app.log`](data/app.log) |
| AI Chatbot CLI tích hợp Gemini 2.5 Flash | Bài 1 (Dễ) | ĐÃ ĐẠT | [`01-stdio/chat_client.py`](01-stdio/chat_client.py) |
| Hướng dẫn đăng ký Claude Code | Bài 1 (Dễ) | ĐÃ ĐẠT | Mục 3 trong README |
| Server Streamable HTTP (`0.0.0.0:8000/mcp`) | Bài 2 (Trung bình) | ĐÃ ĐẠT | [`02-auth/auth_log_server.py`](02-auth/auth_log_server.py) |
| Bearer Token Authentication (3/3 test cases) | Bài 2 (Trung bình) | ĐÃ ĐẠT | [`02-auth/auth_test_results.json`](02-auth/auth_test_results.json) |
| Resource `server://info` chứa metadata | Bài 3 (Khó) | ĐÃ ĐẠT | [`03-versioning/versioned_log_server.py`](03-versioning/versioned_log_server.py) |
| Backward compatibility (v1 + v2 song song) | Bài 3 (Khó) | ĐÃ ĐẠT | [`03-versioning/legacy_client.py`](03-versioning/legacy_client.py) |
| Modern Client đọc metadata & gọi v2 JSON | Bài 3 (Khó) | ĐÃ ĐẠT | [`03-versioning/versioning_test_results.json`](03-versioning/versioning_test_results.json) |
| An toàn bảo mật (Không đưa secret lên repo) | Tất cả | ĐÃ ĐẠT | `.gitignore` chặn `.env`, chỉ đẩy `.env.example` |
