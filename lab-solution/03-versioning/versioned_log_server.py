"""MCP Server co Versioning va Tuong thich nguoc (Bai 3 - Kho).

Phien ban: 2.0.0
Cung cap 3 ky thuat tuong thich nguoc:
  1. Tool v1 (get_recent_errors): Giu nguyen dinh dang plain text cho client cu (deprecated).
  2. Tool v2 (get_recent_errors_v2): Tra ve Structured JSON kem traceback bop tach chi tiet.
  3. Resource server://info: Cong bo metadata server, danh sach deprecated tools va migration guide.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ho tro UTF-8 tren Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOG_PATH = BASE_DIR / "data" / "app.log"

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP as MCPServer
    except ImportError:
        from mcp.server import Server as MCPServer

SERVER_VERSION = "2.0.0"

mcp = MCPServer(
    "log-analyzer-v2",
    instructions=f"Log Analyzer MCP Server v{SERVER_VERSION}. "
    "Ho tro get_recent_errors (v1, backward compat) va get_recent_errors_v2 (v2, structured JSON).",
)

LOG_HEADER_REGEX = re.compile(
    r"^\[(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+\[(?P<level>[A-Z]+)\s*\]\s+\[(?P<service>[^\]]+)\]\s+\[(?P<trace_id>[^\]]+)\]\s+(?P<message>.*)$"
)


class LogEntry:
    def __init__(self, timestamp: str, level: str, service: str, trace_id: str, message: str, full_text: str, stack_trace: list[str]) -> None:
        self.timestamp = timestamp
        self.level = level.strip()
        self.service = service.strip()
        self.trace_id = trace_id.strip()
        self.message = message.strip()
        self.full_text = full_text.strip()
        self.stack_trace = stack_trace


def parse_log_file(log_path: Path | str | None = None) -> list[LogEntry]:
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
    current_traceback: list[str] = []

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
                            stack_trace=current_traceback,
                        )
                    )
                current_header_match = match
                current_lines = [line_str]
                current_traceback = []
            else:
                if current_header_match:
                    current_lines.append(line_str)
                    current_traceback.append(line_str.strip())

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
                stack_trace=current_traceback,
            )
        )

    return entries


# ==============================================================================
# 1. RESOURCE METADATA (Cong bo version va huong dan migration)
# ==============================================================================
@mcp.resource("server://info")
def server_info() -> str:
    """Metadata cua server - Version, capabilities, danh sach deprecated tools va migration guide."""
    return json.dumps(
        {
            "server_name": "log-analyzer",
            "version": SERVER_VERSION,
            "api_version": "2.0",
            "capabilities": [
                "text_search",
                "structured_json_diagnostics",
                "traceback_parsing",
                "service_filtering",
            ],
            "deprecated_tools": ["get_recent_errors"],
            "active_tools": ["get_recent_errors_v2", "search_logs"],
            "migration_guide": (
                "Chuyen tu get_recent_errors (v1) sang get_recent_errors_v2 (v2). "
                "Tham so 'limit' va 'service' giu nguyen. "
                "Format v2 tra ve JSON co cau truc gom timestamp, level, service, trace_id, error_type, stack_trace, suggested_action."
            ),
        },
        indent=2,
        ensure_ascii=False,
    )


# ==============================================================================
# 2. TOOL V1 (Deprecated - Giu nguyen kieu string cho Client cu)
# ==============================================================================
@mcp.tool()
def get_recent_errors(limit: int = 5, service: str = "ALL") -> str:
    """[v1 - Deprecated] Lay danh sach cac loi gan day duoi dang chuoi text don gian. Khuyen nghi chuyen sang get_recent_errors_v2."""
    entries = parse_log_file()
    if not entries:
        return f"Khong tim thay file log tai: {DEFAULT_LOG_PATH}"

    error_entries = [e for e in entries if e.level.upper() in ("ERROR", "CRITICAL")]
    if service.upper() != "ALL":
        error_entries = [e for e in error_entries if e.service.lower() == service.lower()]

    if not error_entries:
        return "Khong tim thay loi nao trong file log."

    recent = error_entries[-limit:]
    recent.reverse()

    results = [f"=== [v1 Legacy] {len(recent)} loi gan nhat ==="]
    for idx, e in enumerate(recent, 1):
        results.append(f"\n[{idx}] {e.timestamp} | {e.level} | {e.service} | Trace: {e.trace_id}")
        results.append(f"    {e.full_text}")

    return "\n".join(results)


# ==============================================================================
# 3. TOOL V2 (Phien ban moi - Tra ve Structured JSON chi tiet)
# ==============================================================================
def extract_error_type(message: str, stack_trace: list[str]) -> str:
    """Trich xuat loai Exception/Error name tu message hoac stack trace."""
    if ":" in message:
        return message.split(":", 1)[0].strip()
    for line in reversed(stack_trace):
        if ":" in line and not line.startswith("File "):
            return line.split(":", 1)[0].strip()
    return "UnknownError"


def suggest_action_for_error(error_type: str, message: str) -> str:
    """De xuat huong xu ly dua tren loai loi phat hien duoc."""
    err_lower = (error_type + " " + message).lower()
    if "operationalerror" in err_lower or "timed out" in err_lower or "connection" in err_lower:
        return "Kiem tra PostgreSQL connection pool, network latency va database host status."
    elif "memorylimitexceeded" in err_lower or "oom" in err_lower:
        return "Tang memory limit cho worker process hoac toi uu hoa batch size xu ly du lieu."
    elif "authentication" in err_lower or "invalidsignature" in err_lower:
        return "Kiem tra JWT secret key rotation va expire time cua client token."
    elif "bad gateway" in err_lower or "502" in err_lower or "stripe" in err_lower:
        return "Kiem tra trang thai upstream payment gateway (Stripe) va kich hoat retry queue."
    elif "validationerror" in err_lower:
        return "Kiem tra payload request cua API client, dam bao day du cac field required."
    return "Kiem tra traceback va log chi tiet de chan doan them."


@mcp.tool()
def get_recent_errors_v2(
    limit: int = 5,
    service: str = "ALL",
    include_traceback: bool = True,
    format: str = "json",
) -> str:
    """[v2] Lay danh sach loi chi tiet duoi dang JSON co cau truc gom timestamp, error_type, stack_trace va suggested_action.

    Args:
        limit: So luong loi gan nhat (mac dinh: 5).
        service: Loc theo microservice ('payment-service', 'auth-service', 'order-service', hoac 'ALL').
        include_traceback: Co bao gom mang stack trace chi tiet hay khong (mac dinh: True).
        format: Dinh dang tra ve ('json' hoac 'summary', mac dinh: 'json').
    """
    entries = parse_log_file()
    if not entries:
        return json.dumps({"status": "error", "message": "File log khong ton tai", "total_errors": 0, "errors": []})

    error_entries = [e for e in entries if e.level.upper() in ("ERROR", "CRITICAL")]
    if service.upper() != "ALL":
        error_entries = [e for e in error_entries if e.service.lower() == service.lower()]

    recent = error_entries[-limit:]
    recent.reverse()

    structured_errors = []
    for e in recent:
        err_type = extract_error_type(e.message, e.stack_trace)
        item = {
            "timestamp": e.timestamp,
            "severity": e.level,
            "service": e.service,
            "trace_id": e.trace_id,
            "error_type": err_type,
            "message": e.message,
            "suggested_action": suggest_action_for_error(err_type, e.message),
        }
        if include_traceback:
            item["stack_trace"] = e.stack_trace
        structured_errors.append(item)

    response_payload = {
        "api_version": "2.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_errors_in_log": len(error_entries),
        "returned_count": len(structured_errors),
        "service_filter": service,
        "errors": structured_errors,
    }

    return json.dumps(response_payload, indent=2, ensure_ascii=False)


# ==============================================================================
# 4. TOOL SEARCH LOGS
# ==============================================================================
@mcp.tool()
def search_logs(keyword: str, level: str = "ALL", limit: int = 20) -> str:
    """Tim kiem cac ban ghi log theo tu khoa va theo cap do log."""
    entries = parse_log_file()
    if not entries:
        return f"Khong tim thay file log tai: {DEFAULT_LOG_PATH}"

    keyword_lower = keyword.lower()
    matched = []

    for e in entries:
        if level.upper() != "ALL" and e.level.upper() != level.upper():
            continue
        if keyword_lower in e.full_text.lower():
            matched.append(e)

    if not matched:
        return f"Khong tim thay ban ghi log nao khop voi: '{keyword}' (Level: {level})."

    selected = matched[-limit:]
    selected.reverse()

    results = [f"=== Tim kiem log cho '{keyword}' ({len(selected)}/{len(matched)} ban ghi) ==="]
    for idx, e in enumerate(selected, 1):
        results.append(f"\n[{idx}] {e.timestamp} | {e.level:<8} | {e.service:<15} | Trace: {e.trace_id}")
        results.append(f"    {e.full_text}")

    return "\n".join(results)


if __name__ == "__main__":
    mcp.run()
