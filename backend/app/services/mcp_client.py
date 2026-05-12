import logging
import os
import time
from typing import Optional, Dict, Any, List
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class RemoteMCPClient:
    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url
        self.api_key = api_key
        self.session_id = None
        self.tools = {}
        self._initialize()

    def _initialize(self):
        logger.info(f"初始化远程MCP服务器: {self.server_url}")
        try:
            self._handshake()
            self._notify_initialized()
            self._discover_tools()
            logger.info(f"MCP工具初始化成功，发现 {len(self.tools)} 个工具")
        except Exception as e:
            logger.error(f"MCP工具初始化失败: {e}")

    def _headers(self) -> dict:
        h = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if self.session_id:
            h["Mcp-Session-Id"] = self.session_id
        return h

    def _handshake(self):
        logger.debug("开始MCP握手...")
        response = httpx.post(
            self.server_url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "trip-planner", "version": "1.0"},
                }
            },
            headers=self._headers(),
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise RuntimeError(data["error"].get("message", "握手失败"))
        self.session_id = response.headers.get("Mcp-Session-Id")
        logger.debug(f"握手成功，Session ID: {self.session_id[:16]}...")

    def _notify_initialized(self):
        httpx.post(
            self.server_url,
            json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            headers=self._headers(),
            timeout=10.0,
        )

    def _discover_tools(self):
        logger.debug("开始发现MCP工具...")
        if not self.session_id:
            logger.warning("没有Session ID，跳过工具发现")
            return

        try:
            response = httpx.post(
                self.server_url,
                json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
                headers=self._headers(),
                timeout=30.0,
            )
            response.raise_for_status()

            data = response.json()
            if "result" in data and "tools" in data["result"]:
                for tool in data["result"]["tools"]:
                    tool_name = tool.get("name", "")
                    self.tools[tool_name] = tool
                    logger.debug(f"发现工具: {tool_name}")
            else:
                logger.warning("工具列表为空或格式未知")
        except Exception as e:
            logger.warning(f"工具发现失败: {e}")

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if not self.session_id:
            return "错误：未建立MCP会话"

        for attempt in range(3):
            try:
                response = httpx.post(
                    self.server_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": int(time.time() * 1000),
                        "method": "tools/call",
                        "params": {"name": tool_name, "arguments": arguments}
                    },
                    headers=self._headers(),
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()

                if "result" in data:
                    content = data["result"].get("content", [])
                    if content and isinstance(content, list):
                        return content[0].get("text", "工具调用返回空结果")
                    return str(data["result"])
                elif "error" in data:
                    return f"错误: {data['error'].get('message', '未知错误')}"

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    logger.warning("MCP会话过期，重新握手...")
                    try:
                        self._handshake()
                        self._notify_initialized()
                        continue
                    except Exception:
                        pass
                logger.warning(f"MCP HTTP错误 (尝试 {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(1)
            except Exception as e:
                logger.warning(f"MCP工具调用异常 (尝试 {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(1)

        return "工具暂时不可用，请稍后重试"

    def get_tool(self, tool_name: str) -> Optional[Dict]:
        return self.tools.get(tool_name)

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())


class MCPClient:
    def __init__(self):
        self.amap_tool = None
        self._initialize_amap()

    def _initialize_amap(self):
        logger.info("初始化高德地图MCP...")
        amap_key = getattr(settings, 'AMAP_MAPS_API_KEY', None) or getattr(settings, 'AMAP_API_KEY', '')
        mcp_url = os.getenv("AMAP_MCP_URL", "https://mcp.api-inference.modelscope.net/48a471a61b394f/mcp")

        logger.info(f"MCP服务器: {mcp_url}, API Key: {'***' if amap_key else '未设置'}")

        try:
            self.amap_tool = RemoteMCPClient(mcp_url, amap_key)
        except Exception as e:
            logger.error(f"MCP初始化失败: {e}")
            self.amap_tool = None

    def search_poi(self, keywords: str, city: str, types: str = "") -> str:
        if not self.amap_tool:
            return "错误：高德地图工具未初始化"
        return self.amap_tool.call_tool("maps_text_search", {
            "keywords": keywords,
            "city": city,
            "citylimit": "false"
        })

    def get_weather(self, city: str) -> str:
        if not self.amap_tool:
            return "错误：高德地图工具未初始化"
        result = self.amap_tool.call_tool("maps_weather", {
            "city": city
        })
        return result

    def get_distance(self, origin: str, destination: str) -> str:
        if not self.amap_tool:
            return "错误：高德地图工具未初始化"
        return self.amap_tool.call_tool("maps_distance", {
            "origins": origin,
            "destination": destination,
            "type": "1"
        })

    def get_route_driving(self, origin: str, destination: str) -> str:
        if not self.amap_tool:
            return "错误：高德地图工具未初始化"
        return self.amap_tool.call_tool("maps_direction_driving_by_coordinates", {
            "origin": origin,
            "destination": destination
        })
