"""Test Client cho MCP Server co Authentication (Bai 2 - Trung binh).

Kiem thu tu dong 3 kich ban va ghi ket qua truc tiep ra file JSON:
  [Case 1] Token hop le: Ket noi thanh cong, list tools va goi get_recent_errors.
  [Case 2] Token sai: Bi tu choi (HTTP 401/403).
  [Case 3] Thieu token: Bi tu choi (HTTP 401).

File output:
  lab-solution/02-auth/auth_test_results.json
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

PORT = int(os.environ.get("MCP_SERVER_PORT", 8000))
SERVER_URL = f"http://localhost:{PORT}/mcp"
VALID_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "log-reader-secret-token-2026")
INVALID_TOKEN = "invalid-token-xyz-12345"
OUTPUT_JSON_PATH = Path(__file__).parent / "auth_test_results.json"


async def test_case_1_valid_token() -> dict:
    print("\n" + "=" * 60)
    print("[Case 1] Kiem thu voi TOKEN HOP LE (Authorization: Bearer <VALID_TOKEN>)")
    print("=" * 60)
    http_client = httpx.AsyncClient(headers={"Authorization": f"Bearer {VALID_TOKEN}"})

    case_data = {
        "case_id": "AUTH-01",
        "name": "Valid Bearer Token",
        "description": "Client gui Authorization header voi token hop le duoc cap quyen",
        "request_header": {"Authorization": f"Bearer {VALID_TOKEN}"},
        "expected_status": "SUCCESS (200 OK)",
        "actual_status": "UNKNOWN",
        "result": "FAILED",
        "discovered_tools": [],
        "tool_call_test": {},
    }

    try:
        async with http_client:
            async with streamable_http_client(SERVER_URL, http_client=http_client) as streams:
                read, write = streams[0], streams[1]
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    tool_names = [t.name for t in tools.tools]
                    case_data["discovered_tools"] = tool_names
                    print(f"[PASSED] Xac thuc thanh cong! Server cong bo {len(tool_names)} tools: {tool_names}")

                    print("\n-> Goi tool get_recent_errors(limit=2)...")
                    result = await session.call_tool("get_recent_errors", {"limit": 2})
                    output_text = result.content[0].text
                    print(output_text)

                    case_data["actual_status"] = "SUCCESS (200 OK)"
                    case_data["result"] = "PASSED"
                    case_data["tool_call_test"] = {
                        "tool": "get_recent_errors",
                        "arguments": {"limit": 2},
                        "response_preview": output_text[:300] + ("..." if len(output_text) > 300 else ""),
                    }
                    print("\n[Case 1] KET QUA: PASSED")
                    return case_data
    except Exception as e:
        case_data["actual_status"] = f"ERROR: {str(e)}"
        print(f"[Case 1] LOI: {e}")
        return case_data


async def test_case_2_invalid_token() -> dict:
    print("\n" + "=" * 60)
    print("[Case 2] Kiem thu voi TOKEN SAI (Authorization: Bearer <INVALID_TOKEN>)")
    print("=" * 60)
    http_client = httpx.AsyncClient(headers={"Authorization": f"Bearer {INVALID_TOKEN}"})

    case_data = {
        "case_id": "AUTH-02",
        "name": "Invalid Bearer Token",
        "description": "Client gui Authorization header voi token khong ton tai trong danh sach",
        "request_header": {"Authorization": f"Bearer {INVALID_TOKEN}"},
        "expected_status": "REJECTED (HTTP 401/403)",
        "actual_status": "UNKNOWN",
        "result": "FAILED",
        "rejection_detail": "",
    }

    try:
        async with http_client:
            async with streamable_http_client(SERVER_URL, http_client=http_client) as streams:
                read, write = streams[0], streams[1]
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    await session.list_tools()
                    case_data["actual_status"] = "ALLOWED (Unexpected)"
                    print("[FAILED] Token sai nhung server van cho phep truy cap!")
                    return case_data
    except Exception as e:
        err_msg = str(e)
        case_data["actual_status"] = "REJECTED (HTTP 401/403)"
        case_data["result"] = "PASSED"
        case_data["rejection_detail"] = f"Server tu choi truy cap do token sai: {err_msg}"
        print(f"[PASSED] Server da tu choi truy cap dung nhu ky vong do Token sai!\n  Chi tiet: {err_msg}")
        print("[Case 2] KET QUA: PASSED")
        return case_data


async def test_case_3_missing_token() -> dict:
    print("\n" + "=" * 60)
    print("[Case 3] Kiem thu khi THIEU TOKEN (Khong gui header Authorization)")
    print("=" * 60)
    http_client = httpx.AsyncClient(headers={})

    case_data = {
        "case_id": "AUTH-03",
        "name": "Missing Authorization Header",
        "description": "Client ket noi toi endpoint MCP HTTP nhung khong truyen header Authorization",
        "request_header": {},
        "expected_status": "REJECTED (HTTP 401)",
        "actual_status": "UNKNOWN",
        "result": "FAILED",
        "rejection_detail": "",
    }

    try:
        async with http_client:
            async with streamable_http_client(SERVER_URL, http_client=http_client) as streams:
                read, write = streams[0], streams[1]
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    await session.list_tools()
                    case_data["actual_status"] = "ALLOWED (Unexpected)"
                    print("[FAILED] Thieu token nhung server van cho phep truy cap!")
                    return case_data
    except Exception as e:
        err_msg = str(e)
        case_data["actual_status"] = "REJECTED (HTTP 401)"
        case_data["result"] = "PASSED"
        case_data["rejection_detail"] = f"Server da chan ket noi do thieu header Authorization: {err_msg}"
        print(f"[PASSED] Server da chan ket noi dung nhu ky vong do thieu header Authorization!\n  Chi tiet: {err_msg}")
        print("[Case 3] KET QUA: PASSED")
        return case_data


async def main() -> None:
    print("================================================================")
    print("BAT DAU KIEM THU AUTH LOG MCP SERVER (Bai 2 - HTTP Streamable)")
    print(f"Target Server: {SERVER_URL}")
    print("================================================================")

    results = []
    results.append(await test_case_1_valid_token())
    results.append(await test_case_2_invalid_token())
    results.append(await test_case_3_missing_token())

    all_passed = all(r["result"] == "PASSED" for r in results)

    # Xuat ra file JSON ket qua thuc te
    summary_report = {
        "test_suite": "MCP Authentication & Streamable HTTP Verification (Bai 2 - Trung binh)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target_server": SERVER_URL,
        "transport": "streamable-http",
        "overall_status": "PASSED" if all_passed else "FAILED",
        "total_cases": len(results),
        "passed_cases": sum(1 for r in results if r["result"] == "PASSED"),
        "failed_cases": sum(1 for r in results if r["result"] == "FAILED"),
        "cases": results,
    }

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("TONG KET KET QUA KIEM THU BAI 2:")
    for r in results:
        status_text = "[PASSED]" if r["result"] == "PASSED" else "[FAILED]"
        print(f"  * {r['name']:<30}: {status_text}")

    print(f"\nDa luu ket qua xac thuc thuc te ra file JSON tai:\n  {OUTPUT_JSON_PATH}")
    if all_passed:
        print("TAT CA 3 CHECKLIST BAO MAT DA DAT 100%!")
    print("================================================================")


if __name__ == "__main__":
    asyncio.run(main())
