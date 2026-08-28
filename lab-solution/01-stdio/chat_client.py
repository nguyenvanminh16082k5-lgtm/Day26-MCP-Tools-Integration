"""MCP Chatbot CLI — Kết hợp Gemini 2.5 Flash và MCP Server (stdio).

Cơ chế hoạt động:
1. Kết nối tới `log_server.py` qua giao thức MCP (stdio).
2. Tự động khám phá tools (session.list_tools) — KHÔNG hard-code schema thủ công.
3. Chuyển đổi linh hoạt schema MCP sang Gemini FunctionDeclaration.
4. Giao diện Chatbot tương tác dòng lệnh (CLI):
   - Người dùng hỏi bằng ngôn ngữ tự nhiên (vd: "Tìm 3 lỗi gần nhất và giải thích nguyên nhân").
   - Gemini (gemini-2.5-flash) tự quyết định gọi MCP tool nào (Function Calling).
   - Client gọi MCP Server thực thi và trả kết quả về cho Gemini tổng hợp.

Cách chạy:
    export GEMINI_API_KEY=your_key_here
    python chat_client.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Hỗ trợ UTF-8 chuẩn trên Windows Console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL_NAME = "gemini-2.5-flash"
SYSTEM_INSTRUCTION = (
    "Bạn là Chuyên gia Kỹ thuật và Vận hành Hệ thống (DevOps & SRE Assistant) thông minh, thân thiện. "
    "Bạn có quyền truy cập vào các công cụ chẩn đoán log hệ thống thông qua MCP Tools. "
    "Khi người dùng hỏi về lỗi, sự cố, hoặc thông tin tra cứu trong log, hãy tự động sử dụng các MCP Tool "
    "phù hợp để trích xuất dữ liệu thực tế, sau đó phân tích nguyên nhân gốc rễ (Root Cause) "
    "và đưa ra khuyến nghị xử lý cụ thể bằng tiếng Việt rõ ràng, dùng emoji trực quan (🚨 🛠️ 🔍 ✅ ⚠️)."
)


def convert_mcp_tool_to_gemini(mcp_tool) -> types.FunctionDeclaration:
    """Chuyển đổi động schema của MCP Tool sang Gemini FunctionDeclaration (hỗ trợ cả MCP 1.x và 2.x)."""
    # Hỗ trợ cả input_schema (MCP 2.x) và inputSchema (MCP 1.x)
    schema = getattr(mcp_tool, "input_schema", None) or getattr(mcp_tool, "inputSchema", None) or {}
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    gemini_properties = {}
    for prop_name, prop_meta in properties.items():
        p_type = prop_meta.get("type", "string")
        if p_type == "integer":
            g_type = types.Type.INTEGER
        elif p_type == "boolean":
            g_type = types.Type.BOOLEAN
        elif p_type == "number":
            g_type = types.Type.NUMBER
        else:
            g_type = types.Type.STRING

        gemini_properties[prop_name] = types.Schema(
            type=g_type,
            description=prop_meta.get("description", f"Tham số {prop_name}"),
        )

    return types.FunctionDeclaration(
        name=mcp_tool.name,
        description=mcp_tool.description or f"Tool {mcp_tool.name}",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties=gemini_properties,
            required=required_fields,
        ),
    )


async def ask_gemini_with_mcp(
    client: genai.Client,
    session: ClientSession,
    gemini_tools: list[types.Tool],
    conversation_history: list[types.Content],
    user_prompt: str,
) -> str:
    """Gửi câu hỏi tới Gemini, tự động điều phối vòng lặp Function Calling qua MCP Server."""
    conversation_history.append(
        types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])
    )

    # 1. Gọi model Gemini
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=conversation_history,
        config=types.GenerateContentConfig(
            tools=gemini_tools,
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )

    # 2. Vòng lặp Function Calling: Nếu Gemini yêu cầu gọi tool
    while resp.function_calls:
        conversation_history.append(resp.candidates[0].content)
        function_responses = []

        for fc in resp.function_calls:
            print(f"\n  🤖 [AI Quyết định gọi MCP Tool] {fc.name}({fc.args})")
            try:
                # GỌI QUA GIAO THỨC MCP TỚI SERVER THẬT
                tool_result = await session.call_tool(fc.name, fc.args or {})
                output_text = tool_result.content[0].text
                preview = output_text[:180].replace("\n", " ") + ("..." if len(output_text) > 180 else "")
                print(f"  ⚡ [MCP Server trả về] {preview}")
            except Exception as e:
                output_text = f"Lỗi khi thực thi tool {fc.name}: {e}"
                print(f"  ❌ [MCP Server Error] {output_text}")

            function_responses.append(
                types.Part.from_function_response(
                    name=fc.name,
                    response={"result": output_text},
                )
            )

        # Gửi dữ liệu log từ MCP Server ngược lại cho Gemini tổng hợp
        conversation_history.append(types.Content(role="user", parts=function_responses))
        resp = client.models.generate_content(
            model=MODEL_NAME,
            contents=conversation_history,
            config=types.GenerateContentConfig(
                tools=gemini_tools,
                system_instruction=SYSTEM_INSTRUCTION,
            ),
        )

    # 3. Kết quả tổng hợp cuối cùng từ AI
    final_reply = resp.text or "Không có phản hồi từ mô hình."
    conversation_history.append(resp.candidates[0].content)
    return final_reply


async def run_cli() -> None:
    # Kiểm tra API Key
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("\n❌ LỖI: Chưa cấu hình GEMINI_API_KEY!")
        print("   Vui lòng cấu hình trong file .env hoặc chạy lệnh:")
        print("   export GEMINI_API_KEY=your_api_key_here  (Linux/Mac)")
        print("   $env:GEMINI_API_KEY=\"your_api_key_here\"  (PowerShell)\n")
        return

    gemini_client = genai.Client(api_key=api_key)
    server_script = str(Path(__file__).parent / "log_server.py")
    params = StdioServerParameters(command=sys.executable, args=[server_script])

    print("=" * 65)
    print("🤖 LOG ANALYZER AI CHATBOT (Gemini 2.5 Flash + MCP stdio)")
    print("=" * 65)
    print("📡 Đang kết nối tới MCP Log Server...")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Khám phá dynamic tools từ MCP Server
            tools_data = await session.list_tools()
            declarations = [convert_mcp_tool_to_gemini(t) for t in tools_data.tools]
            gemini_tools = [types.Tool(function_declarations=declarations)]

            print(f"✅ Đã kết nối MCP Server thành công! Khám phá được {len(declarations)} tools:")
            for d in declarations:
                print(f"   • {d.name}: {d.description.strip().splitlines()[0]}")

            print("\n💡 Gợi ý câu hỏi:")
            print("   - Tìm cho tôi 3 lỗi gần nhất trong file log và phân tích nguyên nhân.")
            print("   - Kiểm tra xem user usr_1042 đã gặp vấn đề gì khi đặt hàng?")
            print("   - Hệ thống có bị lỗi thanh toán Stripe hay database timeout không?")
            print("   - Gõ 'exit' hoặc 'quit' để thoát.\n" + "-" * 65)

            conversation_history: list[types.Content] = []

            # Nếu có truyền câu hỏi qua tham số dòng lệnh thì trả lời ngay
            if len(sys.argv) > 1:
                single_question = " ".join(sys.argv[1:])
                print(f"👤 Bạn: {single_question}")
                print("\n🧠 AI đang suy nghĩ & truy xuất MCP Server...")
                reply = await ask_gemini_with_mcp(
                    gemini_client, session, gemini_tools, conversation_history, single_question
                )
                print(f"\n🤖 AI Assistant:\n{reply}\n")
                return

            # Vòng lặp chat tương tác liên tục từ CLI
            while True:
                try:
                    user_input = input("\n👤 Bạn: ").strip()
                    if not user_input:
                        continue
                    if user_input.lower() in ("exit", "quit", "q"):
                        print("👋 Tạm biệt! Hẹn gặp lại.")
                        break

                    print("\n🧠 AI đang suy nghĩ & truy xuất MCP Server...")
                    reply = await ask_gemini_with_mcp(
                        gemini_client, session, gemini_tools, conversation_history, user_input
                    )
                    print(f"\n🤖 AI Assistant:\n{reply}")
                except (KeyboardInterrupt, EOFError):
                    print("\n👋 Đã thoát chương trình.")
                    break


if __name__ == "__main__":
    asyncio.run(run_cli())
