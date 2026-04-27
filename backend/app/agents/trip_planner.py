import json
import re
from typing import Optional, Dict, Any, List, Callable
from app.services.llm import HelloAgentsLLM
from app.services.mcp_client import MCPClient
from app.models.schemas import TripPlanRequest, TripPlan, Budget


class ToolAwareAgent:
    """
    具备工具调用能力的智能体
    支持多轮思考-行动循环，让Agent能真正自主调用工具
    """

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
        """获取工具描述字符串，供LLM理解可用工具"""
        if not self.mcp_client or not self.mcp_client.amap_tool:
            return "暂无可用工具"

        tools = self.mcp_client.amap_tool.list_tools()
        if not tools:
            return "暂无可用工具"

        descriptions = []
        descriptions.append("## 可用工具")
        descriptions.append("你可以通过以下工具获取信息：\n")

        for tool_name in tools:
            tool_info = self.mcp_client.amap_tool.get_tool(tool_name)
            if tool_info:
                desc = tool_info.get("description", "无描述")
                input_schema = tool_info.get("inputSchema", {})
                params = input_schema.get("properties", {})
                param_str = ", ".join(params.keys()) if params else "无参数"
                descriptions.append(f"- **{tool_name}**({param_str}): {desc}")

        return "\n".join(descriptions)

    def parse_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """解析文本中的工具调用"""
        tool_calls = []

        patterns = [
            r'\[TOOL_CALL:(\w+):([^\]]+)\]',
            r'Action:\s*(\w+)\[([^\]]+)\]',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                tool_name, tool_args = match
                if tool_name.lower() != "finish" and tool_name != "Final":
                    tool_calls.append({
                        "tool_name": tool_name,
                        "tool_args": tool_args.strip(),
                        "original": f"TOOL_CALL:{tool_name}:{tool_args}"
                    })

        return tool_calls

    def execute_tool(self, tool_name: str, tool_args: str) -> str:
        """执行工具调用"""
        if not self.mcp_client or not self.mcp_client.amap_tool:
            return f"错误：工具 {tool_name} 不可用"

        try:
            args_dict = self._parse_args(tool_name, tool_args)
            result = self.mcp_client.amap_tool.call_tool(tool_name, args_dict)
            return result
        except Exception as e:
            return f"工具调用失败: {str(e)}"

    def _parse_args(self, tool_name: str, tool_args: str) -> Dict[str, Any]:
        """解析工具参数"""
        args = {}

        if not tool_args.strip():
            return args

        if "," in tool_args:
            for param in tool_args.split(","):
                if "=" in param:
                    key, value = param.split("=", 1)
                    args[key.strip()] = value.strip()
        elif "=" in tool_args:
            key, value = tool_args.split("=", 1)
            args[key.strip()] = value.strip()
        else:
            first_param = tool_args.split()[0] if tool_args else ""
            if first_param:
                if tool_name == "amap_maps_text_search":
                    args["keywords"] = tool_args
                elif tool_name == "amap_maps_weather":
                    args["city"] = tool_args
                else:
                    args["input"] = tool_args

        return args

    def _run_without_tools(self, user_input: str, show_thinking: bool = True) -> str:
        """不使用工具的运行模式（直接调用LLM）"""
        if show_thinking:
            print(f"\n🤖 {self.name} 开始处理（无工具模式）...")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]

        response = self.llm.think(messages)
        if show_thinking:
            print(f"✅ 处理完成")
        return response or "处理失败"

    def run(self, user_input: str, show_thinking: bool = True) -> str:
        """
        运行Agent，支持多轮工具调用

        流程：
        1. 构建包含工具描述的提示词
        2. LLM思考并决定是否调用工具
        3. 如果有工具调用，执行工具
        4. 将结果反馈给LLM继续思考
        5. 循环直到LLM给出最终答案
        """
        if not self.mcp_client:
            return self._run_without_tools(user_input, show_thinking)

        tools_desc = self.get_tools_description()

        full_system_prompt = f"""{self.system_prompt}

{tools_desc}

## 工具调用规则
1. 当需要获取信息时，使用工具调用格式: [TOOL_CALL:工具名:参数]
2. 参数用逗号分隔多个参数，如: [TOOL_CALL:amap_maps_text_search:keywords=景点,city=北京]
3. 当获得足够信息时，输出最终答案

## 输出格式
请严格按照以下格式输出：
Thought: 思考你需要做什么
Action: [TOOL_CALL:工具名:参数] 或 [TOOL_CALL:Finish:]
Observation: （系统会自动提供工具结果，不要自己填写）
"""

        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_input}
        ]

        if show_thinking:
            print(f"\n🤖 {self.name} 开始处理...")

        for iteration in range(self.max_iterations):
            if show_thinking:
                print(f"\n--- 第 {iteration + 1} 轮 ---")

            response = self.llm.think(messages)
            if response is None:
                if show_thinking:
                    print("❌ LLM返回失败，使用默认结果")
                return "无法获取信息，请检查网络连接或API配置"
            messages.append({"role": "assistant", "content": response})

            if show_thinking:
                print(f"📝 LLM回复:\n{response[:200]}...")

            tool_calls = self.parse_tool_calls(response)

            if not tool_calls:
                if "Final Answer:" in response or "完成" in response:
                    final_answer = self._extract_final_answer(response)
                    if show_thinking:
                        print(f"✅ 完成!")
                    return final_answer
                if show_thinking:
                    print("⚠️ 未检测到工具调用，引导继续...")
                messages.append({
                    "role": "user",
                    "content": "请继续按照格式输出你的思考和行动。如果已完成任务，使用 [TOOL_CALL:Finish:] 结束。"
                })
                continue

            for tool_call in tool_calls:
                tool_name = tool_call["tool_name"]
                tool_args = tool_call["tool_args"]

                if tool_name.lower() == "finish":
                    final_answer = self._extract_final_answer(response)
                    if show_thinking:
                        print(f"✅ 任务完成!")
                    return final_answer

                if show_thinking:
                    print(f"🔧 执行工具: {tool_name}[{tool_args}]")

                result = self.execute_tool(tool_name, tool_args)

                if show_thinking:
                    print(f"📥 工具返回: {result[:150]}...")

                messages.append({
                    "role": "user",
                    "content": f"Observation: {result}"
                })

        return "抱歉，我在限定次数内无法完成任务。"

    def _extract_final_answer(self, response: str) -> str:
        """提取最终答案"""
        if "Final Answer:" in response:
            return response.split("Final Answer:")[-1].strip()
        if "答案:" in response:
            return response.split("答案:")[-1].strip()
        lines = response.split("\n")
        for line in reversed(lines):
            if line.strip() and not line.startswith("Thought") and not line.startswith("Action"):
                return line.strip()
        return response.strip()


