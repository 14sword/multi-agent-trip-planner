"""
路线优化单元测试
覆盖: 最近邻排序、三方案变体、Day1起点、午餐插入
"""
import pytest

from app.agents.coordinates import CoordinateManager


def _make_attraction(name, lng, lat, category="景点"):
    return {
        "name": name,
        "address": f"{name}地址",
        "location": {"longitude": lng, "latitude": lat},
        "visit_duration": 60,
        "description": f"{name}的描述",
        "ticket_price": 0,
        "category": category,
    }


class TestOptimizeDailyRoute:
    """测试景点路线优化算法"""

    def setup_method(self):
        self.mgr = CoordinateManager()

    def test_classic_nearest_neighbor(self):
        """经典模式：严格最近邻排序"""
        day = {
            "attractions": [
                _make_attraction("颐和园", 116.275, 39.999),
                _make_attraction("天安门", 116.397, 39.909),
                _make_attraction("故宫", 116.397, 39.917),
            ]
        }
        self.mgr.optimize_daily_route(day, (116.397, 39.909), "classic")
        names = [a["name"] for a in day["attractions"]]
        assert names[0] == "天安门"
        assert names[1] == "故宫"
        assert names[2] == "颐和园"

    def test_day1_starts_from_arrival(self):
        """Day1从到达坐标出发，排序应从最近景点开始"""
        day = {
            "attractions": [
                _make_attraction("颐和园", 116.275, 39.999),
                _make_attraction("天安门", 116.397, 39.909),
                _make_attraction("故宫", 116.397, 39.917),
            ]
        }
        self.mgr.optimize_daily_route(day, (116.411, 39.510), "classic")
        names = [a["name"] for a in day["attractions"]]
        assert names[0] == "天安门"

    def test_two_attractions_no_change(self):
        """只有1个景点时不重排"""
        day = {"attractions": [_make_attraction("故宫", 116.397, 39.917)]}
        original = day["attractions"][:]
        self.mgr.optimize_daily_route(day, (116.397, 39.909), "classic")
        assert day["attractions"] == original

    def test_no_coords_not_reordered(self):
        """无坐标的景点排在末尾"""
        day = {
            "attractions": [
                _make_attraction("远郊景点", 116.1, 40.5),
                {"name": "未知景点", "address": "某地", "visit_duration": 60,
                 "description": "无坐标", "ticket_price": 0},
                _make_attraction("近处景点", 116.39, 39.91),
            ]
        }
        self.mgr.optimize_daily_route(day, (116.397, 39.909), "classic")
        names = [a["name"] for a in day["attractions"]]
        assert names[-1] == "未知景点"
        assert names[0] == "近处景点"
        assert names[1] == "远郊景点"

    def test_relaxed_minimal_reorder(self):
        """轻松休闲模式：只在大幅减少距离时才重排"""
        day = {
            "attractions": [
                _make_attraction("A", 116.39, 39.91),
                _make_attraction("B", 116.40, 39.92),
                _make_attraction("C", 116.28, 40.00),
            ]
        }
        original_names = [a["name"] for a in day["attractions"]]
        self.mgr.optimize_daily_route(day, (116.397, 39.909), "relaxed")
        result_names = [a["name"] for a in day["attractions"]]
        assert result_names == original_names

    def test_relaxed_preserves_good_order(self):
        """轻松休闲模式：好的顺序保持不变"""
        day = {
            "attractions": [
                _make_attraction("A", 116.39, 39.91),
                _make_attraction("B", 116.40, 39.92),
                _make_attraction("C", 116.41, 39.93),
            ]
        }
        original_names = [a["name"] for a in day["attractions"]]
        self.mgr.optimize_daily_route(day, (116.397, 39.909), "relaxed")
        result_names = [a["name"] for a in day["attractions"]]
        assert result_names == original_names

    def test_deep_grouped_by_category(self):
        """深度探索模式：同类别景点分组"""
        day = {
            "attractions": [
                _make_attraction("故宫", 116.397, 39.917, "历史文化"),
                _make_attraction("798", 116.494, 39.984, "创意园区"),
                _make_attraction("天坛", 116.411, 39.882, "历史文化"),
                _make_attraction("南锣鼓巷", 116.403, 39.937, "创意园区"),
            ]
        }
        self.mgr.optimize_daily_route(day, (116.397, 39.909), "deep")
        categories = [a["category"] for a in day["attractions"]]
        for cat in ["历史文化", "创意园区"]:
            indices = [i for i, c in enumerate(categories) if c == cat]
            if len(indices) > 1:
                assert max(indices) - min(indices) == len(indices) - 1, f"{cat}类景点应连续"


class TestValidateAndFixPlan:
    """测试 validate_and_fix_plan 路线优化集成"""

    def setup_method(self):
        self.mgr = CoordinateManager()

    def test_day1_uses_arrival_coords(self):
        """Day1使用arrival坐标作为起点"""
        plan_data = {
            "transport_info": {
                "arrival_longitude": 116.597,
                "arrival_latitude": 40.080,
            },
            "days": [
                {
                    "attractions": [
                        _make_attraction("颐和园", 116.275, 39.999),
                        _make_attraction("天安门", 116.397, 39.909),
                    ],
                    "hotel": {"location": {"longitude": 116.397, "latitude": 39.91}},
                }
            ],
        }
        request = type("Req", (), {
            "days": 1, "departure_city": "上海", "city": "北京"
        })()
        self.mgr.validate_and_fix_plan(plan_data, request, "classic")
        names = [a["name"] for a in plan_data["days"][0]["attractions"]]
        assert names[0] == "天安门"

    def test_day2_uses_prev_hotel(self):
        """Day2使用前一天酒店坐标作为起点"""
        plan_data = {
            "days": [
                {
                    "attractions": [_make_attraction("A", 116.3, 39.9)],
                    "hotel": {"location": {"longitude": 116.4, "latitude": 39.92}},
                },
                {
                    "attractions": [
                        _make_attraction("远景点", 116.2, 40.0),
                        _make_attraction("近景点", 116.41, 39.93),
                    ],
                },
            ],
        }
        request = type("Req", (), {"days": 2, "departure_city": "", "city": "北京"})()
        self.mgr.validate_and_fix_plan(plan_data, request, "classic")
        names = [a["name"] for a in plan_data["days"][1]["attractions"]]
        assert names[0] == "近景点"
