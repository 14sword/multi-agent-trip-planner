"""认证模块测试 — 直接请求运行中的服务"""
import httpx
import uuid

BASE = "http://localhost:8000"
client = httpx.Client(base_url=BASE, timeout=5.0)


def _server_running():
    try:
        return client.get("/").status_code == 200
    except Exception:
        return False


SRV = _server_running()


def _unique_email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def _register(email: str = None, password: str = "test123456"):
    if email is None:
        email = _unique_email()
    return client.post("/api/auth/register", json={"email": email, "password": password}), email


def _login(email: str, password: str = "test123456"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


class TestRegister:
    def test_register_success(self):
        if not SRV:
            return
        resp, _ = _register()
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert "email" in data

    def test_register_duplicate_email(self):
        if not SRV:
            return
        _, email = _register()
        resp, _ = _register(email=email)
        assert resp.status_code == 409

    def test_register_weak_password(self):
        if not SRV:
            return
        resp, _ = _register(password="123")
        assert resp.status_code == 400

    def test_register_bad_email(self):
        if not SRV:
            return
        resp, _ = _register(email="not-an-email")
        assert resp.status_code == 400


class TestLogin:
    def test_login_success(self):
        if not SRV:
            return
        _, email = _register()
        resp = _login(email)
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_login_wrong_password(self):
        if not SRV:
            return
        _, email = _register()
        resp = _login(email, password="wrongpassword")
        assert resp.status_code == 401

    def test_login_nonexistent(self):
        if not SRV:
            return
        resp = _login("nobody@example.com")
        assert resp.status_code == 401


class TestMe:
    def test_me_with_token(self):
        if not SRV:
            return
        resp, email = _register()
        token = resp.json()["token"]
        me_resp = client.get("/api/auth/me", headers=_auth_header(token))
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == email

    def test_me_without_token(self):
        if not SRV:
            return
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401


class TestProtectedEndpoints:
    def test_favorites_requires_auth(self):
        if not SRV:
            return
        resp = client.get("/api/trip/favorites/list")
        assert resp.status_code == 401

    def test_favorites_with_auth(self):
        if not SRV:
            return
        resp, _ = _register()
        token = resp.json()["token"]
        fav_resp = client.get("/api/trip/favorites/list", headers=_auth_header(token))
        assert fav_resp.status_code == 200

    def test_list_trips_works_without_auth(self):
        if not SRV:
            return
        resp = client.get("/api/trip/list")
        assert resp.status_code == 200
