"""
坐标提取与兜底逻辑单元测试
覆盖: 酒店文本正则提取、景点文本提取、空日期坐标兜底、(0,0)无效坐标清理
"""
import pytest

from app.agents.coordinates import (
    CoordinateManager,
    extract_hotels_from_text,
    extract_attractions_from_text,
)


def _get_manager():
    return CoordinateManager()


# ── 酒店文本正则提取 ──────────────────────────────────────────

class TestExtractHotelsFromText:
    def test_standard_format(self):
        text = '【希尔顿酒店】地址: 东城区 | 坐标: 116.407,39.904'
        hotels = extract_hotels_from_text(text)
        assert len(hotels) == 1
        assert hotels[0]["name"] == "希尔顿酒店"
        assert hotels[0]["location"]["longitude"] == 116.407
        assert hotels[0]["location"]["latitude"] == 39.904

    def test_chinese_colon(self):
        text = '【万豪酒店】地址：朝阳区 | 坐标：116.460,39.908'
        hotels = extract_hotels_from_text(text)
        assert len(hotels) == 1
        assert hotels[0]["location"]["longitude"] == 116.460

    def test_parenthesized_coords(self):
        text = '【香格里拉】地址: 海淀区 | (116.326, 39.947)'
        hotels = extract_hotels_from_text(text)
        assert len(hotels) == 1
        assert hotels[0]["location"]["longitude"] == 116.326

    def test_bare_coords(self):
        text = '【洲际酒店】评分: 4.5 | 120.15,30.28 附近'
        hotels = extract_hotels_from_text(text)
        assert len(hotels) == 1
        assert hotels[0]["location"]["longitude"] == 120.15

    def test_no_coords_still_returned(self):
        text = '【无坐标酒店】地址: 某路 | 评分: 4.3'
        hotels = extract_hotels_from_text(text)
        assert len(hotels) == 1
        assert hotels[0]["location"] is None

    def test_empty_text(self):
        assert extract_hotels_from_text("") == []
        assert extract_hotels_from_text(None) == []

    def test_multiple_hotels(self):
        text = (
            '【A酒店】坐标: 116.4,39.9\n'
            '【B酒店】坐标: 121.47,31.23\n'
            '【C酒店】地址: 某路'
        )
        hotels = extract_hotels_from_text(text)
        assert len(hotels) == 3
        assert hotels[0]["location"] is not None
        assert hotels[1]["location"] is not None
        assert hotels[2]["location"] is None

    def test_out_of_range_coords_ignored(self):
        text = '【测试酒店】坐标: 5.0,3.0'
        hotels = extract_hotels_from_text(text)
        assert len(hotels) == 1
        assert hotels[0]["location"] is None

    def test_price_extraction(self):
        text = '【商务酒店】参考价: 500元/晚 | 坐标: 116.4,39.9'
        hotels = extract_hotels_from_text(text)
        assert hotels[0]["price"] == 500

    def test_avg_price_format(self):
        text = '【精品酒店】均价: 380元 | 坐标: 116.4,39.9'
        hotels = extract_hotels_from_text(text)
        assert hotels[0]["price"] == 380


# ── 景点文本正则提取 ──────────────────────────────────────────

class TestExtractAttractionsFromText:
    def test_standard_format(self):
        text = '【故宫博物院】地址: 东城区 | 坐标: 116.397,39.918'
        result = extract_attractions_from_text(text)
        assert len(result) >= 1
        assert result[0]["name"] == "故宫博物院"
        assert result[0]["location"]["longitude"] == 116.397

    def test_multiple_attractions(self):
        text = (
            '【天安门】坐标: 116.397,39.908\n'
            '【长城】坐标: 116.024,40.362\n'
            '【颐和园】坐标: 116.275,39.999'
        )
        result = extract_attractions_from_text(text)
        assert len(result) == 3

    def test_no_coords_still_returned(self):
        text = '【无坐标景点】地址: 某处 | 评分: 4.5'
        result = extract_attractions_from_text(text)
        assert len(result) == 1
        assert "location" not in result[0]

    def test_empty_text(self):
        assert extract_attractions_from_text("") == []
        assert extract_attractions_from_text(None) == []


# ── 空日期坐标兜底 ──────────────────────────────────────────

class TestEnrichEmptyDays:
    def setup_method(self):
        self.mgr = _get_manager()

    def test_hotel_gets_city_center_coords(self):
        plan_data = {
            "city": "北京",
            "start_date": "2024-06-01",
            "days": [{
                "hotel": {"name": "测试酒店", "address": "某路"},
                "meals": [],
                "attractions": [],
            }],
        }
        self.mgr.enrich_empty_days(plan_data, "", "")
        hotel_loc = plan_data["days"][0]["hotel"]["location"]
        assert hotel_loc is not None
        assert 116.0 < hotel_loc["longitude"] < 117.0
        assert 39.0 < hotel_loc["latitude"] < 40.5

    def test_meal_gets_offset_coords(self):
        plan_data = {
            "city": "上海",
            "start_date": "2024-06-01",
            "days": [{
                "meals": [{"type": "lunch", "name": "午餐"}],
                "attractions": [{"name": "外滩", "location": {"longitude": 121.49, "latitude": 31.24}}],
            }],
        }
        self.mgr.enrich_empty_days(plan_data, "", "")
        meal_loc = plan_data["days"][0]["meals"][0]["location"]
        assert meal_loc is not None
        assert 121.0 < meal_loc["longitude"] < 122.0

    def test_prev_day_attractions_used_as_ref(self):
        plan_data = {
            "city": "成都",
            "start_date": "2024-06-01",
            "days": [
                {"attractions": [{"name": "宽窄巷子", "location": {"longitude": 104.056, "latitude": 30.669}}], "meals": []},
                {"hotel": {"name": "酒店"}, "meals": [{"type": "lunch"}], "attractions": []},
            ],
        }
        self.mgr.enrich_empty_days(plan_data, "", "")
        hotel_loc = plan_data["days"][1]["hotel"]["location"]
        assert hotel_loc is not None
        assert 104.0 < hotel_loc["longitude"] < 104.2

    def test_extracted_hotels_matched_by_name(self):
        hotel_info = '【皇冠酒店】地址: 某路 | 坐标: 116.41,39.91'
        plan_data = {
            "city": "北京",
            "start_date": "2024-06-01",
            "days": [{
                "hotel": {"name": "皇冠酒店"},
                "meals": [],
                "attractions": [],
            }],
        }
        self.mgr.enrich_empty_days(plan_data, "", hotel_info)
        hotel_loc = plan_data["days"][0]["hotel"]["location"]
        assert hotel_loc["longitude"] == 116.41


