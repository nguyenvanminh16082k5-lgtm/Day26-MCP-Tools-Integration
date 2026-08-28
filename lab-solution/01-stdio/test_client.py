"""Test Client cho Log Analyzer MCP Server (Bài 1 - Dễ).

Client kết nối tới log_server.py qua stdio transport:
1. Khám phá các tools qua session.list_tools()
2. Kiểm thử gọi tool `get_recent_errors`
3. Kiểm thử gọi tool `search_logs` với các từ khóa thực tế
"""

import asyncio
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server_script = str(Path(__file__).parent / "log_server.py")
    params = StdioServerParameters(command=sys.executable, args=[server_script])

    print("================================================================")
    print("🚀 Bắt đầu kiểm thử Log Analyzer MCP Server (Bài 1 - stdio)")
    print("================================================================")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. KHÁM PHÁ TOOLS
            print("\n📋 1. Khám phá Tools server công bố (session.list_tools):")
            tools_response = await session.list_tools()
            for t in tools_response.tools:
                schema = getattr(t, "input_schema", None) or getattr(t, "inputSchema", None) or {}
                properties = schema.get("properties", {})
                print(f"\n  🔧 Tool: {t.name}")
                print(f"     Mô tả: {t.description.strip().splitlines()[0]}")
                print(f"     Schema params: {list(properties.keys())}")

            # 2. KIỂM THỬ TOOL get_recent_errors
            print("\n" + "=" * 60)
            print("🧪 2. Kiểm thử get_recent_errors(limit=3):")
            res_errors = await session.call_tool("get_recent_errors", {"limit": 3})
            print(res_errors.content[0].text)

            # 3. KIỂM THỬ TOOL search_logs (Lọc theo từ khóa database timeout)
            print("\n" + "=" * 60)
            print("🧪 3. Kiểm thử search_logs(keyword='psycopg2', level='ERROR'):")
            res_db = await session.call_tool("search_logs", {"keyword": "psycopg2", "level": "ERROR"})
            print(res_db.content[0].text)

            # 4. KIỂM THỬ TOOL search_logs (Truy vết User usr_1042)
            print("\n" + "=" * 60)
            print("🧪 4. Kiểm thử search_logs(keyword='usr_1042'):")
            res_user = await session.call_tool("search_logs", {"keyword": "usr_1042"})
            print(res_user.content[0].text)

            print("\n" + "=" * 60)
            print("✅ HOÀN THÀNH TẤT CẢ TEST CASES CHO BÀI 1 (stdio)!")
            print("================================================================")


if __name__ == "__main__":
    asyncio.run(main())
