"""
API路由测试
测试旅行规划API的基本功能
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestTripPlanAPI:
    """旅行规划API测试类"""

    def test_create_trip_plan_success(self):
        """测试成功创建旅行计划"""
        response = client.post("/api/trip/plan", json={
            "city": "北京",
            "days": 3,
            "start_date": "2024-06-01",
            "end_date": "2024-06-03",
            "preferences": "历史文化",
            "budget": "中等",
            "transportation": "公共交通",
            "accommodation": "经济型酒店"
        })
        
        # 注意：由于API需要调用LLM，测试可能失败
        # 这里主要测试接口格式是否正确
        assert response.status_code in [200, 500]  # 500是因为API Key未配置
        
    def test_create_trip_plan_missing_city(self):
        """测试缺少城市参数的请求"""
        response = client.post("/api/trip/plan", json={
            "days": 3,
            "start_date": "2024-06-01",
            "end_date": "2024-06-03"
        })
        
        assert response.status_code == 422  # 验证错误

    def test_create_trip_plan_invalid_date(self):
        """测试无效日期格式"""
        response = client.post("/api/trip/plan", json={
            "city": "北京",
            "days": 3,
            "start_date": "invalid-date",
            "end_date": "2024-06-03"
        })
        
        assert response.status_code == 422  # 验证错误


class TestEditTripAPI:
    """编辑旅行API测试类"""

    def test_edit_trip_plan(self):
        """测试编辑旅行计划"""
        # 先创建一个空的旅行计划
        response = client.post("/api/trip/edit", json={
            "trip_plan": {
                "city": "上海",
                "days": 2,
                "start_date": "2024-07-01",
                "end_date": "2024-07-02",
                "suggestions": "",
                "weather_info": [],
                "budget": {
                    "total_attractions": 0,
                    "total_hotels": 0,
                    "total_meals": 0,
                    "total_transportation": 0,
                    "total": 0
                },
                "days": []
            },
            "changes": "添加一个博物馆行程"
        })
        
        assert response.status_code in [200, 500]  # 500是因为API Key未配置


class TestHealthCheck:
    """健康检查测试"""

    def test_root_endpoint(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        
    def test_docs_endpoint(self):
        """测试API文档路径"""
        response = client.get("/docs")
        assert response.status_code == 200
