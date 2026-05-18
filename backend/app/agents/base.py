"""
ToolAwareAgent — 具备工具调用能力的智能体基类
支持多轮思考-行动循环（ReAct 范式）
"""
import re
import logging
from typing import Optional, Dict, Any, List

from app.services.llm import HelloAgentsLLM
from app.services.mcp_client import MCPClient

logger = logging.getLogger(__name__)


class ToolAwareAgent:
    """具备工具调用能力的智能体，支持多轮思考-行动循环"""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm: HelloAgentsLLM,
        mcp_client: Optional[MCPClient] = None,
        max_iterations: int = 3
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = llm
        self.mcp_client = mcp_client
        self.max_iterations = max_iterations

    def get_tools_description(self) -> str:
        if not self.mcp_client or not self.mcp_client.amap_tool:
            return "暂无可用工具"

        tools = self.mcp_client.amap_tool.list_tools()
        if not tools:
            return "暂无可用工具"

        lines = ["## 可用工具", "你可以通过以下工具获取信息：\n"]
        for tool_name in tools:
            tool_info = self.mcp_client.amap_tool.get_tool(tool_name)
            if tool_info:
                desc = tool_info.get("description", "无描述")
                params = tool_info.get("inputSchema", {}).get("properties", {})
                param_str = ", ".join(params.keys()) if params else "无参数"
                lines.append(f"- **{tool_name}**({param_str}): {desc}")
        return "\n".join(lines)

    def parse_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        tool_calls = []
        for pattern in [r'\[TOOL_CALL:(\w+):([^\]]+)\]', r'Action:\s*(\w+)\[([^\]]+)\]']:
            for match in re.findall(pattern, text):
                tool_name, tool_args = match
                if tool_name.lower() not in ("finish", "final"):
                    tool_calls.append({
                        "tool_name": tool_name,
                        "tool_args": tool_args.strip(),
                    })
        return tool_calls

    def execute_tool(self, tool_name: str, tool_args: str) -> str:
        if not self.mcp_client or not self.mcp_client.amap_tool:
            return f"错误：工具 {tool_name} 不可用"
        try:
            args_dict = self._parse_args(tool_name, tool_args)
            return self.mcp_client.amap_tool.call_tool(tool_name, args_dict)
        except Exception as e:
            return f"工具调用失败: {e}"

    def _parse_args(self, tool_name: str, tool_args: str) -> Dict[str, Any]:
        if not tool_args.strip():
            return {}

        if "," in tool_args and "=" in tool_args:
            return dict(
                kv.split("=", 1)
                for kv in tool_args.split(",")
                if "=" in kv
            )
        if "=" in tool_args:
            k, v = tool_args.split("=", 1)
            return {k.strip(): v.strip()}

        if tool_name == "amap_maps_text_search":
            return {"keywords": tool_args}
        if tool_name == "amap_maps_weather":
            return {"city": tool_args}
        return {"input": tool_args}

    def _run_without_tools(self, user_input: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]
        return self.llm.think(messages) or "处理失败"

    def run(self, user_input: str, show_thinking: bool = True) -> str:
        if not self.mcp_client:
            return self._run_without_tools(user_input)

        tools_desc = self.get_tools_description()
        full_system_prompt = f"""{self.system_prompt}

{tools_desc}

## 工具调用规则
1. 当需要获取信息时，使用: [TOOL_CALL:工具名:参数]
2. 多参数用逗号分隔: [TOOL_CALL:amap_maps_text_search:keywords=景点,city=北京]
3. 完成时输出最终答案

## 输出格式
Thought: 思考你需要做什么
Action: [TOOL_CALL:工具名:参数] 或 [TOOL_CALL:Finish:]
Observation: （系统自动提供，不要自己填写）"""

        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_input}
        ]

        logger.info(f"{self.name} 开始处理")

        for iteration in range(self.max_iterations):
            logger.info(f"第 {iteration + 1} 轮")

            response = self.llm.think(messages)
            if response is None:
                return "无法获取信息，请检查网络连接或API配置"
            messages.append({"role": "assistant", "content": response})

            tool_calls = self.parse_tool_calls(response)

            if not tool_calls:
                if "Final Answer:" in response or "完成" in response:
                    return self._extract_final_answer(response)
                messages.append({
                    "role": "user",
                    "content": "请继续。如果已完成任务，使用 [TOOL_CALL:Finish:] 结束。"
                })
                continue

            for tc in tool_calls:
                if tc["tool_name"].lower() == "finish":
                    return self._extract_final_answer(response)
                result = self.execute_tool(tc["tool_name"], tc["tool_args"])
                messages.append({"role": "user", "content": f"Observation: {result}"})

        return "抱歉，我在限定次数内无法完成任务。"

    def _extract_final_answer(self, response: str) -> str:
        for marker in ["Final Answer:", "答案:"]:
            if marker in response:
                return response.split(marker)[-1].strip()
        for line in reversed(response.split("\n")):
            if line.strip() and not line.startswith(("Thought", "Action")):
                return line.strip()
        return response.strip()
