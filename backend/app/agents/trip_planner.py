import json
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict
from app.services.llm import HelloAgentsLLM
from app.services.mcp_client import MCPClient
from app.models.schemas import TripPlanRequest, TripPlan, Budget
from app.agents.prompts import (
    ATTRACTION_AGENT_PROMPT,
    WEATHER_AGENT_PROMPT,
    HOTEL_AGENT_PROMPT,
    PLANNER_AGENT_PROMPT_TEMPLATE,
    VARIANT_STYLES,
)
from app.agents.coordinates import get_city_tier, CoordinateManager
from app.agents.base import ToolAwareAgent
from app.agents.transport import get_real_transport, estimate_transport

logger = logging.getLogger(__name__)


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
    # 城市信息缓存（避免重复LLM调用）
    _info_cache: Dict[str, tuple] = {}
    _CACHE_TTL = 600  # 10分钟缓存

    def __init__(self):
        logger.info("初始化旅行规划智能体系统...")
        self.llm = HelloAgentsLLM()
        self.mcp_client = MCPClient()
        self.coord_manager = CoordinateManager(mcp_client=self.mcp_client)

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

    # Function calling schema for structured trip plan output
    TRIP_PLAN_TOOL = {
        "type": "function",
        "function": {
            "name": "generate_trip_plan",
            "description": "生成结构化的旅行计划，包含每日行程、景点、餐饮、住宿和预算",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "目的地城市"},
                    "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD"},
                    "days": {
                        "type": "array",
                        "description": "每日行程安排",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string", "description": "日期 YYYY-MM-DD"},
                                "day_index": {"type": "integer", "description": "第几天从0开始"},
                                "description": {"type": "string", "description": "当日主题概述"},
                                "transportation": {"type": "string", "description": "交通方式"},
                                "accommodation": {"type": "string", "description": "住宿安排"},
                                "hotel": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "address": {"type": "string"},
                                        "location": {
                                            "type": "object",
                                            "properties": {
                                                "longitude": {"type": "number", "description": "经度"},
                                                "latitude": {"type": "number", "description": "纬度"}
                                            },
                                            "required": ["longitude", "latitude"],
                                            "description": "酒店的经纬度坐标"
                                        },
                                        "price_range": {"type": "string"},
                                        "rating": {"type": "number"},
                                        "estimated_cost": {"type": "integer"}
                                    },
                                    "required": ["name", "address", "location", "price_range", "estimated_cost"]
                                },
                                "attractions": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "address": {"type": "string"},
                                            "location": {
                                                "type": "object",
                                                "properties": {
                                                    "longitude": {"type": "number"},
                                                    "latitude": {"type": "number"}
                                                },
                                                "required": ["longitude", "latitude"]
                                            },
                                            "visit_duration": {"type": "integer", "description": "游览时间(分钟)"},
                                            "description": {"type": "string", "description": "景点深度介绍100-150字"},
                                            "category": {"type": "string"},
                                            "rating": {"type": "number"},
                                            "ticket_price": {"type": "integer"}
                                        },
                                        "required": ["name", "address", "location", "visit_duration", "description", "ticket_price"]
                                    }
                                },
                                "meals": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "type": {"type": "string", "enum": ["breakfast", "lunch", "dinner", "snack"]},
                                            "name": {"type": "string"},
                                            "address": {"type": "string"},
                                            "location": {
                                                "type": "object",
                                                "properties": {
                                                    "longitude": {"type": "number", "description": "经度"},
                                                    "latitude": {"type": "number", "description": "纬度"}
                                                },
                                                "required": ["longitude", "latitude"],
                                                "description": "餐厅的经纬度坐标"
                                            },
                                            "description": {"type": "string"},
                                            "estimated_cost": {"type": "integer"}
                                        },
                                        "required": ["type", "name", "address", "location", "estimated_cost"]
                                    }
                                }
                            },
                            "required": ["date", "day_index", "description", "transportation", "accommodation", "attractions", "meals"]
                        }
                    },
                    "weather_info": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string"},
                                "day_weather": {"type": "string"},
                                "night_weather": {"type": "string"},
                                "day_temp": {"type": "integer"},
                                "night_temp": {"type": "integer"},
                                "wind_direction": {"type": "string"},
                                "wind_power": {"type": "string"}
                            }
                        }
                    },
                    "overall_suggestions": {"type": "string", "description": "5-8条实用旅行建议，每条一行"},
                    "budget": {
                        "type": "object",
                        "properties": {
                            "total_attractions": {"type": "integer"},
                            "total_hotels": {"type": "integer"},
                            "total_meals": {"type": "integer"},
                            "total_transportation": {"type": "integer"},
                            "total": {"type": "integer"}
                        }
                    }
                },
                "required": ["city", "start_date", "end_date", "days", "weather_info", "overall_suggestions", "budget"]
            }
        }
    }

    def generate_plan(
        self,
        request: TripPlanRequest,
        attraction_info: str,
        weather_info: str,
        hotel_info: str,
        variant_key: str = "classic",
    ) -> Optional[dict]:
        """Generate trip plan using function calling for structured output, with regex fallback."""
        style = VARIANT_STYLES.get(variant_key, VARIANT_STYLES["classic"])
        logger.info(f"生成旅行计划（{style['name']}风格）...")

        # 交通信息
        dep_city = getattr(request, 'departure_city', '') or ''
        if dep_city and dep_city != request.city:
            transport = estimate_transport(dep_city, request.city)
            dep_display = f"{dep_city}→{request.city}"
            mode_display = transport.recommended_mode
            cost_display = str(transport.estimated_cost)
            dur_display = transport.estimated_duration
        else:
            dep_display = dep_city or "未填写"
            mode_display = "未知"
            cost_display = "0"
            dur_display = "未知"

        tier_info = get_city_tier(request.city)

        query = PLANNER_AGENT_PROMPT_TEMPLATE.format(
            city=request.city,
            departure_city=dep_display,
            recommended_mode=mode_display,
            transport_cost=cost_display,
            transport_duration=dur_display,
            meal_range=tier_info["meal"],
            hotel_range=tier_info["hotel"],
            price_multiplier=tier_info["multiplier"],
            start_date=request.start_date,
            end_date=request.end_date,
            days=request.days,
            travelers=request.travelers,
            preferences=request.preferences_text,
            budget=request.budget,
            transportation=request.transportation,
            accommodation=request.accommodation,
            attraction_info=attraction_info,
            weather_info=weather_info,
            hotel_info=hotel_info,
            style_name=style["name"],
            style_instruction=style["instruction"],
        )

        messages = [
            {"role": "system", "content": "你是经验丰富的旅行规划师。根据已收集的信息，调用 generate_trip_plan 生成结构化的旅行计划。所有数据必须来自提供的景点/天气/酒店信息，不要编造。"},
            {"role": "user", "content": query}
        ]

        # Try function calling first, with one retry on validation failure
        for attempt in range(2):
            result = self.llm.think_structured(
                messages=messages,
                tools=[self.TRIP_PLAN_TOOL],
                temperature=0
            )

            if result and "city" in result and "days" in result:
                logger.info("Function calling 输出成功")
                # Mimo 可能将 list 字段序列化为 JSON 字符串，需手动还原
                for key in ("days", "weather_info"):
                    val = result.get(key)
                    if isinstance(val, str):
                        parsed = self._safe_json_list(val)
                        if parsed is not None:
                            result[key] = parsed
                            logger.info(f"  {key}: str→list, len={len(parsed)}")
                        else:
                            logger.warning(f"  {key} JSON解析彻底失败，置空")
                            result[key] = []
                    elif isinstance(val, list):
                        logger.info(f"  {key}: list, len={len(val)}")
                    else:
                        result[key] = []

                # 安全截断：确保 days/weather_info 不超过请求数量
                requested_days = request.days
                if isinstance(result.get("days"), list) and len(result["days"]) > requested_days:
                    logger.info(f"  days 截断: {len(result['days'])} → {requested_days}")
                    result["days"] = result["days"][:requested_days]
                if isinstance(result.get("weather_info"), list) and len(result["weather_info"]) > requested_days:
                    result["weather_info"] = result["weather_info"][:requested_days]

                # Schema validation
                if self._validate_plan(result, request):
                    return result
                elif attempt == 0:
                    logger.warning("Schema 验证失败，重试一次...")
                    continue
                else:
                    logger.warning("Schema 验证仍失败，使用结果（后续有宽松解析兜底）")
                    return result

        # Fallback: use ToolAwareAgent with regex parsing
        logger.info("Function calling 未成功，回退到文本解析...")
        text_result = self.planner_agent.run(query, show_thinking=True)
        return self.parse_json_response(text_result)

    @staticmethod
    def _validate_plan(plan: dict, request: TripPlanRequest) -> bool:
        """Validate that a plan dict has minimum required fields."""
        days = plan.get("days")
        if not isinstance(days, list) or len(days) == 0:
            logger.warning("验证失败: days 缺失或为空")
            return False
        if len(days) < request.days:
            logger.warning(f"验证警告: days 数量不足 {len(days)}/{request.days}")
            # Accept but log — can't reject on this
        for i, day in enumerate(days):
            if not isinstance(day, dict):
                logger.warning(f"验证失败: days[{i}] 不是 dict")
                return False
            if not day.get("attractions") or not isinstance(day["attractions"], list):
                logger.warning(f"验证失败: days[{i}].attractions 缺失或非 list")
                return False
            if not day.get("meals") or not isinstance(day["meals"], list):
                logger.warning(f"验证失败: days[{i}].meals 缺失或非 list")
                return False
        if not plan.get("budget") or not isinstance(plan["budget"], dict):
            logger.warning("验证失败: budget 缺失")
            return False
        return True

    @staticmethod
    def _safe_json_list(val: str) -> Optional[list]:
        """尝试解析 JSON 字符串为 list，支持多种常见损坏格式修复。"""
        # 直接解析
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) else None
        except (json.JSONDecodeError, TypeError):
            pass

        # 提取 [...] 部分
        bracket_match = re.search(r'\[[\s\S]*\]', val)
        if bracket_match:
            raw = bracket_match.group(0)
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass

            # 修复常见问题：尾部逗号、缺少引号
            fixed = re.sub(r',\s*]', ']', raw)
            fixed = re.sub(r',\s*}', '}', fixed)
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass

            # 逐个提取 {...} 对象
            objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', raw)
            result = []
            for obj_str in objects:
                try:
                    result.append(json.loads(obj_str))
                except json.JSONDecodeError:
                    continue
            if result:
                return result

        return None

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

    def _fetch_info_directly(self, city: str, preferences: str, accommodation: str, budget: str):
        """直接调用 MCP 工具获取信息，MCP 不可用时用精简LLM生成。"""
        if not self.mcp_client or not self.mcp_client.amap_tool or not self.mcp_client.amap_tool.ready:
            logger.info("MCP 不可用，使用精简LLM获取景点信息")
            return self._fetch_info_via_llm(city, preferences, accommodation, budget)

        attraction_info = ""
        weather_info = ""
        hotel_info = ""

        with ThreadPoolExecutor(max_workers=3) as executor:
            def fetch_attractions():
                logger.info(f"直接搜索{city}景点...")
                return self.mcp_client.search_poi(preferences, city)

            def fetch_weather():
                logger.info(f"直接查询{city}天气...")
                return self.mcp_client.get_weather(city)

            def fetch_hotels():
                logger.info(f"直接搜索{city}酒店...")
                keywords = f"{accommodation} {budget}" if budget else accommodation
                return self.mcp_client.search_poi(keywords, city)

            futures = {
                executor.submit(fetch_attractions): "attractions",
                executor.submit(fetch_weather): "weather",
                executor.submit(fetch_hotels): "hotels",
            }
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    result = future.result(timeout=30)
                    if task_name == "attractions":
                        attraction_info = result
                    elif task_name == "weather":
                        weather_info = result
                    elif task_name == "hotels":
                        hotel_info = result
                    logger.info(f"{task_name} 数据获取完成")
                except Exception as e:
                    logger.error(f"{task_name} 数据获取失败: {e}")

        # MCP 返回空结果时，回退到 LLM 获取对应信息
        if not attraction_info.strip():
            logger.warning("景点信息为空，回退到LLM获取")
            attraction_info = self._fetch_attractions_via_llm(city, preferences)
        if not hotel_info.strip():
            logger.warning("酒店信息为空，回退到LLM获取")
            hotel_info = self._fetch_hotels_via_llm(city, accommodation, budget)

        return attraction_info, weather_info, hotel_info

    def _fetch_attractions_via_llm(self, city: str, preferences: str) -> str:
        """LLM 生成景点列表。"""
        prompt = f"列出{city}最值得去的6个{preferences}景点，格式：序号. 景点名：地址：一句话简介：评分"
        messages = [
            {"role": "system", "content": "你是旅行助手。直接输出景点列表，不要其他内容。"},
            {"role": "user", "content": prompt}
        ]
        return self.llm.think(messages, temperature=0.3) or ""

    def _fetch_hotels_via_llm(self, city: str, accommodation: str, budget: str) -> str:
        """LLM 生成酒店推荐列表。"""
        prompt = f"推荐{city}3家{accommodation}，预算档位：{budget}，格式：序号. 酒店名：地址：价格范围：评分：亮点"
        messages = [
            {"role": "system", "content": "你是酒店推荐专家。直接输出酒店推荐列表，不要其他内容。"},
            {"role": "user", "content": prompt}
        ]
        return self.llm.think(messages, temperature=0.3) or ""

    def _fetch_info_via_llm(self, city: str, preferences: str, accommodation: str, budget: str):
        """MCP 不可用时，用精简LLM生成景点列表，天气用REST API。"""
        import time as _time

        # 检查缓存
        cache_key = f"{city}|{preferences}|{accommodation}"
        if cache_key in self._info_cache:
            cached_at, cached_result = self._info_cache[cache_key]
            if _time.time() - cached_at < self._CACHE_TTL:
                logger.info(f"使用缓存: {city}")
                return cached_result

        # 天气用REST API直接获取
        from app.services.weather import get_weather_str
        weather_info = get_weather_str(city)

        attraction_info = self._fetch_attractions_via_llm(city, preferences)
        hotel_info = self._fetch_hotels_via_llm(city, accommodation, budget)

        # 缓存结果
        self._info_cache[cache_key] = (_time.time(), (attraction_info, weather_info, hotel_info))

        return attraction_info, weather_info, hotel_info


    def plan_trip(self, request: TripPlanRequest, variant_key: str = "classic") -> TripPlan:
        logger.info(f"开始规划: {request.city} {request.days}天行程")

        # 直接调 MCP 工具获取数据（快速路径，无 LLM 开销）
        attraction_info, weather_info, hotel_info = self._fetch_info_directly(
            request.city, request.preferences_text, request.accommodation, request.budget
        )

        # 生成旅行计划
        logger.info("生成旅行计划...")
        plan_data = self.generate_plan(request, attraction_info, weather_info, hotel_info, variant_key)

        if plan_data:
            logger.info("旅行计划生成成功")
            # 确保 days 和 weather_info 是列表（Mimo 可能返回 JSON 字符串）
            for key in ("days", "weather_info"):
                val = plan_data.get(key)
                if isinstance(val, str):
                    try:
                        plan_data[key] = json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        plan_data[key] = []
                elif not isinstance(val, list):
                    plan_data[key] = []

            days_val = plan_data.get("days", [])
            logger.info(f"  解析后 days: type={type(days_val).__name__}, len={len(days_val) if isinstance(days_val, list) else 'N/A'}")
            if isinstance(days_val, list) and len(days_val) > 0:
                logger.info(f"  first day keys: {list(days_val[0].keys()) if isinstance(days_val[0], dict) else type(days_val[0])}")

            # 安全截断：确保不超过请求数量
            if isinstance(days_val, list) and len(days_val) > request.days:
                logger.info(f"  plan_trip 安全截断 days: {len(days_val)} → {request.days}")
                plan_data["days"] = days_val[:request.days]
            weather_val = plan_data.get("weather_info", [])
            if isinstance(weather_val, list) and len(weather_val) > request.days:
                plan_data["weather_info"] = weather_val[:request.days]

            # 将天气日期映射到实际旅行日期
            from datetime import datetime, timedelta
            try:
                start = datetime.strptime(request.start_date, "%Y-%m-%d")
                for i, w in enumerate(plan_data.get("weather_info", [])):
                    if isinstance(w, dict):
                        w["date"] = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            except Exception:
                pass

            # 补全缺失的 attractions/meals
            self.coord_manager.enrich_empty_days(plan_data, attraction_info, hotel_info, request.budget)

            # 数据质量验证与修复：先清除无效坐标，再做地理编码
            self.coord_manager.validate_and_fix_plan(plan_data, request, variant_key)

            # 地理编码兜底：补充缺失坐标的景点/酒店/餐厅
            self.coord_manager.geocode_missing_coords(plan_data, request.city)

            # 城际交通：实时查询火车/航班
            if request.departure_city and request.departure_city != request.city:
                try:
                    transport = get_real_transport(
                        request.departure_city, request.city, request.start_date
                    )
                    plan_data["transport_info"] = transport.model_dump()
                    plan_data["departure_city"] = request.departure_city
                except Exception as e:
                    logger.warning(f"交通查询失败，使用估算: {e}")
                    transport = estimate_transport(request.departure_city, request.city)
                    plan_data["transport_info"] = transport.model_dump()
                    plan_data["departure_city"] = request.departure_city

            try:
                return TripPlan(**plan_data)
            except Exception as e:
                logger.error(f"TripPlan 验证失败: {e}，尝试宽松解析")
                return self._build_plan_fallback(plan_data, request)
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

    def _build_plan_fallback(self, plan_data: dict, request: TripPlanRequest) -> TripPlan:
        """宽松模式构建 TripPlan，跳过验证失败的字段。"""
        try:
            # 提取基本字段
            city = plan_data.get("city", request.city)
            start_date = plan_data.get("start_date", request.start_date)
            end_date = plan_data.get("end_date", request.end_date)
            suggestions = plan_data.get("overall_suggestions", "")

            # 逐个构建 DayPlan
            days_raw = plan_data.get("days", [])
            if isinstance(days_raw, str):
                days_raw = json.loads(days_raw) if days_raw.strip().startswith("[") else []

            from app.models.schemas import DayPlan, WeatherInfo, Budget
            valid_days = []
            for d in days_raw:
                if isinstance(d, str):
                    try:
                        d = json.loads(d)
                    except:
                        continue
                try:
                    # 清理每个字段
                    cleaned = {
                        "date": str(d.get("date", "")),
                        "day_index": int(d.get("day_index", 0)),
                        "description": str(d.get("description", "")),
                        "transportation": str(d.get("transportation", "")),
                        "accommodation": str(d.get("accommodation", "")),
                        "hotel": d.get("hotel"),
                        "attractions": d.get("attractions", []),
                        "meals": d.get("meals", []),
                    }
                    valid_days.append(DayPlan(**cleaned))
                except Exception as ex:
                    logger.warning(f"跳过无效 DayPlan: {ex}")

            # 安全截断
            if len(valid_days) > request.days:
                valid_days = valid_days[:request.days]

            # 构建天气信息
            weather_raw = plan_data.get("weather_info", [])
            if isinstance(weather_raw, str):
                weather_raw = json.loads(weather_raw) if weather_raw.strip().startswith("[") else []
            valid_weather = []
            for w in weather_raw:
                try:
                    valid_weather.append(WeatherInfo(**{
                        "date": str(w.get("date", "")),
                        "day_weather": str(w.get("day_weather", "")),
                        "night_weather": str(w.get("night_weather", "")),
                        "day_temp": int(float(str(w.get("day_temp", 0)).replace("°C", "").replace("℃", ""))),
                        "night_temp": int(float(str(w.get("night_temp", 0)).replace("°C", "").replace("℃", ""))),
                        "wind_direction": str(w.get("wind_direction", "")),
                        "wind_power": str(w.get("wind_power", "")),
                    }))
                except Exception:
                    pass

            # 安全截断天气列表
            if len(valid_weather) > request.days:
                valid_weather = valid_weather[:request.days]

            # 将天气日期映射到实际旅行日期
            from datetime import datetime, timedelta
            try:
                start = datetime.strptime(request.start_date, "%Y-%m-%d")
                for i, w in enumerate(valid_weather):
                    w.date = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            except Exception:
                pass

            # 构建预算
            budget_raw = plan_data.get("budget")
            budget = None
            if budget_raw and isinstance(budget_raw, dict):
                try:
                    budget = Budget(**budget_raw)
                except Exception:
                    pass

            return TripPlan(
                city=city,
                start_date=start_date,
                end_date=end_date,
                days=valid_days,
                weather_info=valid_weather,
                overall_suggestions=suggestions,
                budget=budget,
            )
        except Exception as e:
            logger.error(f"宽松解析也失败: {e}")
            return TripPlan(
                city=request.city,
                start_date=request.start_date,
                end_date=request.end_date,
                days=[],
                weather_info=[],
                overall_suggestions="抱歉，生成过程中出现错误，请稍后重试。"
            )


    def update_budget(self, trip_plan: TripPlan, transportation: str = "公共交通", intercity_transport_cost: int = 0) -> TripPlan:
        """
        更新行程预算
        """
        # 交通费用按方式区分（元/天）
        transport_cost_map = {
            "公共交通": 30,
            "出租车/网约车": 120,
            "租车自驾": 200,
            "步行": 0,
        }
        daily_transport = transport_cost_map.get(transportation, 50)

        total_attractions = 0
        total_hotels = 0
        total_meals = 0

        for day in trip_plan.days:
            for attraction in day.attractions:
                total_attractions += attraction.ticket_price or 0
            if day.hotel:
                total_hotels += day.hotel.estimated_cost or 0
            for meal in day.meals:
                total_meals += meal.estimated_cost or 0

        # 城际交通费用优先使用 transport_info 中的数据
        if not intercity_transport_cost and trip_plan.transport_info:
            intercity_transport_cost = trip_plan.transport_info.estimated_cost

        total_transportation = len(trip_plan.days) * daily_transport + intercity_transport_cost
        total = total_attractions + total_hotels + total_meals + total_transportation

        trip_plan.budget = Budget(
            total_attractions=total_attractions,
            total_hotels=total_hotels,
            total_meals=total_meals,
            total_transportation=total_transportation,
            total=total
        )

        return trip_plan
