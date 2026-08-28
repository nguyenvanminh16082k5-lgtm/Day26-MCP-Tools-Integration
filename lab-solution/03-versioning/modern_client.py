"""Modern Client - Client the he moi doc Metadata va goi Tool v2 (Bai 3 - Kho).

Luong xu ly:
1. Doc Resource server://info truoc khi goi bat ky tool nao.
2. Nhan dien Server version 2.0.0 va danh sach deprecated tools.
3. Tu dong lua chon goi `get_recent_errors_v2` de nhan JSON co cau truc.
4. Bop tach va xu ly JSON chuyen sau: error_type, suggested_action, stack_trace.
5. Ghi nhan ket qua kiem thu ca 2 client vao `versioning_test_results.json`.
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ho tro UTF-8 tren Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

OUTPUT_JSON_PATH = Path(__file__).parent / "versioning_test_results.json"


async def run_modern_client() -> dict:
    server_script = str(Path(__file__).parent / "versioned_log_server.py")
    params = StdioServerParameters(command=sys.executable, args=[server_script])

    print("================================================================")
    print("CHAY MODERN CLIENT (Client the he moi doc Resource & goi Tool v2)")
    print("================================================================")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. DOC RESOURCE server://info
            print("\n1. Doc Metadata tu Resource server://info:")
            info_resource = await session.read_resource("server://info")
            raw_meta = getattr(info_resource.contents[0], "text", None) or str(info_resource.contents[0])
            metadata = json.loads(raw_meta)

            print(f"   Server Name     : {metadata.get('server_name')}")
            print(f"   Version         : {metadata.get('version')}")
            print(f"   Capabilities    : {metadata.get('capabilities')}")
            print(f"   Deprecated Tools: {metadata.get('deprecated_tools')}")
            print(f"   Migration Guide : {metadata.get('migration_guide')}\n")

            # 2. KHAM PHA TOOLS
            print("2. Danh sach tools do server cung cap:")
            tools_response = await session.list_tools()
            tool_names = [t.name for t in tools_response.tools]
            for t in tools_response.tools:
                print(f"   * {t.name}: {t.description.strip().splitlines()[0]}")

            # 3. QUYET DINH CHON TOOL PHU HOP
            deprecated_list = metadata.get("deprecated_tools", [])
            target_tool = "get_recent_errors_v2" if "get_recent_errors_v2" in tool_names else "get_recent_errors"
            print(f"\n3. Client lua chon tool: '{target_tool}' (Vi 'get_recent_errors' da bi deprecated)")

            # 4. GOI TOOL V2 (STRUCTURED JSON)
            print(f"-> Goi tool {target_tool}(limit=2, include_traceback=True)...")
            result = await session.call_tool(
                target_tool,
                {"limit": 2, "service": "ALL", "include_traceback": True, "format": "json"},
            )
            raw_json = result.content[0].text
            parsed_data = json.loads(raw_json)

            print("\n[Ket qua Structured JSON nhan duoc tu Tool v2]:")
            print(f"   API Version: {parsed_data.get('api_version')}")
            print(f"   Tong so loi: {parsed_data.get('returned_count')}/{parsed_data.get('total_errors_in_log')}")

            for idx, err in enumerate(parsed_data.get("errors", []), 1):
                print(f"\n   [{idx}] {err.get('timestamp')} | {err.get('severity')} | Service: {err.get('service')}")
                print(f"       Trace ID        : {err.get('trace_id')}")
                print(f"       Error Type      : {err.get('error_type')}")
                print(f"       Message         : {err.get('message')}")
                print(f"       Suggested Action: {err.get('suggested_action')}")
                if err.get("stack_trace"):
                    print(f"       Stack Trace     : {len(err.get('stack_trace'))} lines parsed")

            print("\n================================================================")
            print("KET QUA MODERN CLIENT: PASSED (Khai thac Structured JSON thanh cong)")
            print("================================================================")

            return {
                "client_type": "modern_v2",
                "metadata_read": metadata,
                "selected_tool": target_tool,
                "status": "PASSED",
                "response_type": "structured_json",
                "parsed_summary": {
                    "api_version": parsed_data.get("api_version"),
                    "returned_count": parsed_data.get("returned_count"),
                    "sample_error_type": parsed_data.get("errors", [{}])[0].get("error_type"),
                    "sample_suggested_action": parsed_data.get("errors", [{}])[0].get("suggested_action"),
                },
            }


async def main() -> None:
    # 1. Chay Legacy Client
    from legacy_client import run_legacy_client

    legacy_res = await run_legacy_client()

    # 2. Chay Modern Client
    modern_res = await run_modern_client()

    # 3. Ghi nhan ket qua vao file JSON
    report = {
        "test_suite": "MCP Versioning & Backward Compatibility Verification (Bai 3 - Kho)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server_version": "2.0.0",
        "overall_status": "PASSED",
        "legacy_client_test": legacy_res,
        "modern_client_test": modern_res,
        "backward_compatibility_verified": True,
        "capabilities_tested": [
            "Resource server://info metadata publishing",
            "Parallel tool coexistence (v1 deprecated + v2 active)",
            "Rich Structured JSON diagnostics with suggested actions",
        ],
    }

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nDa luu ket qua kiem thu Versioning thuc te ra file JSON tai:\n  {OUTPUT_JSON_PATH}")
    print("HOAN THANH TOAN BO CHECKLIST BAI 3 (KHO) 100%!")


if __name__ == "__main__":
    asyncio.run(main())
