# BÁO CÁO KỸ THUẬT: TÍCH HỢP CÔNG CỤ QUA GIAO THỨC MODEL CONTEXT PROTOCOL (MCP)

---

## 1. Bối cảnh và Lựa chọn Bài toán

* **Công việc lựa chọn**: Đọc, trích xuất và phân tích log hệ thống từ môi trường microservices (`Application Log Analyzer`).
* **Lý do lựa chọn**:
  * Việc tra cứu log thủ công hàng ngày để tìm nguyên nhân sự cố thường tốn thời gian, đặc biệt khi log có nhiều microservices và chứa traceback nhiều dòng.
  * Tác vụ có input rõ ràng (từ khóa, cấp độ log, số lượng dòng, tên service) và output rõ ràng (nội dung log, stack trace, phân tích lỗi).
* **Dữ liệu thực nghiệm**: File log `lab-solution/data/app.log` chứa các bản ghi log từ 6 microservices (`api-gateway`, `auth-service`, `order-service`, `payment-service`, `inventory-service`, `worker-service`) với các mức độ INFO, WARNING, ERROR, CRITICAL và các khối Python traceback đa dòng.

---

## 2. Chi tiết Triển khai và Kết quả Thực nghiệm

### 2.1. Bài 1 (Dễ): MCP Server qua giao thức `stdio`

#### Các phần đã thực hiện:
* Xây dựng `lab-solution/01-stdio/log_server.py` sử dụng class `MCPServer`/`FastMCP` của MCP SDK.
* Cung cấp 2 công cụ (tools):
  * `get_recent_errors(limit, service)`: Lọc các bản ghi ERROR và CRITICAL gần nhất kèm toàn bộ khối stack trace liên quan.
  * `search_logs(keyword, level, limit)`: Tìm kiếm log theo từ khóa (trace ID, user ID, tên lỗi) và lọc theo mức độ log.
* Viết parser đa dòng sử dụng Regular Expression để gom toàn bộ các dòng traceback thuộc về một bản ghi log thay vì tách rời từng dòng đơn lẻ.
* Xây dựng `test_client.py` (kiểm thử giao thức stdio) và `chat_client.py` (chatbot CLI kết nối MCP Server với mô hình `gemini-2.5-flash`).

#### Kết quả đạt được:
* MCP Server khởi động và giao tiếp ổn định qua kênh `stdio`.
* Khi client gửi yêu cầu `list_tools`, server trả về đầy đủ metadata và schema tham số của 2 công cụ.
* `chat_client.py` tự động chuyển đổi schema từ MCP sang `FunctionDeclaration` của Gemini SDK. Khi người dùng đặt câu hỏi tự nhiên, mô hình đưa ra quyết định gọi tool phù hợp, nhận dữ liệu log từ server và giải thích nguyên nhân sự cố.

#### Giải thích kỹ thuật (Tại sao lại như vậy):
* Giao thức `stdio` sử dụng hai luồng `stdin`/`stdout` chuẩn để trao đổi thông điệp JSON-RPC giữa tiến trình client và server trên cùng một máy chủ, không cần mở cổng mạng.
* Việc gom nhóm các dòng stack trace vào cùng một `LogEntry` giúp mô hình AI có đầy đủ ngữ cảnh của lỗi (nguyên nhân, file nguồn, số dòng phát sinh lỗi) thay vì chỉ nhận được dòng thông báo lỗi ban đầu.

---

### 2.2. Bài 2 (Trung bình): Streamable HTTP và Xác thực Bearer Token

#### Các phần đã thực hiện:
* Xây dựng `lab-solution/02-auth/auth_log_server.py` chạy trên transport `streamable-http`, lắng nghe tại cổng `http://0.0.0.0:8000/mcp`.
* Tích hợp lớp `StaticTokenVerifier` (kế thừa từ `TokenVerifier` của MCP SDK) và cấu hình `AuthSettings` để kiểm tra Bearer Token trong header `Authorization`.
* Xây dựng `test_auth_client.py` kiểm thử tự động 3 kịch bản bảo mật và lưu kết quả vào file `auth_test_results.json`.

