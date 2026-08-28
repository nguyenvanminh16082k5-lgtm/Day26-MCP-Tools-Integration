"""MCP SERVER minh hoạ — công bố tool `get_weather` qua giao thức MCP.

Khác với function calling: tool nằm ở một server ĐỘC LẬP. Server tự "khai
báo" tool của mình; bất kỳ MCP client nào (Claude Code, Claude Desktop,
Cursor, hoặc weather_client.py) cũng cắm vào dùng được mà không cần biết
code bên trong.

Schema của tool được TỰ ĐỘNG sinh ra từ type hints + docstring.

Chạy trực tiếp:
    pip install -r ../requirements.txt
    python weather_server.py

Đăng ký với Claude Code (làm 1 lần, dùng mãi):
    claude mcp add weather -- python /đường/dẫn/tới/weather_server.py
"""

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("weather")

_MOCK_DB = {
    "Hanoi": "29°C, trời mưa",
    "Haiphong": "33°C, mưa rào",
    "Danang": "30°C, nhiều mây",
}

_MOCK_NEWS = {
    "Hanoi": "nghỉ lễ, không có tin tức mới",
    "Haiphong": "nghỉ lễ, không có tin tức mới",
    "Danang": "nghỉ lễ, không có tin tức mới",
}


_MOCK_SINGER = {
    "Sơn Tùng M-TP": {
        "name": "Sơn Tùng M-TP",
        "age": 29,
        "gender": "male",
        "country": "Vietnam",
    },
    "Bích Phương": {
        "name": "Bích Phương",
        "age": 33,
        "gender": "female",
        "country": "Vietnam",
    },
    "Taylor Swift": {
        "name": "Taylor Swift",
        "age": 30,
        "gender": "female",
        "country": "USA",
    },
}

@mcp.tool()
def get_weather(city: str) -> str:
    """Lấy thời tiết hiện tại của một thành phố."""
    return f"{city}: {_MOCK_DB.get(city, '28°C, không có dữ liệu chi tiết')}"

@mcp.tool()
def get_news(city: str) -> str:
    """Lấy thông tin tin tức, thời sự của một thành phố."""
    return f"{city}: {_MOCK_NEWS.get(city, 'nghỉ lễ, không có tin tức mới')}"

@mcp.tool()
def get_singer(name: str) -> str:
    """Lấy thông tin ca sĩ."""
    return f"{name}: {_MOCK_SINGER.get(name, 'không có dữ liệu')}"

if __name__ == "__main__":
    mcp.run()  # mặc định chạy qua stdio
