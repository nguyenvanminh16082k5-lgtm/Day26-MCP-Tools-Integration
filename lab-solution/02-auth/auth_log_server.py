"""MCP Server co Authentication qua Streamable HTTP (Bai 2 - Trung binh).

Server chay qua HTTP (Streamable HTTP) thay vi stdio, kem Bearer Token verification.
Chi request mang token hop le moi duoc phep kham pha va goi tools doc log.

Luong hoat dong:
  Client gui request HTTP kem header "Authorization: Bearer <token>"
    -> MCP SDK tu chay StaticTokenVerifier de xac minh token
    -> Token hop le -> cho phep truy cap tools (HTTP 200)
    -> Token sai / thieu -> tra ve HTTP 401 / 403
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ho tro UTF-8 tren Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP as MCPServer
    except ImportError:
        from mcp.server import Server as MCPServer

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings

# Quan ly Token hop le
VALID_TOKENS: dict[str, str] = {
    os.environ.get("MCP_AUTH_TOKEN", "log-reader-secret-token-2026"): "developer",
    os.environ.get("ADMIN_AUTH_TOKEN", "admin-super-secret-9999"): "admin-ops",
}

HOST = os.environ.get("MCP_SERVER_HOST", "0.0.0.0")
PORT = int(os.environ.get("MCP_SERVER_PORT", 8000))
DEFAULT_LOG_PATH = BASE_DIR / "data" / "app.log"


class StaticTokenVerifier(TokenVerifier):
    """Kiem tra Bearer Token dua tren danh sach token duoc cap quyen."""

    async def verify_token(self, token: str) -> AccessToken | None:
        client_id = VALID_TOKENS.get(token)
        if client_id is None:
            return None
        return AccessToken(token=token, client_id=client_id, scopes=["logs:read"])


# Khoi tao MCP Server bao mat
mcp = MCPServer(
    "log-analyzer-secure",
    auth=AuthSettings(
        issuer_url=f"http://localhost:{PORT}",
        resource_server_url=f"http://localhost:{PORT}",
    ),
    token_verifier=StaticTokenVerifier(),
)

LOG_HEADER_REGEX = re.compile(
    r"^\[(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+\[(?P<level>[A-Z]+)\s*\]\s+\[(?P<service>[^\]]+)\]\s+\[(?P<trace_id>[^\]]+)\]\s+(?P<message>.*)$"
)


class LogEntry:
    def __init__(self, timestamp: str, level: str, service: str, trace_id: str, message: str, full_text: str) -> None:
        self.timestamp = timestamp
        self.level = level.strip()
        self.service = service.strip()
        self.trace_id = trace_id.strip()
        self.message = message.strip()
        self.full_text = full_text.strip()


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
    """Lay danh sach cac loi (ERROR, CRITICAL) gan day nhat tu file log kem stack trace."""
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

    results = [f"=== [Auth Verified] {len(recent)} loi gan nhat ==="]
    for idx, e in enumerate(recent, 1):
        results.append(f"\n[{idx}] {e.timestamp} | {e.level} | {e.service} | Trace: {e.trace_id}")
        results.append(f"    {e.full_text}")

    return "\n".join(results)


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

    results = [f"=== [Auth Verified] Tim kiem log cho '{keyword}' ({len(selected)}/{len(matched)} ban ghi) ==="]
    for idx, e in enumerate(selected, 1):
        results.append(f"\n[{idx}] {e.timestamp} | {e.level:<8} | {e.service:<15} | Trace: {e.trace_id}")
        results.append(f"    {e.full_text}")

    return "\n".join(results)


if __name__ == "__main__":
    print(f"Khoi dong Auth Log MCP Server tren Streamable HTTP tai http://{HOST}:{PORT}/mcp")
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
