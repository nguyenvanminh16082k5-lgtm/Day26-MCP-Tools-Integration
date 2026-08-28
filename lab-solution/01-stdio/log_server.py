"""MCP Server cho tác vụ Đọc & Phân tích Log Hệ thống (Bài 1 - Dễ).

Server hoạt động qua giao thức MCP stdio. Tự động parse file log thực tế,
giữ nguyên vẹn multi-line stack trace và cung cấp 2 tools cho Claude Code / MCP Client:
1. get_recent_errors: Trích xuất N lỗi gần đây nhất kèm traceback.
2. search_logs: Tìm kiếm log theo từ khóa và lọc theo cấp độ (INFO, WARNING, ERROR, CRITICAL).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Hỗ trợ UTF-8 chuẩn trên Windows Console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Tương thích cả MCP 2.x (MCPServer) và MCP 1.x (FastMCP)
try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP as MCPServer
    except ImportError:
        from mcp.server import Server as MCPServer

# Khởi tạo MCP Server
mcp = MCPServer("log-analyzer")

# Xác định đường dẫn file log an toàn, độc lập với working directory
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOG_PATH = BASE_DIR / "data" / "app.log"

LOG_HEADER_REGEX = re.compile(
    r"^\[(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+\[(?P<level>[A-Z]+)\s*\]\s+\[(?P<service>[^\]]+)\]\s+\[(?P<trace_id>[^\]]+)\]\s+(?P<message>.*)$"
)


class LogEntry:
    """Đại diện cho một bản ghi log (gồm header và các dòng stacktrace)."""

    def __init__(self, timestamp: str, level: str, service: str, trace_id: str, message: str, full_text: str) -> None:
        self.timestamp = timestamp
        self.level = level.strip()
        self.service = service.strip()
        self.trace_id = trace_id.strip()
        self.message = message.strip()
        self.full_text = full_text.strip()


def parse_log_file(log_path: Path | str | None = None) -> list[LogEntry]:
    """Đọc và parse file log thành danh sách các LogEntry đa dòng."""
    target_path = Path(log_path) if log_path else DEFAULT_LOG_PATH
    if not target_path.exists():
        env_path = os.environ.get("LOG_FILE_PATH")
        if env_path and Path(env_path).exists():
            target_path = Path(env_path)
        else:
            return []

    entries: list[LogEntry] = []
    current_header_match: re.Match | None = None
    current_lines: list[str] = []

    with open(target_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.rstrip("\r\n")
            match = LOG_HEADER_REGEX.match(line_str)
            if match:
                if current_header_match:
                    gd = current_header_match.groupdict()
                    entries.append(
                        LogEntry(
                            timestamp=gd["timestamp"],
                            level=gd["level"],
                            service=gd["service"],
                            trace_id=gd["trace_id"],
                            message=gd["message"],
                            full_text="\n".join(current_lines),
                        )
                    )
                current_header_match = match
                current_lines = [line_str]
            else:
                if current_header_match:
                    current_lines.append(line_str)

    if current_header_match:
        gd = current_header_match.groupdict()
        entries.append(
            LogEntry(
                timestamp=gd["timestamp"],
                level=gd["level"],
                service=gd["service"],
                trace_id=gd["trace_id"],
                message=gd["message"],
                full_text="\n".join(current_lines),
            )
        )

    return entries


@mcp.tool()
def get_recent_errors(limit: int = 5, service: str = "ALL") -> str:
    """Lấy danh sách các lỗi (ERROR, CRITICAL) gần đây nhất từ file log của hệ thống kèm stack trace đầy đủ.

    Dùng tool này khi người dùng hỏi về:
    - Các lỗi mới nhất/gần đây trong log
    - Sự cố hệ thống hoặc các lần crash ứng dụng
    - Cần tìm nguyên nhân gây lỗi gần nhất

    Args:
        limit: Số lượng lỗi gần nhất cần lấy (mặc định: 5).
        service: Tên microservice cần lọc (ví dụ: 'payment-service', 'auth-service', 'order-service', hoặc 'ALL').
    """
    entries = parse_log_file()
    if not entries:
        return f"Không tìm thấy file log hoặc file log rỗng tại: {DEFAULT_LOG_PATH}"

    error_entries = [
        e for e in entries if e.level.upper() in ("ERROR", "CRITICAL")
    ]

    if service.upper() != "ALL":
        error_entries = [
            e for e in error_entries if e.service.lower() == service.lower()
        ]

    if not error_entries:
        service_msg = f" của service '{service}'" if service.upper() != "ALL" else ""
        return f"✅ Không tìm thấy lỗi nào (ERROR/CRITICAL){service_msg} trong file log."

    recent = error_entries[-limit:]
    recent.reverse()

    results = [
        f"=== Tìm thấy {len(recent)} lỗi gần nhất (tổng số lỗi trong log: {len(error_entries)}) ==="
    ]
    for idx, e in enumerate(recent, 1):
        results.append(f"\n[{idx}] {e.timestamp} | {e.level} | {e.service} | Trace: {e.trace_id}")
        results.append(f"    {e.full_text}")

    return "\n".join(results)


@mcp.tool()
def search_logs(keyword: str, level: str = "ALL", limit: int = 20) -> str:
    """Tìm kiếm các bản ghi log theo từ khóa (keyword, trace_id, user_id, error name, SKU, IP) và theo cấp độ log.

    Dùng tool này khi người dùng muốn:
    - Tra cứu lịch sử hoạt động của một User, Order, Request (Trace ID)
    - Tìm kiếm xem một từ khóa/lỗi cụ thể (ví dụ: 'psycopg2', 'Stripe', 'usr_1042', 'OOM') có xuất hiện trong log không

    Args:
        keyword: Từ khóa cần tìm kiếm trong nội dung log hoặc trace ID.
        level: Cấp độ log cần lọc: 'INFO', 'WARNING', 'ERROR', 'CRITICAL', hoặc 'ALL' (mặc định: 'ALL').
        limit: Số lượng bản ghi tối đa trả về (mặc định: 20).
    """
    entries = parse_log_file()
    if not entries:
        return f"Không tìm thấy file log hoặc file log rỗng tại: {DEFAULT_LOG_PATH}"

    keyword_lower = keyword.lower()
    matched = []

    for e in entries:
        if level.upper() != "ALL" and e.level.upper() != level.upper():
            continue
        if keyword_lower in e.full_text.lower():
            matched.append(e)

    if not matched:
        return f"Không tìm thấy bản ghi log nào khớp với từ khóa: '{keyword}' (Level: {level})."

    selected = matched[-limit:]
    selected.reverse()

    results = [
        f"=== Kết quả tìm kiếm log cho từ khóa '{keyword}' (Khớp: {len(matched)} bản ghi, hiển thị: {len(selected)}) ==="
    ]
    for idx, e in enumerate(selected, 1):
        results.append(f"\n[{idx}] {e.timestamp} | {e.level:<8} | {e.service:<15} | Trace: {e.trace_id}")
        results.append(f"    {e.full_text}")

    return "\n".join(results)


if __name__ == "__main__":
    mcp.run()
