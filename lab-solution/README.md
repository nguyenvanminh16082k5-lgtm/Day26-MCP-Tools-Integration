# Huong dan Thuc hanh: Log Analyzer MCP Server

Du an nay trien khai tron ven 3 bai tap MCP tu co ban den nang cao cho bai toan Doc, Loc & Chan doan Log He thong Thuc te.

---

## 1. Bai 1 (De): MCP Server qua giao thuc stdio

### Cau truc thu muc
* `01-stdio/log_server.py`: MCP Server chuan (MCPServer/FastMCP) cung cap 2 tools:
  * `get_recent_errors(limit, service)`: Lay cac loi gan nhat kem stack trace.
  * `search_logs(keyword, level, limit)`: Tim kiem log theo tu khoa va cap do.
* `01-stdio/test_client.py`: Script kiem thu giao thuc MCP tu dong qua `stdio_client` (Khong can API key).
* `01-stdio/chat_client.py`: AI Chatbot CLI tich hop Gemini 2.5 Flash + MCP Server (Tu dong chuyen doi MCP tools sang Function Calling).

### Cach chay
```bash
# Kiem thu giao thuc stdio
python lab-solution/01-stdio/test_client.py

# Chatbot CLI voi Gemini 2.5 Flash (can GEMINI_API_KEY trong .env)
python lab-solution/01-stdio/chat_client.py
```

---

## 2. Bai 2 (Trung binh): Streamable HTTP + Authentication

### Cau truc thu muc
* `02-auth/auth_log_server.py`: MCP Server chay Streamable HTTP (`0.0.0.0:8000/mcp`) tich hop `StaticTokenVerifier` (Bearer Token).
* `02-auth/test_auth_client.py`: Script kiem thu tu dong 3 kich ban bao mat va xuat bao cao JSON.
* `02-auth/auth_test_results.json`: File ket qua chung minh chi tiet cho ca 3 test case da chay thuc te.

### Cach chay
* Terminal 1 (Chay server):
  ```bash
  python lab-solution/02-auth/auth_log_server.py
  ```
* Terminal 2 (Chay client test):
  ```bash
  python lab-solution/02-auth/test_auth_client.py
  ```

---

## 3. Bai 3 (Kho): Versioning & Backward Compatibility

### Cau truc thu muc
* `03-versioning/versioned_log_server.py`: MCP Server v2.0.0 tich hop:
  * Resource `server://info`: Metadata phien ban, danh sach deprecated tools, active tools va migration guide.
  * Tool v1 `get_recent_errors`: Giu nguyen plain text cho client cu (deprecated).
  * Tool v2 `get_recent_errors_v2`: Tra ve Structured JSON kem phan tich `error_type`, `suggested_action` va `stack_trace`.
  * Tool `search_logs`: Tim kiem log chung.
* `03-versioning/legacy_client.py`: Gia lap client cu chi biet goi tool v1 -> Kiem chung khong bi break.
* `03-versioning/modern_client.py`: Client the he moi doc resource `server://info`, phat hien deprecated va tu dong goi tool v2.
* `03-versioning/versioning_test_results.json`: File JSON ket qua kiem thu thuc te.

### Cach chay
```bash
# Chay kiem thu toan bo Bai 3 (ca legacy va modern client)
python lab-solution/03-versioning/modern_client.py
```

---

## Bang Tong hop Checklist Nghiem thu

### Bai 1 (De):
- [x] MCP Server khoi dong duoc qua stdio
- [x] Co 2 tools tu xay (`get_recent_errors`, `search_logs`)
- [x] Giai quyet cong viec thuc te tu `data/app.log`
- [x] AI Chatbot CLI tich hop Gemini 2.5 Flash

### Bai 2 (Trung binh):
- [x] Server chay bang Streamable HTTP (`http://0.0.0.0:8000/mcp`)
- [x] Client ket noi qua HTTP
- [x] Authentication duoc bat (Bearer Token)
- [x] Token dung -> 200 OK
- [x] Token sai -> 401 Unauthorized
- [x] Thieu token -> 401 Unauthorized
- [x] File JSON chung minh thuc te (`auth_test_results.json`)

### Bai 3 (Kho):
- [x] Thay doi response format sang Structured JSON
- [x] Client cu van chay binh thuong (Backward compatibility verified)
- [x] Client moi dung duoc capability moi
- [x] Co resource `server://info`
- [x] `server://info` chua metadata, version, migration guide
- [x] Client moi doc metadata truoc khi chon tool
- [x] File JSON chung minh thuc te (`versioning_test_results.json`)