# ── 无效坐标清理 ──────────────────────────────────────────

class TestValidateAndFixPlan:
    def setup_method(self):
        self.mgr = _get_manager()

    def _make_request(self):
        from app.models.schemas import TripPlanRequest
        return TripPlanRequest(
            city="北京", days=1,
            start_date="2024-06-01", end_date="2024-06-01"
        )

    def test_zero_zero_coord_set_to_none(self):
        plan_data = {
            "city": "北京",
            "days": [{
                "attractions": [{"name": "景点", "location": {"longitude": 0, "latitude": 0}}],
                "hotel": {"name": "酒店", "location": {"longitude": 0, "latitude": 0}},
                "meals": [],
            }],
        }
        self.mgr.validate_and_fix_plan(plan_data, self._make_request())
        attr_loc = plan_data["days"][0]["attractions"][0]["location"]
        assert attr_loc is None

    def test_valid_coords_preserved(self):
        plan_data = {
            "city": "北京",
            "days": [{
                "attractions": [{"name": "景点", "location": {"longitude": 116.4, "latitude": 39.9}}],
                "hotel": {"name": "酒店", "location": {"longitude": 116.4, "latitude": 39.9}},
                "meals": [],
            }],
        }
        self.mgr.validate_and_fix_plan(plan_data, self._make_request())
        attr_loc = plan_data["days"][0]["attractions"][0]["location"]
        assert attr_loc["longitude"] == 116.4

    def test_invalid_visit_duration_fixed(self):
        plan_data = {
            "city": "北京",
            "days": [{
                "attractions": [{"name": "景点", "visit_duration": -30}],
                "hotel": {},
                "meals": [],
            }],
        }
        self.mgr.validate_and_fix_plan(plan_data, self._make_request())
        dur = plan_data["days"][0]["attractions"][0]["visit_duration"]
        assert dur >= 30

    def test_hotel_estimated_cost_fixed_when_invalid(self):
        plan_data = {
            "city": "北京",
            "days": [{
                "attractions": [],
                "hotel": {"name": "酒店", "estimated_cost": 0},
                "meals": [],
            }],
        }
        self.mgr.validate_and_fix_plan(plan_data, self._make_request())
        assert plan_data["days"][0]["hotel"]["estimated_cost"] == 300

    def test_hotel_estimated_cost_fixed_when_none(self):
        plan_data = {
            "city": "北京",
            "days": [{
                "attractions": [],
                "hotel": {"name": "酒店", "estimated_cost": "abc"},
                "meals": [],
            }],
        }
        self.mgr.validate_and_fix_plan(plan_data, self._make_request())
        assert plan_data["days"][0]["hotel"]["estimated_cost"] == 300

    def test_hotel_estimated_cost_preserved_when_valid(self):
        plan_data = {
            "city": "北京",
            "days": [{
                "attractions": [],
                "hotel": {"name": "酒店", "estimated_cost": 500},
                "meals": [],
            }],
        }
        self.mgr.validate_and_fix_plan(plan_data, self._make_request())
        assert plan_data["days"][0]["hotel"]["estimated_cost"] == 500


# ── 日期递增 ──────────────────────────────────────────

class TestEnrichEmptyDaysDateIncrement:
    def setup_method(self):
        self.mgr = _get_manager()

    def test_dates_increment_across_days(self):
        plan_data = {
            "city": "北京",
            "start_date": "2024-06-01",
            "days": [
                {"hotel": {"name": "A"}, "meals": [], "attractions": []},
                {"hotel": {"name": "B"}, "meals": [], "attractions": []},
                {"hotel": {"name": "C"}, "meals": [], "attractions": []},
            ],
        }
        self.mgr.enrich_empty_days(plan_data, "", "")
        assert plan_data["days"][0]["date"] == "2024-06-01"
        assert plan_data["days"][1]["date"] == "2024-06-02"
        assert plan_data["days"][2]["date"] == "2024-06-03"

    def test_existing_date_preserved(self):
        plan_data = {
            "city": "北京",
            "start_date": "2024-06-01",
            "days": [
                {"date": "2024-07-15", "hotel": {"name": "A"}, "meals": [], "attractions": []},
            ],
        }
        self.mgr.enrich_empty_days(plan_data, "", "")
        assert plan_data["days"][0]["date"] == "2024-07-15"


# ── 景点提取格式 ──────────────────────────────────────────

class TestExtractAttractionsFormats:
    def test_star_format(self):
        text = '* 故宫: 地址东城区 | 坐标: 116.397,39.918'
        result = extract_attractions_from_text(text)
        assert len(result) >= 1
        assert result[0]["name"] == "故宫"

    def test_number_format(self):
        text = '1. 天安门: 坐标: 116.397,39.908'
        result = extract_attractions_from_text(text)
        assert len(result) >= 1
