import subprocess
import json
import os
import time
from typing import Optional, Dict, Any, List
from app.config import settings

class MCPTool:
    def __init__(self, name: str, command: str, args: List[str], env: Dict[str, str], auto_expand: bool = True, max_retries: int = 3):
        self.name = name
        self.command = command
        self.args = args
        self.env = {**os.environ, **env}
        self.auto_expand = auto_expand
        self.max_retries = max_retries
        self.process = None
        self.tools = {}
        self._initialize()

    def _initialize(self):
        print(f"🔧 初始化MCP工具: {self.name}")
        for attempt in range(self.max_retries):
            try:
                self.process = subprocess.Popen(
                    [self.command] + self.args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=self.env,
                    text=True,
                    bufsize=1
                )
                time.sleep(0.5)  # 等待进程启动
                if self.auto_expand:
                    self._discover_tools()
                print(f"✅ MCP工具初始化成功")
                return
            except Exception as e:
                print(f"⚠️ MCP工具初始化失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if self.process:
                    self.process.terminate()
                    self.process = None
                if attempt < self.max_retries - 1:
                    time.sleep(1)  # 等待后重试
        print(f"❌ MCP工具初始化最终失败")

    def _discover_tools(self):
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        response = self._send_request(request)
        if response and "result" in response:
            tools = response["result"].get("tools", [])
            for tool in tools:
                tool_name = tool.get("name", "")
                self.tools[tool_name] = tool
                print(f"  ✅ 发现工具: {tool_name}")
        else:
            print(f"  ⚠️ 未发现工具列表")

    def _send_request(self, request: Dict[str, Any]) -> Optional[Dict]:
        if not self.process or self.process.poll() is not None:
            print(f"❌ MCP进程不可用")
            return None
        try:
            request_str = json.dumps(request) + "\n"
            self.process.stdin.write(request_str)
            self.process.stdin.flush()
            # 等待响应，增加超时处理
            import select
            if select.select([self.process.stdout], [], [], 5)[0]:  # 5秒超时
                response_str = self.process.stdout.readline()
                if response_str:
                    return json.loads(response_str)
            else:
                print(f"⚠️ MCP请求超时")
        except Exception as e:
            print(f"❌ MCP请求失败: {e}")
        return None

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """调用工具，带重试机制"""
        for attempt in range(self.max_retries):
            try:
                request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                response = self._send_request(request)
                if response and "result" in response:
                    content = response["result"].get("content", [])
                    if content and isinstance(content, list):
                        result = content[0].get("text", "")
                        if result and result != "工具调用失败":
                            return result
                        else:
                            print(f"⚠️ 工具返回空结果 (尝试 {attempt + 1}/{self.max_retries})")
                    else:
                        print(f"⚠️ 工具返回格式错误 (尝试 {attempt + 1}/{self.max_retries})")
                else:
                    print(f"⚠️ 工具调用失败 (尝试 {attempt + 1}/{self.max_retries})")
                
                # 重试前等待
                if attempt < self.max_retries - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"❌ 工具调用异常 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(0.5)
        
        return "工具暂时不可用，请稍后重试"

    def get_tool(self, tool_name: str) -> Optional[Dict]:
        return self.tools.get(tool_name)

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def __del__(self):
        if self.process:
            self.process.terminate()


class MCPClient:
    def __init__(self):
        self.amap_tool = None
        self._initialize_amap()

    def _initialize_amap(self):
        print("🔧 初始化高德地图MCP...")
        self.amap_tool = MCPTool(
            name="amap_mcp",
            command="npx",
            args=["-y", "@sugarforever/amap-mcp-server"],
            env={"AMAP_API_KEY": settings.AMAP_API_KEY},
            auto_expand=True
        )

    def search_poi(self, keywords: str, city: str, types: str = "") -> str:
        if not self.amap_tool:
            return "错误：高德地图工具未初始化"
        return self.amap_tool.call_tool("amap_maps_text_search", {
            "keywords": keywords,
            "city": city,
            "types": types
        })

    def get_weather(self, city: str) -> str:
        if not self.amap_tool:
            return "错误：高德地图工具未初始化"
        return self.amap_tool.call_tool("amap_maps_weather", {
            "city": city
        })

    def get_distance(self, origin: str, destination: str) -> str:
        if not self.amap_tool:
            return "错误：高德地图工具未初始化"
        return self.amap_tool.call_tool("amap_maps_distance", {
            "origin": origin,
            "destination": destination
        })

    def get_route_driving(self, origin: str, destination: str) -> str:
        if not self.amap_tool:
            return "错误：高德地图工具未初始化"
        return self.amap_tool.call_tool("amap_maps_driving", {
            "origin": origin,
            "destination": destination
        })
