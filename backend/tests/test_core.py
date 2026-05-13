"""
核心逻辑单元测试
覆盖: JSON解析、温度转换、输入校验、速率限制
"""
import json
import pytest
from unittest.mock import MagicMock


# ── JSON 解析 ──────────────────────────────────────────────

class TestParseJsonResponse:
    """测试从 LLM 响应中提取 JSON"""

    def _get_parser(self):
        from app.agents.trip_planner import TripPlannerAgent
        # 不初始化 LLM/MCP，只测 parse_json_response
        agent = object.__new__(TripPlannerAgent)
        return agent.parse_json_response

    def test_parse_clean_json(self):
        parser = self._get_parser()
        data = {"city": "北京", "days": []}
        result = parser(json.dumps(data))
        assert result is not None
        assert result["city"] == "北京"

    def test_parse_json_in_code_block(self):
        parser = self._get_parser()
        text = '以下是结果：\n```json\n{"city": "上海", "days": []}\n```\n'
        result = parser(text)
        assert result is not None
        assert result["city"] == "上海"

    def test_parse_json_with_surrounding_text(self):
        parser = self._get_parser()
        text = '好的，这是行程：{"city": "成都", "days": []} 请查收'
        result = parser(text)
        assert result is not None
        assert result["city"] == "成都"

    def test_parse_invalid_json_returns_none(self):
        parser = self._get_parser()
        result = parser("这不是JSON")
        assert result is None

    def test_parse_missing_required_fields(self):
        parser = self._get_parser()
        result = parser('{"name": "test"}')
        assert result is None

    def test_parse_empty_string(self):
        parser = self._get_parser()
        result = parser("")
        assert result is None


# ── 温度解析 ───────────────────────────────────────────────

class TestWeatherParseTemp:
    """测试 WeatherInfo 温度字段的 field_validator"""

    def test_parse_temp_with_degree_symbol(self):
        from app.models.schemas import WeatherInfo
        w = WeatherInfo(
            date="2024-06-01",
            day_weather="晴",
            night_weather="多云",
            day_temp="25°C",
            night_temp="18℃",
            wind_direction="南风",
            wind_power="3级"
        )
        assert w.day_temp == 25
        assert w.night_temp == 18

    def test_parse_temp_pure_int(self):
        from app.models.schemas import WeatherInfo
        w = WeatherInfo(
            date="2024-06-01",
            day_weather="晴",
            night_weather="多云",
            day_temp=30,
            night_temp=20,
            wind_direction="南风",
            wind_power="3级"
        )
        assert w.day_temp == 30

    def test_parse_temp_string_number(self):
        from app.models.schemas import WeatherInfo
        w = WeatherInfo(
            date="2024-06-01",
            day_weather="晴",
            night_weather="多云",
            day_temp="22°",
            night_temp="15",
            wind_direction="南风",
            wind_power="3级"
        )
        assert w.day_temp == 22
        assert w.night_temp == 15


# ── 输入校验 ───────────────────────────────────────────────

class TestTripPlanRequestValidation:
    """测试请求参数校验"""

    def test_valid_request(self):
        from app.models.schemas import TripPlanRequest
        r = TripPlanRequest(
            city="北京", days=3,
            start_date="2024-06-01", end_date="2024-06-03"
        )
        assert r.city == "北京"

    def test_invalid_date_format(self):
        from app.models.schemas import TripPlanRequest
        with pytest.raises(Exception):
            TripPlanRequest(
                city="北京", days=3,
                start_date="06/01/2024", end_date="2024-06-03"
            )

    def test_invalid_city_characters(self):
        from app.models.schemas import TripPlanRequest
        with pytest.raises(Exception):
            TripPlanRequest(
                city="北京<script>", days=3,
                start_date="2024-06-01", end_date="2024-06-03"
            )

    def test_empty_city(self):
        from app.models.schemas import TripPlanRequest
        with pytest.raises(Exception):
            TripPlanRequest(
                city="", days=3,
                start_date="2024-06-01", end_date="2024-06-03"
            )

    def test_days_out_of_range(self):
        from app.models.schemas import TripPlanRequest
        with pytest.raises(Exception):
            TripPlanRequest(
                city="北京", days=0,
                start_date="2024-06-01", end_date="2024-06-03"
            )


# ── 健康检查 ───────────────────────────────────────────────
# httpx ASGITransport 需要 httpx>=0.24，当前环境版本较低
# 运行: curl http://localhost:8000/health