#### Kết quả đạt được:
* **Kịch bản 1 (Token hợp lệ - `Bearer log-reader-secret-token-2026`)**: Server xác thực thành công, trả về HTTP 200/202, client đọc được danh sách công cụ và thực thi tool `get_recent_errors` bình thường.
* **Kịch bản 2 (Token không hợp lệ - `Bearer invalid-token-xyz-12345`)**: Server từ chối yêu cầu và phản hồi mã lỗi HTTP 401 Unauthorized.
* **Kịch bản 3 (Không truyền header Authorization)**: Server chặn kết nối ở tầng transport và phản hồi mã lỗi HTTP 401 Unauthorized.
* Toàn bộ log của server và phản hồi của client được ghi nhận thực tế trong file `lab-solution/02-auth/auth_test_results.json`.

#### Giải thích kỹ thuật (Tại sao lại như vậy):
* Khi MCP Server phục vụ qua giao thức HTTP, bất kỳ client nào có kết nối mạng đều có thể gửi request. Cơ chế xác thực Bearer Token giúp kiểm soát quyền truy cập trước khi phiên làm việc (session) của MCP được khởi tạo.
* MCP SDK xử lý việc xác thực tại tầng middleware của transport (HTTP layer), do đó logic nghiệp vụ của các tool bên trong không cần phải tự kiểm tra token.

---

### 2.3. Bài 3 (Khó): Quản lý Phiên bản (Versioning) và Tương thích ngược (Backward Compatibility)

#### Các phần đã thực hiện:
* Xây dựng `lab-solution/03-versioning/versioned_log_server.py` đại diện cho phiên bản `2.0.0`.
* Triển khai Resource `server://info` công bố metadata phiên bản, danh sách công cụ đang hoạt động, công cụ đã đánh dấu deprecated và tài liệu chuyển đổi (migration guide).
* Giữ nguyên tool v1 `get_recent_errors` trả về định dạng plain text (đánh dấu deprecated trong docstring và metadata).
* Bổ sung tool v2 `get_recent_errors_v2` trả về dữ liệu định dạng **Structured JSON** bóc tách các trường: `timestamp`, `severity`, `service`, `trace_id`, `error_type`, `message`, `stack_trace`, `suggested_action`.
* Xây dựng `legacy_client.py` (đại diện cho client cũ) và `modern_client.py` (đại diện cho client mới đọc resource trước khi gọi tool).

#### Kết quả đạt được:
* `legacy_client.py` chỉ gọi tool v1 `get_recent_errors` và vẫn nhận được kết quả dạng chuỗi text như thiết kế ban đầu, không phát sinh lỗi.
* `modern_client.py` truy vấn resource `server://info`, phát hiện `get_recent_errors` thuộc danh sách `deprecated_tools`, từ đó chủ động chuyển sang gọi `get_recent_errors_v2` để nhận dữ liệu JSON có cấu trúc.
* Kết quả kiểm chứng sự cùng tồn tại của 2 phiên bản client được ghi nhận tại `lab-solution/03-versioning/versioning_test_results.json`.

#### Giải thích kỹ thuật (Tại sao lại như vậy):
* Việc thay đổi kiểu dữ liệu trả về (từ text sang JSON) là một breaking change đối với các client cũ nếu sửa trực tiếp trên tool hiện có.
* Bằng cách duy trì tool v1 song song với tool v2 và công bố metadata qua Resource `server://info`, hệ thống cho phép client mới khai thác các tính năng nâng cao trong khi các client cũ vẫn tiếp tục vận hành mà không bị gián đoạn.

---

## 3. Tổng kết Đối chiếu Yêu cầu

| Hạng mục | Yêu cầu bài tập | Kết quả thực tế | Ghi chú kỹ thuật |
|---|---|---|---|
| **Bài 1 (Dễ)** | MCP Server stdio, 1-2 tools thực tế, kết nối client | Đã triển khai `log_server.py` với 2 tools, kiểm thử thành công qua `test_client.py` và `chat_client.py` | Sử dụng regex đa dòng xử lý traceback Python |
| **Bài 2 (Trung bình)** | Streamable HTTP, Bearer Token Auth, kiểm thử 3 kịch bản | Đã triển khai `auth_log_server.py` trên cổng 8000, kiểm thử 3 kịch bản và lưu log tại `auth_test_results.json` | Token được xác minh tại tầng transport của MCP |
| **Bài 3 (Khó)** | Thay đổi response format, Resource `server://info`, đảm bảo backward compatibility | Đã triển khai `versioned_log_server.py` (v1 plain text + v2 JSON), kiểm thử thành công với cả `legacy_client` và `modern_client` | Client mới đọc metadata để điều hướng gọi tool v2 |
