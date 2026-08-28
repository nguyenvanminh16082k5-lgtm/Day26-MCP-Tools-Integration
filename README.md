# Day 26: Model Context Protocol (MCP) & Tools Integration

> **Loi giai Bai tap Lab (Lab Solutions)**: Toan bo ma nguon, test client, chatbot CLI va file bao cao ket qua nghiem thu cho 3 cap do (De, Trung binh, Kho) duoc dat tai thu muc **[`lab-solution/`](lab-solution/)**.
> 
> * **Bao cao tong ket nghiem thu**: [`lab-solution/REPORT.md`](lab-solution/REPORT.md)
> * **Huong dan chi tiet tung bai**: [`lab-solution/README.md`](lab-solution/README.md)

---

## 1. Huong dan Nhanh cho Nguoi Cham (Quick Start for Grading)

### Kich hoat moi truong
```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### Chay kiem thu cac cap do bai tap:

#### Bai 1 - De: MCP Server qua stdio (Application Log Analyzer)
```bash
# Kiem thu giao thuc stdio (khong can API key)
python lab-solution/01-stdio/test_client.py

# Chatbot CLI voi Gemini 2.5 Flash (can GEMINI_API_KEY trong .env)
python lab-solution/01-stdio/chat_client.py
```

#### Bai 2 - Trung binh: Streamable HTTP + Authentication (Bearer Token)
* Terminal 1 (Chay server tren port 8000):
  ```bash
  python lab-solution/02-auth/auth_log_server.py
  ```
* Terminal 2 (Chay test suite 3 kich ban bao mat):
  ```bash
  python lab-solution/02-auth/test_auth_client.py
  ```
* Ket qua thuc te duoc luu tai: [`lab-solution/02-auth/auth_test_results.json`](lab-solution/02-auth/auth_test_results.json)

#### Bai 3 - Kho: Versioning & Backward Compatibility
```bash
# Chay kiem thu ca Legacy Client (v1) va Modern Client (v2 doc server://info)
python lab-solution/03-versioning/modern_client.py
```
* Ket qua thuc te duoc luu tai: [`lab-solution/03-versioning/versioning_test_results.json`](lab-solution/03-versioning/versioning_test_results.json)

---

## 2. Cau truc Toan bo Repository

```
Day26-MCP-Tools-Integration/
├── README.md                      <- Huong dan tong quan toan bo repo
│
├── lab-solution/                  <- [LOI GIAI BAI TAP LAB DAY 26]
│   ├── REPORT.md                  <- Bao cao ket qua nghiem thu chi tiet
│   ├── README.md                  <- Huong dan chi tiet cho lab-solution
│   ├── requirements.txt           <- Dependencies
│   ├── .env.example               <- Template bien moi truong
│   │
│   ├── data/                      <- Du lieu log thuc te da microservices
│   │   ├── app.log                <- File log he thong chua 5 loi kem stack trace
│   │   └── generate_logs.py       <- Script tao/lam moi timestamps log
│   │
│   ├── 01-stdio/                  <- [BAI 1 - DE] MCP Server stdio
│   │   ├── log_server.py          <- FastMCP/MCPServer cung cap 2 tools
│   │   ├── test_client.py         <- Client kiem thu giao thuc stdio
│   │   └── chat_client.py         <- AI Chatbot CLI tich hop Gemini 2.5 Flash
│   │
│   ├── 02-auth/                   <- [BAI 2 - TRUNG BINH] Streamable HTTP + Auth
│   │   ├── auth_log_server.py     <- Server HTTP tich hop StaticTokenVerifier
│   │   ├── test_auth_client.py    <- Test suite tu dong 3 kich ban bao mat
│   │   └── auth_test_results.json <- File JSON ket qua kiem thu thuc te
│   │
│   └── 03-versioning/             <- [BAI 3 - KHO] Versioning & Backward Compat
│       ├── versioned_log_server.py<- Server v2.0 (v1 + v2 + resource server://info)
│       ├── legacy_client.py       <- Client v1 goi tool cu (khong bi break)
│       ├── modern_client.py       <- Client v2 doc server://info va goi tool v2
│       └── versioning_test_results.json <- File JSON ket qua kiem thu thuc te
│
├── 01-function-calling/           <- Vi du ly thuyet: Function Calling thuan (Gemini SDK)
├── 02-mcp-basics/                 <- Vi du ly thuyet: MCP Server & Client co ban
└── 03-production/                 <- Vi du ly thuyet: Auth, Registry, Versioning
```

---

## 3. Phan biet MCP va Function Calling

### Dinh nghia
* **Function Calling** la mot *kha nang cua model* (capability). Model tu quyet dinh goi tool va sinh JSON tham so, nhung app moi la noi chay tool.
* **MCP (Model Context Protocol)** la mot *giao thuc chuan* (protocol) giup cac MCP Client (Claude Code, Claude Desktop, Cursor, Custom Client) ket noi va su dung tools/resources tu MCP Server mot cach thong nhat.

### So sanh truc tiep
| Tieu chi | Function Calling | Model Context Protocol (MCP) |
|---|---|---|
| **Ban chat** | Tinh nang cua mo hinh (Model capability) | Giao thuc giao tiep client-server |
| **Dinh nghia tool** | Hard-code trong tung app | Server tu cong bo (self-describe) tool |
| **Tai su dung** | Phai viet lai cho moi app | Viet 1 lan, moi MCP client dung duoc |
| **Thuc thi** | App tu chay | MCP Server chay, client dieu phoi |
| **Chuan hoa** | Moi nha cung cap 1 kieu | Chuan chung cua he sinh thai Anthropic/MCP |