class SimpleAgent:
    """简单的Agent，不支持工具调用"""
    def __init__(self, name: str, system_prompt: str, llm: HelloAgentsLLM):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = llm

    def run(self, user_input: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]
        response = self.llm.think(messages)
        return response or "Agent执行失败"


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
        print("🚀 初始化旅行规划智能体系统...")
        self.llm = HelloAgentsLLM()
        self.mcp_client = MCPClient()

        self.attraction_agent = ToolAwareAgent(
            name="景点搜索专家",
            system_prompt="""你是专业的景点搜索专家。根据用户的偏好，搜索最合适的旅游景点信息。
你需要根据用户需求决定使用哪些工具来获取信息。""",
            llm=self.llm,
            mcp_client=self.mcp_client
        )

        self.weather_agent = ToolAwareAgent(
            name="天气查询专家",
            system_prompt="""你是专业的气象顾问。查询指定城市的天气预报信息。
你需要使用工具来获取准确的天气数据。""",
            llm=self.llm,
            mcp_client=self.mcp_client
        )

        self.hotel_agent = ToolAwareAgent(
            name="酒店推荐专家",
            system_prompt="""你是专业的酒店顾问。根据用户的住宿偏好，推荐最合适的酒店。
你需要根据用户需求搜索合适的酒店信息。""",
            llm=self.llm,
            mcp_client=self.mcp_client
        )

        self.planner_agent = ToolAwareAgent(
            name="行程规划专家",
            system_prompt="""你是专业的旅行规划师。根据已收集的信息，生成完整的旅行计划。
你需要综合已有的景点、天气、酒店信息，生成合理的行程安排。
**重要：你不需要调用任何工具，因为信息已经提供给你了。**
最后必须按照指定的JSON格式输出旅行计划。""",
            llm=self.llm,
            mcp_client=None
        )

        print("✅ 旅行规划智能体系统初始化完成")

    def search_attractions(self, city: str, preferences: str) -> str:
        print(f"\n🔍 步骤1: 搜索{city}的景点...")
        query = f"请搜索{city}的{preferences}景点，返回景点名称、地址、评分和门票价格等信息。"
        result = self.attraction_agent.run(query)
        print(f"✅ 景点搜索完成")
        return result

    def query_weather(self, city: str) -> str:
        print(f"\n🌤️ 步骤2: 查询{city}的天气...")
        query = f"请查询{city}的天气预报，返回未来几天的天气情况。"
        result = self.weather_agent.run(query)
        print(f"✅ 天气查询完成")
        return result

    def search_hotels(self, city: str, accommodation: str) -> str:
        print(f"\n🏨 步骤3: 搜索{city}的酒店...")
        query = f"请搜索{city}的{accommodation}，返回酒店名称、地址、价格范围和评分等信息。"
        result = self.hotel_agent.run(query)
        print(f"✅ 酒店搜索完成")
        return result

    def generate_plan(
        self,
        request: TripPlanRequest,
        attraction_info: str,
        weather_info: str,
        hotel_info: str
    ) -> str:
        print(f"\n📋 步骤4: 生成旅行计划...")

        json_template = '''{
  "city": "CITY",
  "start_date": "START",
  "end_date": "END",
  "days": [
    {
      "date": "日期",
      "day_index": 0,
      "description": "描述",
      "transportation": "交通",
      "accommodation": "住宿",
      "hotel": {"name": "酒店", "address": "地址", "estimated_cost": 0},
      "attractions": [
        {"name": "景点", "address": "地址", "location": {"longitude": 0, "latitude": 0}, "visit_duration": 60, "description": "描述", "ticket_price": 0}
      ],
      "meals": [
        {"type": "类型", "name": "餐饮", "estimated_cost": 0}
      ]
    }
  ],
  "weather_info": [
    {"date": "日期", "day_weather": "天气", "night_weather": "夜间天气", "day_temp": 0, "night_temp": 0, "wind_direction": "风向", "wind_power": "风力"}
  ],
  "overall_suggestions": "建议",
  "budget": {"total_attractions": 0, "total_hotels": 0, "total_meals": 0, "total_transportation": 0, "total": 0}
}'''

        query = f"""请根据以下信息生成{request.city}的{request.days}天旅行计划：

用户需求：
- 目的地：{request.city}
- 日期：{request.start_date} 至 {request.end_date}
- 天数：{request.days}天
- 偏好：{request.preferences}
- 预算：{request.budget}
- 交通方式：{request.transportation}
- 住宿类型：{request.accommodation}

已收集的信息：
【景点信息】
{attraction_info}

【天气信息】
{weather_info}

【酒店信息】
{hotel_info}

请生成详细的旅行计划，包括每天的景点安排、餐饮推荐、住宿信息和预算明细。
最后必须严格按照以下JSON格式输出：
{json_template}
"""
        result = self.planner_agent.run(query, show_thinking=True)
        print(f"✅ 计划生成完成")
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
        """从响应中提取JSON"""
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
        """
        规划旅行的核心方法

        该方法是整个旅行规划系统的入口，协调多个Agent完成规划任务。

        Args:
            request: 用户提交的旅行请求，包含以下字段:
                - city: 目的地城市
                - days: 旅行天数
                - start_date: 出发日期
                - end_date: 返程日期
                - preferences: 旅行偏好
                - budget: 预算范围
                - transportation: 交通方式
                - accommodation: 住宿类型

        Returns:
            TripPlan: 结构化的旅行计划，包含:
                - 城市和日期信息
                - 每日行程详情(景点、餐饮、住宿)
                - 天气预报信息
                - 预算明细
                - 总体建议

        工作流程:
            1. 调用景点Agent搜索目的地景点
            2. 调用天气Agent查询天气预报
            3. 调用酒店Agent搜索住宿
            4. 综合信息生成最终行程
            5. 自动补充景点图片

        Note:
            如果在限定次数内无法获取有效的JSON响应，
            将返回一个空的行程列表并附带错误提示。
        """
        print(f"\n{'='*60}")
        print(f"🧳 开始规划: {request.city} {request.days}天行程")
        print(f"{'='*60}")

        attraction_info = self.search_attractions(request.city, request.preferences)
        weather_info = self.query_weather(request.city)
        hotel_info = self.search_hotels(request.city, request.accommodation)

        plan_response = self.generate_plan(
            request, attraction_info, weather_info, hotel_info
        )

        plan_data = self.parse_json_response(plan_response)
        if plan_data:
            return TripPlan(**plan_data)
        else:
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
