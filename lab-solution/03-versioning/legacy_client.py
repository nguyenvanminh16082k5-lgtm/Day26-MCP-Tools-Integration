"""Legacy Client - Dai dien cho Client cu chi biet goi Tool v1 (Bai 3 - Kho).

Kiem chung tinh tuong thich nguoc:
Client nay KHONG biet ve server://info hay get_recent_errors_v2.
No chi goi get_recent_errors (v1) va van nhan duoc plain text chuoi string binh thuong,
khong bi exception hay break code.
"""

import asyncio
import sys
from pathlib import Path

# Ho tro UTF-8 tren Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_legacy_client() -> dict:
    server_script = str(Path(__file__).parent / "versioned_log_server.py")
    params = StdioServerParameters(command=sys.executable, args=[server_script])

    print("================================================================")
    print("CHAY LEGACY CLIENT (Gia lap Client cu chi biet goi Tool v1)")
    print("================================================================")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("-> Legacy Client goi tool cu: get_recent_errors(limit=2)...")
            result = await session.call_tool("get_recent_errors", {"limit": 2})
            output_text = result.content[0].text

            print("\n[Ket qua phan hoi cho Legacy Client]:")
            print(output_text)

            is_plain_text = isinstance(output_text, str) and output_text.startswith("=== [v1 Legacy]")
            print(f"\n[Kiem chung] Client cu van nhan dung dinh dang text string: {is_plain_text}")
            print("KET QUA: PASSED (Khong bi break)")
            print("================================================================")

            return {
                "client_type": "legacy_v1",
                "called_tool": "get_recent_errors",
                "status": "PASSED",
                "response_type": "plain_text",
                "preview": output_text[:200],
            }


if __name__ == "__main__":
    asyncio.run(run_legacy_client())
