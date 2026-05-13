import json
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any, List
from app.services.llm import HelloAgentsLLM
from app.services.mcp_client import MCPClient
from app.models.schemas import TripPlanRequest, TripPlan, Budget
from app.agents.prompts import (
    ATTRACTION_AGENT_PROMPT,
    WEATHER_AGENT_PROMPT,
    HOTEL_AGENT_PROMPT,
    PLANNER_AGENT_PROMPT,
)

logger = logging.getLogger(__name__)


class ToolAwareAgent:
    """具备工具调用能力的智能体，支持多轮思考-行动循环"""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm: HelloAgentsLLM,
        mcp_client: Optional[MCPClient] = None,
        max_iterations: int = 5
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


class TripPlannerAgent:
    """
    旅行规划智能体系统

    该系统采用Multi-Agent架构，通过多个专业Agent协作完成旅行规划任务。

    Agent分工:
        - attraction_agent: 负责搜索景点信息
        - weather_agent: 负责查询天气预报
        - hotel_agent: 负责搜索酒店信息
        - planner_agent: 负责综合信息生成行程

    工作流程:
        1. 并行调用三个专业Agent获取信息
        2. 将获取的信息汇总后调用规划Agent
        3. 规划Agent生成结构化的旅行计划

    Attributes:
        llm: LLM服务实例，用于Agent的推理和生成
        mcp_client: MCP客户端，用于调用外部工具(高德地图API)
        attraction_agent: 景点搜索专家Agent
        weather_agent: 天气查询专家Agent
        hotel_agent: 酒店推荐专家Agent
        planner_agent: 行程规划专家Agent
    """
    def __init__(self):
        logger.info("初始化旅行规划智能体系统...")
        self.llm = HelloAgentsLLM()
        self.mcp_client = MCPClient()

        self.attraction_agent = ToolAwareAgent(
            name="景点搜索专家",
            system_prompt=ATTRACTION_AGENT_PROMPT,
            llm=self.llm,
            mcp_client=self.mcp_client
        )

        self.weather_agent = ToolAwareAgent(
            name="天气查询专家",
            system_prompt=WEATHER_AGENT_PROMPT,
            llm=self.llm,
            mcp_client=self.mcp_client
        )

        self.hotel_agent = ToolAwareAgent(
            name="酒店推荐专家",
            system_prompt=HOTEL_AGENT_PROMPT,
            llm=self.llm,
            mcp_client=self.mcp_client
        )

        self.planner_agent = ToolAwareAgent(
            name="行程规划专家",
            system_prompt="""你是经验丰富的旅行规划师。根据已收集的信息生成完整的旅行计划。

**重要：你不需要调用任何工具，所有信息已提供给你。**

规划原则：
1. 每天2-3个景点，按地理位置就近安排
2. 包含早中晚三餐
3. 根据天气调整安排
4. 预算分配合理

最后必须严格按JSON格式输出，不要包含其他文字。""",
            llm=self.llm,
            mcp_client=None
        )

        logger.info("旅行规划智能体系统初始化完成")

    def search_attractions(self, city: str, preferences: str) -> str:
        logger.info(f"搜索{city}的{preferences}景点...")
        query = f"请搜索{city}的{preferences}景点，返回景点名称、地址、评分和门票价格等信息。"
        return self.attraction_agent.run(query)

    def query_weather(self, city: str) -> str:
        logger.info(f"查询{city}的天气...")
        query = f"请查询{city}的天气预报，返回未来几天的天气情况。"
        return self.weather_agent.run(query)

    def search_hotels(self, city: str, accommodation: str, budget: str = "中等") -> str:
        logger.info(f"搜索{city}的{accommodation}（预算：{budget}）...")
        query = f"请搜索{city}的{accommodation}，预算档位：{budget}，返回酒店名称、地址、价格范围、评分和亮点等信息。"
        return self.hotel_agent.run(query)

    def generate_plan(
        self,
        request: TripPlanRequest,
        attraction_info: str,
        weather_info: str,
        hotel_info: str
    ) -> str:
        logger.info("生成旅行计划...")

        query = PLANNER_AGENT_PROMPT.format(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=request.days,
            preferences=request.preferences,
            budget=request.budget,
            transportation=request.transportation,
            accommodation=request.accommodation,
            attraction_info=attraction_info,
            weather_info=weather_info,
            hotel_info=hotel_info,
        )

        result = self.planner_agent.run(query, show_thinking=True)
        logger.info("计划生成完成")
        return result

    def parse_json_response(self, response: str) -> Optional[dict]:
        """
        从LLM响应中提取JSON数据

        LLM返回的文本可能包含多个JSON块或嵌入在其他内容中，
        该方法通过多种正则模式尝试解析出有效的旅行计划JSON。

        Args:
            response: LLM返回的原始文本

        Returns:
            解析后的旅行计划字典，如果解析失败则返回None

        正则模式优先级:
            1. ```json ... ``` 格式
            2. ``` ... ``` 格式
            3. 任意 {...} 格式

        验证条件:
            - 必须包含"city"字段
            - 必须包含"days"字段
        """
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[\s\S]*\})'
        ]
        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    parsed = json.loads(match)
                    if "city" in parsed and "days" in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue
        return None

    def plan_trip(self, request: TripPlanRequest) -> TripPlan:
        logger.info(f"开始规划: {request.city} {request.days}天行程")

        # 并行执行三个信息收集 Agent
        attraction_info = ""
        weather_info = ""
        hotel_info = ""

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self.search_attractions, request.city, request.preferences): "attractions",
                executor.submit(self.query_weather, request.city): "weather",
                executor.submit(self.search_hotels, request.city, request.accommodation, request.budget): "hotels",
            }
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    result = future.result(timeout=120)
                    if task_name == "attractions":
                        attraction_info = result
                    elif task_name == "weather":
                        weather_info = result
                    elif task_name == "hotels":
                        hotel_info = result
                    logger.info(f"{task_name} Agent 完成")
                except Exception as e:
                    logger.error(f"{task_name} Agent 失败: {e}")

        # 生成旅行计划
        logger.info("生成旅行计划...")
        plan_response = self.generate_plan(request, attraction_info, weather_info, hotel_info)

        plan_data = self.parse_json_response(plan_response)
        if plan_data:
            logger.info("旅行计划生成成功")
            return TripPlan(**plan_data)
        else:
            logger.warning("JSON解析失败，返回空计划")
            return TripPlan(
                city=request.city,
                start_date=request.start_date,
                end_date=request.end_date,
                days=[],
                weather_info=[],
                overall_suggestions="抱歉，无法生成旅行计划，请稍后重试。"
            )

    def update_budget(self, trip_plan: TripPlan) -> TripPlan:
        """
        更新行程预算
        """
        total_attractions = 0
        total_hotels = 0
        total_meals = 0
        total_transportation = 0

        for day in trip_plan.days:
            # 计算景点门票费用
            for attraction in day.attractions:
                total_attractions += attraction.ticket_price or 0

            # 计算酒店费用
            if day.hotel:
                total_hotels += day.hotel.estimated_cost or 0

            # 计算餐饮费用
            for meal in day.meals:
                total_meals += meal.estimated_cost or 0

        # 计算交通费用（按每天50元估算）
        total_transportation = len(trip_plan.days) * 50

        total = total_attractions + total_hotels + total_meals + total_transportation

        # 更新预算
        trip_plan.budget = Budget(
            total_attractions=total_attractions,
            total_hotels=total_hotels,
            total_meals=total_meals,
            total_transportation=total_transportation,
            total=total
        )

        return trip_plan
