# Day 26: Model Context Protocol (MCP) & Tools Integration

> **Lời giải Bài tập Lab (Lab Solutions)**: Toàn bộ mã nguồn, test client, chatbot CLI và file báo cáo kỹ thuật nghiệm thu cho 3 cấp độ (Dễ, Trung bình, Khó) được đặt tại thư mục **[`lab-solution/`](lab-solution/)**.
> 
> * **Báo cáo kỹ thuật tổng kết**: [`lab-solution/REPORT.md`](lab-solution/REPORT.md)
> * **Hướng dẫn cài đặt, mô tả Input/Output & Đăng ký Claude Code**: [`lab-solution/README.md`](lab-solution/README.md)

---

## 1. Hướng dẫn Nhanh cho Người Chấm Bài (Quick Start for Grading)

### Kích hoạt môi trường
```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### Chạy kiểm thử từng cấp độ bài tập:

#### Bài 1 - Dễ: MCP Server qua stdio (Application Log Analyzer)
```bash
# Kiểm thử giao thức stdio (không cần API key)
python lab-solution/01-stdio/test_client.py

# Chatbot CLI với Gemini 2.5 Flash (cần GEMINI_API_KEY trong .env)
python lab-solution/01-stdio/chat_client.py

# Đăng ký với Claude Code:
claude mcp add log-analyzer -- python "c:/Users/USER/Desktop/Vin/Day26-MCP-Tools-Integration/lab-solution/01-stdio/log_server.py"
```

#### Bài 2 - Trung bình: Streamable HTTP + Authentication (Bearer Token)
* Terminal 1 (Chạy server trên port 8000):
  ```bash
  python lab-solution/02-auth/auth_log_server.py
  ```
* Terminal 2 (Chạy test suite 3 kịch bản bảo mật):
  ```bash
  python lab-solution/02-auth/test_auth_client.py
  ```
* Kết quả thực tế được lưu tại: [`lab-solution/02-auth/auth_test_results.json`](lab-solution/02-auth/auth_test_results.json)

#### Bài 3 - Khó: Versioning & Backward Compatibility
```bash
# Chạy kiểm thử cả Legacy Client (v1) và Modern Client (v2 đọc server://info)
python lab-solution/03-versioning/modern_client.py
```
* Kết quả thực tế được lưu tại: [`lab-solution/03-versioning/versioning_test_results.json`](lab-solution/03-versioning/versioning_test_results.json)

---

## 2. Cấu trúc Toàn bộ Repository

```
Day26-MCP-Tools-Integration/
├── README.md                      <- Hướng dẫn tổng quan toàn bộ repo
│
├── lab-solution/                  <- [LỜI GIẢI BÀI TẬP LAB DAY 26]
│   ├── REPORT.md                  <- Báo cáo kết quả kỹ thuật chi tiết
│   ├── README.md                  <- Hướng dẫn chi tiết, Input/Output bảng tra cứu
│   ├── requirements.txt           <- Dependencies
│   ├── .env.example               <- Template biến môi trường
│   │
│   ├── data/                      <- Dữ liệu log thực tế đa microservices
│   │   ├── app.log                <- File log hệ thống chứa 5 lỗi kèm stack trace
│   │   └── generate_logs.py       <- Script tạo/làm mới timestamps log
│   │
│   ├── 01-stdio/                  <- [BÀI 1 - DỄ] MCP Server stdio
│   │   ├── log_server.py          <- FastMCP/MCPServer cung cấp 2 tools
│   │   ├── test_client.py         <- Client kiểm thử giao thức stdio
│   │   └── chat_client.py         <- AI Chatbot CLI tích hợp Gemini 2.5 Flash
│   │
│   ├── 02-auth/                   <- [BÀI 2 - TRUNG BÌNH] Streamable HTTP + Auth
│   │   ├── auth_log_server.py     <- Server HTTP tích hợp StaticTokenVerifier
│   │   ├── test_auth_client.py    <- Test suite tự động 3 kịch bản bảo mật
│   │   └── auth_test_results.json <- File JSON kết quả kiểm thử thực tế
│   │
│   └── 03-versioning/             <- [BÀI 3 - KHÓ] Versioning & Backward Compat
│       ├── versioned_log_server.py<- Server v2.0 (v1 + v2 + resource server://info)
│       ├── legacy_client.py       <- Client v1 gọi tool cũ (không bị break)
│       ├── modern_client.py       <- Client v2 đọc server://info và gọi tool v2
│       └── versioning_test_results.json <- File JSON kết quả kiểm thử thực tế
│
├── 01-function-calling/           <- Ví dụ lý thuyết: Function Calling thuần (Gemini SDK)
├── 02-mcp-basics/                 <- Ví dụ lý thuyết: MCP Server & Client cơ bản
└── 03-production/                 <- Ví dụ lý thuyết: Auth, Registry, Versioning
```

---

## 3. Phân biệt MCP và Function Calling

### Định nghĩa
* **Function Calling** là một *khả năng của model* (capability). Model tự quyết định gọi tool và sinh JSON tham số, nhưng ứng dụng (app) mới là nơi chạy tool.
* **MCP (Model Context Protocol)** là một *giao thức chuẩn* (protocol) giúp các MCP Client (Claude Code, Claude Desktop, Cursor, Custom Client) kết nối và sử dụng tools/resources từ MCP Server một cách thống nhất.

### So sánh trực tiếp
| Tiêu chí | Function Calling | Model Context Protocol (MCP) |
|---|---|---|
| **Bản chất** | Tính năng của mô hình (Model capability) | Giao thức giao tiếp client-server |
| **Định nghĩa tool** | Hard-code trong từng app | Server tự công bố (self-describe) tool |
| **Tái sử dụng** | Phải viết lại cho mỗi app | Viết 1 lần, mọi MCP client dùng được |
| **Thực thi** | App tự chạy | MCP Server chạy, client điều phối |
| **Chuẩn hóa** | Mỗi nhà cung cấp 1 kiểu | Chuẩn chung của hệ sinh thái Anthropic/MCP |
