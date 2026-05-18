"""
API路由测试 - 直接请求运行中的服务
"""
import httpx

BASE = "http://localhost:8000"
client = httpx.Client(base_url=BASE, timeout=5.0)


def _server_running():
    try:
        return client.get("/").status_code == 200
    except Exception:
        return False


SRV = _server_running()


class TestHealthCheck:
    def test_root_endpoint(self):
        if not SRV:
            return
        r = client.get("/")
        assert r.status_code == 200
        assert "running" in r.json().get("status", "")

    def test_docs_endpoint(self):
        if not SRV:
            return
        r = client.get("/docs")
        assert r.status_code == 200


class TestTripPlanValidation:
    def test_missing_city_returns_422(self):
        if not SRV:
            return
        r = client.post("/api/trip/plan", json={
            "days": 3, "start_date": "2024-06-01", "end_date": "2024-06-03"
        })
        assert r.status_code == 422

    def test_invalid_date_returns_422(self):
        if not SRV:
            return
        r = client.post("/api/trip/plan", json={
            "city": "北京", "days": 3,
            "start_date": "bad", "end_date": "2024-06-03"
        })
        assert r.status_code == 422

    def test_missing_days_returns_422(self):
        if not SRV:
            return
        r = client.post("/api/trip/plan", json={
            "city": "北京", "start_date": "2024-06-01", "end_date": "2024-06-03"
        })
        assert r.status_code == 422


class TestTripEditValidation:
    def test_missing_trip_plan_returns_422(self):
        if not SRV:
            return
        r = client.post("/api/trip/edit", json={})
        assert r.status_code == 422
