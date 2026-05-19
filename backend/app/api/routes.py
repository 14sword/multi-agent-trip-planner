"""
API 路由 — 旅行规划 + CRUD + 分享 + 收藏 + CPS + 多方案 + 流式输出 + 路线规划
"""
import json
import logging
import os
import re
import time
import uuid
import secrets
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.models.schemas import TripPlanRequest, TripPlan, TripEditRequest
from app.agents.trip_planner import TripPlannerAgent
from app.agents.transport import estimate_transport
from app.services.unsplash import UnsplashService
from app.auth import hash_password, verify_password, create_access_token, require_user, get_current_user
from app import database as db
from app import templates as tpl

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/trip", tags=["trip"])

# ====== 认证路由 ======

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@auth_router.post("/register")
async def register(req: RegisterRequest):
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', req.email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")
    if db.get_user_by_email(req.email):
        raise HTTPException(status_code=409, detail="该邮箱已注册")
    pwd_hash = hash_password(req.password)
    user = db.create_user(req.email, pwd_hash)
    if not user:
        raise HTTPException(status_code=500, detail="注册失败")
    token = create_access_token(user["id"], user["email"])
    return {"user_id": user["id"], "email": user["email"], "token": token}


@auth_router.post("/login")
async def login(req: LoginRequest):
    user = db.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    token = create_access_token(user["id"], user["email"])
    return {"user_id": user["id"], "email": user["email"], "token": token}


@auth_router.get("/me")
async def me(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return {"user_id": user["user_id"], "email": user["email"]}


# ====== 路线规划代理（绕过 JS API Key 权限限制）=======

def _simplify_path(pts: list, tolerance: float = 0.0005) -> list:
    """Douglas-Peucker 路径简化，保留主干道路。"""
    if len(pts) <= 2:
        return pts
    sx, sy = pts[0]
    ex, ey = pts[-1]
    dx, dy = ex - sx, ey - sy
    len_sq = dx * dx + dy * dy
    if len_sq == 0:
        return [pts[0], pts[-1]]
    max_dist, max_idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        t = max(0.0, min(1.0, ((pts[i][0] - sx) * dx + (pts[i][1] - sy) * dy) / len_sq))
        px, py = sx + t * dx, sy + t * dy
        dist = ((pts[i][0] - px) ** 2 + (pts[i][1] - py) ** 2) ** 0.5
        if dist > max_dist:
            max_dist, max_idx = dist, i
    if max_dist > tolerance:
        left = _simplify_path(pts[:max_idx + 1], tolerance)
        right = _simplify_path(pts[max_idx:], tolerance)
        return left[:-1] + right
    return [pts[0], pts[-1]]

@router.get("/route")
async def get_route(origin: str, destination: str, mode: str = "driving", city: str = ""):
    """
    代理高德路线规划 REST API。
    origin/destination 格式: "lng,lat"
    mode: driving | walking | transit
    """
    amap_key = os.getenv("AMAP_API_KEY", "")
    if not amap_key:
        raise HTTPException(status_code=500, detail="AMAP_API_KEY 未配置")

    # 公交路线用综合出行 API
    if mode == "transit":
        url = "https://restapi.amap.com/v3/direction/transit/integrated"
        params = {
            "origin": origin,
            "destination": destination,
            "city": city or "",
            "key": amap_key,
            "strategy": 0,
            "extensions": "all",
        }
    else:
        api_type = "driving" if mode == "driving" else "walking"
        url = f"https://restapi.amap.com/v3/direction/{api_type}"
        params = {
            "origin": origin,
            "destination": destination,
            "key": amap_key,
            "extensions": "all",
        }
        if mode == "driving":
            params["strategy"] = 0

    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        if data.get("status") != "1" or not data.get("route"):
            info = data.get("info", "unknown")
            logger.warning(f"路线规划失败 [{mode}]: {info}")
            raise HTTPException(status_code=502, detail=f"路线规划失败: {info}")

        route = data["route"]
        paths = route.get("paths", [])
        if not paths:
            raise HTTPException(status_code=502, detail="未找到路线")

        # 提取坐标点
        path_coords = []
        if mode == "transit":
            # 公交：遍历所有 segments → steps
            for seg in paths[0].get("segments", []):
                busseg = seg.get("bus", {}).get("buslines", [])
                for bl in busseg:
                    for step in bl.get("steps", []):
                        polyline = step.get("polyline", "")
                        for pt in polyline.split(";"):
                            parts = pt.split(",")
                            if len(parts) == 2:
                                path_coords.append([float(parts[0]), float(parts[1])])
                # 步行段
                walkseg = seg.get("walking", {}).get("steps", [])
                for step in walkseg:
                    polyline = step.get("polyline", "")
                    for pt in polyline.split(";"):
                        parts = pt.split(",")
                        if len(parts) == 2:
                            path_coords.append([float(parts[0]), float(parts[1])])
        else:
            # 驾车/步行：steps 直接在 paths[0] 下
            steps = paths[0].get("steps", [])
            if not steps:
                for leg in paths[0].get("legs", []):
                    steps.extend(leg.get("steps", []))
            for step in steps:
                polyline = step.get("polyline", "")
                for pt in polyline.split(";"):
                    parts = pt.split(",")
                    if len(parts) == 2:
                        path_coords.append([float(parts[0]), float(parts[1])])

        distance = int(paths[0].get("distance", 0))
        duration = int(paths[0].get("duration", 0))

        if len(path_coords) > 30:
            path_coords = _simplify_path(path_coords, tolerance=0.0005)

        return {
            "path": path_coords,
            "distance": distance,
            "duration": duration,
            "mode": "transit" if mode == "transit" else ("walking" if mode == "walking" else "driving"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"路线规划异常 [{mode}]: {e}")
        raise HTTPException(status_code=502, detail=f"路线规划服务异常: {str(e)}")


@router.get("/trains")
async def search_trains(departure: str, arrival: str, date: str):
    """查询12306高铁/火车班次"""
    from app.services.transport_search import transport_search
    results = transport_search.search_trains(departure, arrival, date)
    return {"trains": results, "count": len(results)}


@router.get("/flights")
async def search_flights(departure: str, arrival: str, date: str):
    """查询航班信息"""
    from app.services.transport_search import transport_search
    results = transport_search.search_flights(departure, arrival, date)
    return {"flights": results, "count": len(results)}


# 单例
_planner: TripPlannerAgent | None = None
_unsplash: UnsplashService | None = None
_image_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="img")


def _get_planner() -> TripPlannerAgent:
    global _planner
    if _planner is None:
        _planner = TripPlannerAgent()
    return _planner


def _get_unsplash() -> UnsplashService:
    global _unsplash
    if _unsplash is None:
        _unsplash = UnsplashService()
    return _unsplash


# 中文景点名 → 英文搜索词
_ENGLISH_KEYWORDS = {
    "西湖": "West Lake Hangzhou", "故宫": "Forbidden City Beijing",
    "长城": "Great Wall China", "天安门": "Tiananmen Square Beijing",
    "外滩": "The Bund Shanghai", "东方明珠": "Oriental Pearl Tower Shanghai",
    "兵马俑": "Terracotta Warriors Xi'an", "鼓浪屿": "Gulangyu Xiamen",
    "黄山": "Mount Huangshan", "泰山": "Mount Tai",
    "丽江古城": "Lijiang Old Town", "大理古城": "Dali Old Town",
    "布达拉宫": "Potala Palace Lhasa", "九寨沟": "Jiuzhaigou Valley",
    "峨眉山": "Mount Emei", "漓江": "Li River Guilin",
    "张家界": "Zhangjiajie National Park", "敦煌莫高窟": "Mogao Caves Dunhuang",
    "颐和园": "Summer Palace Beijing", "圆明园": "Old Summer Palace Beijing",
    "拙政园": "Humble Administrator Garden Suzhou", "周庄": "Zhouzhuang Water Town",
    "乌镇": "Wuzhen Water Town", "三亚": "Sanya Beach Hainan",
    "成都大熊猫": "Chengdu Giant Panda", "宽窄巷子": "Kuanzhai Alley Chengdu",
    "锦里": "Jinli Ancient Street Chengdu", "回民街": "Muslim Quarter Xi'an",
    "黄鹤楼": "Yellow Crane Tower Wuhan", "滕王阁": "Tengwang Pavilion Nanchang",
    "岳阳楼": "Yueyang Tower",
}


def _fetch_amap_photo(lat: float, lng: float) -> str | None:
    amap_key = os.getenv("AMAP_API_KEY", "")
    if not amap_key:
        return None
    try:
        resp = httpx.get(
            "https://restapi.amap.com/v3/place/around",
            params={"location": f"{lng},{lat}", "radius": 500, "types": "风景名胜",
                    "extensions": "all", "key": amap_key, "offset": 1},
            timeout=5.0, trust_env=False,
        )
        data = resp.json()
        pois = data.get("pois", [])
        if pois:
            photos = pois[0].get("photos", [])
            if photos:
                return photos[0].get("url")
    except Exception as e:
        logger.debug(f"高德POI图片获取失败: {e}")
    return None


def _enrich_images(trip_plan: TripPlan, city: str, unsplash: UnsplashService, force: bool = False) -> None:
    for day in trip_plan.days:
        for attraction in day.attractions:
            if not force and attraction.image_url:
                continue
            image_url = None
            if attraction.location:
                image_url = _fetch_amap_photo(attraction.location.latitude, attraction.location.longitude)
            if not image_url:
                en_kw = _ENGLISH_KEYWORDS.get(attraction.name, "")
                query = f"{attraction.name} {en_kw} {city}".strip() if en_kw else f"{attraction.name} {city}"
                image_url = unsplash.get_photo_url(query)
            if not image_url:
                image_url = unsplash.get_photo_url(f"{city} China cityscape")
            attraction.image_url = image_url


def _get_client_id(request: Request) -> str:
    return request.client.host if request.client else "unknown"


_DISCLAIMER_PATTERNS = [
    "数据源暂时不可用", "基于规划师专业知识", "基于专业知识生成",
    "数据源不可用", "数据暂不可用", "请核实景区开放时间",
    "请核实", "数据来源", "仅供参考", "建议提前确认",
]


def _strip_disclaimer(text: str) -> str:
    """移除 overall_suggestions 中的数据来源声明。"""
    if not text:
        return text
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        if any(p in line for p in _DISCLAIMER_PATTERNS):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


# ====== CPS 酒店/机票链接 ======

_CPS_PLATFORMS = {
    "ctrip": {"name": "携程", "base": "https://m.ctrip.com/webapp/hotel/hotellist", "param": "keyword"},
    "qunar": {"name": "去哪儿", "base": "https://m.qunar.com/hotel", "param": "keyword"},
    "fliggy": {"name": "飞猪", "base": "https://www.fliggy.com/hotel", "param": "keyword"},
}


def _build_cps_links(city: str, hotel_name: str = "") -> dict:
    keyword = f"{city} {hotel_name}".strip()
    links = {}
    for platform, cfg in _CPS_PLATFORMS.items():
        links[platform] = {
            "name": cfg["name"],
            "url": f"{cfg['base']}?{cfg['param']}={keyword}",
        }
    links["flight"] = {
        "name": "机票比价",
        "url": f"https://www.ly.com/flights?departCity=&arriveCity={city}",
    }
    return links


# ====== 核心接口 ======

@router.post("/plan", response_model=TripPlan)
async def create_trip_plan(request: TripPlanRequest, req: Request) -> TripPlan:
    client_id = _get_client_id(req)
    db.log_api_usage(client_id, "/api/trip/plan")
    user = get_current_user(req)
    user_id = user["user_id"] if user else None

    logger.info(f"收到旅行规划请求: {request.city} {request.days}天 departure={request.departure_city}")

    try:
        template = tpl.get_template(request.city)

        if template and request.days <= len(template["days"]):
            logger.info(f"命中模板: {request.city}，秒出方案")
            from app.models.schemas import DayPlan, Attraction, Meal, WeatherInfo, Budget
            template_days = template["days"][:request.days]
            days = []
            for i, td in enumerate(template_days):
                attractions = [Attraction(**a) for a in td["attractions"]]
                meals = [Meal(**m) for m in td["meals"]]
                day_date = (
                    request.start_date if not request.start_date
                    else (__import__("datetime").datetime.strptime(request.start_date, "%Y-%m-%d")
                          + __import__("datetime").timedelta(days=i)).strftime("%Y-%m-%d")
                )
                days.append(DayPlan(
                    date=day_date,
                    day_index=i,
                    description=td["description"],
                    transportation=td["transportation"],
                    accommodation=td["accommodation"],
                    attractions=attractions,
                    meals=meals,
                ))

            weather_info = [WeatherInfo(date=day.date, day_weather="晴", night_weather="多云",
                                        day_temp=25, night_temp=15,
                                        wind_direction="南风", wind_power="1-3级") for day in days]
            trip_plan = TripPlan(
                city=request.city,
                start_date=request.start_date,
                end_date=request.end_date,
                days=days,
                weather_info=weather_info,
                overall_suggestions=template.get("overall_suggestions", ""),
            )

            if request.departure_city and request.departure_city != request.city:
                transport = estimate_transport(request.departure_city, request.city)
                trip_plan.transport_info = transport
                trip_plan.departure_city = request.departure_city

            planner = _get_planner()
            planner.update_budget(trip_plan, request.transportation)
        else:
            planner = _get_planner()
            trip_plan = planner.plan_trip(request)
            planner.update_budget(trip_plan, request.transportation)

        unsplash = _get_unsplash()
        _enrich_images(trip_plan, request.city, unsplash)

        # 清理声明性文字
        trip_plan.overall_suggestions = _strip_disclaimer(trip_plan.overall_suggestions or "")

        # 持久化
        trip_id = str(uuid.uuid4())[:8]
        share_token = secrets.token_urlsafe(8)
        db.save_trip(trip_id, request.city, request.start_date, request.end_date,
                     request.days, trip_plan.model_dump(), share_token, user_id=user_id)
        trip_plan.id = trip_id
        trip_plan.share_token = share_token
        trip_plan.cps_links = _build_cps_links(request.city)

        logger.info(f"旅行规划完成: {request.city} (id={trip_id})")
        return trip_plan
    except Exception as e:
        logger.error(f"生成计划失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="生成旅行计划失败，请稍后重试")


# ====== 流式输出 ======

@router.post("/plan/stream")
async def create_trip_plan_stream(request: TripPlanRequest, req: Request):
    """SSE 流式生成旅行计划，实时推送进度。"""
    client_id = _get_client_id(req)
    db.log_api_usage(client_id, "/api/trip/plan/stream")
    user = get_current_user(req)
    user_id = user["user_id"] if user else None

    def event_generator():
        try:
            yield _sse("progress", "景点专家搜索中...")
            time.sleep(0.8)
            logger.info(f"流式规划: {request.city} {request.days}天")

            yield _sse("progress", "天气专家查询中...")
            time.sleep(0.8)
            planner = _get_planner()
            unsplash = _get_unsplash()

            # 获取信息
            attraction_info, weather_info, hotel_info = planner._fetch_info_directly(
                request.city, request.preferences_text, request.accommodation, request.budget
            )

            yield _sse("progress", "规划专家整合中...")
            time.sleep(0.6)

            # 生成计划
            plan_data = planner.generate_plan(request, attraction_info, weather_info, hotel_info)
            if not plan_data:
                yield _sse("error", "生成计划失败，请稍后重试")
                return

            for key in ("days", "weather_info"):
                val = plan_data.get(key)
                if isinstance(val, str):
                    try:
                        plan_data[key] = json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        plan_data[key] = []
                elif not isinstance(val, list):
                    plan_data[key] = []

            if isinstance(plan_data.get("days"), list) and len(plan_data["days"]) > request.days:
                plan_data["days"] = plan_data["days"][:request.days]
            if isinstance(plan_data.get("weather_info"), list) and len(plan_data["weather_info"]) > request.days:
                plan_data["weather_info"] = plan_data["weather_info"][:request.days]

            # 天气日期映射
            from datetime import datetime, timedelta
            try:
                start = datetime.strptime(request.start_date, "%Y-%m-%d")
                for i, w in enumerate(plan_data.get("weather_info", [])):
                    if isinstance(w, dict):
                        w["date"] = (start + timedelta(days=i)).strftime("%Y-%m-%d")
            except Exception:
                pass

            planner.coord_manager.enrich_empty_days(plan_data, attraction_info, hotel_info)

            try:
                trip_plan = TripPlan(**plan_data)
            except Exception as e:
                logger.error(f"TripPlan 验证失败: {e}")
                trip_plan = planner._build_plan_fallback(plan_data, request)

            # 图片后台加载，不阻塞流式输出
            _image_executor.submit(
                _enrich_images, trip_plan, request.city, unsplash
            )

            yield _sse("progress", "整理专家汇总中...")
            time.sleep(0.5)

            # 清理声明性文字
            trip_plan.overall_suggestions = _strip_disclaimer(trip_plan.overall_suggestions or "")

            # 持久化
            trip_id = str(uuid.uuid4())[:8]
            share_token = secrets.token_urlsafe(8)
            db.save_trip(trip_id, request.city, request.start_date, request.end_date,
                         request.days, trip_plan.model_dump(), share_token, user_id=user_id)
            trip_plan.id = trip_id
            trip_plan.share_token = share_token
            trip_plan.cps_links = _build_cps_links(request.city)

            yield _sse("result", trip_plan.model_dump())
            logger.info(f"流式规划完成: {request.city} (id={trip_id})")

        except Exception as e:
            logger.error(f"流式规划失败: {e}", exc_info=True)
            yield _sse("error", "生成旅行计划失败，请稍后重试")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(event: str, data) -> str:
    """构造 SSE 事件字符串。"""
    if isinstance(data, dict):
        data = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {data}\n\n"


@router.post("/edit", response_model=TripPlan)
async def edit_trip_plan(request: TripEditRequest, req: Request) -> TripPlan:
    client_id = _get_client_id(req)
    db.log_api_usage(client_id, "/api/trip/edit")

    logger.info(f"收到行程编辑请求: {request.trip_plan.city}")
    try:
        planner = _get_planner()
        unsplash = _get_unsplash()
        updated_plan = planner.update_budget(request.trip_plan)
        _enrich_images(updated_plan, updated_plan.city, unsplash, force=True)

        # 更新持久化
        if request.trip_plan.id:
            db.update_trip(request.trip_plan.id, updated_plan.model_dump())

        updated_plan.cps_links = _build_cps_links(updated_plan.city)
        logger.info(f"行程编辑完成: {updated_plan.city}")
        return updated_plan
    except Exception as e:
        logger.error(f"编辑计划失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="编辑旅行计划失败，请稍后重试")


# ====== 多方案对比 ======

@router.post("/plan/variants")
async def create_plan_variants(request: TripPlanRequest, req: Request) -> dict:
    """生成 3 个方案变体: 经典高效/轻松休闲/深度探索（同一预算，并行生成）"""
    client_id = _get_client_id(req)
    db.log_api_usage(client_id, "/api/trip/plan/variants")
    user = get_current_user(req)
    user_id = user["user_id"] if user else None

    variant_configs = [
        ("classic", "经典高效"),
        ("relaxed", "轻松休闲"),
        ("deep", "深度探索"),
    ]
    planner = _get_planner()
    unsplash = _get_unsplash()

    def generate_one(variant_key: str, style_name: str) -> dict:
        try:
            plan = planner.plan_trip(request, variant_key=variant_key)
            planner.update_budget(plan, request.transportation)
            _enrich_images(plan, request.city, unsplash)
            plan.id = str(uuid.uuid4())[:8]
            plan.share_token = secrets.token_urlsafe(8)
            db.save_trip(plan.id, request.city, request.start_date, request.end_date,
                         request.days, plan.model_dump(), plan.share_token, user_id=user_id)
            plan.cps_links = _build_cps_links(request.city)
            return {"variant": variant_key, "style_name": style_name, "plan": plan}
        except Exception as e:
            logger.error(f"方案 {style_name} 生成失败: {e}")
            return {"variant": variant_key, "style_name": style_name, "plan": None, "error": str(e)}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(generate_one, v, s): v
            for v, s in variant_configs
        }
        variants = []
        for future in as_completed(futures):
            variants.append(future.result())

    order = {"classic": 0, "relaxed": 1, "deep": 2}
    variants.sort(key=lambda x: order.get(x["variant"], 99))

    return {"variants": variants}


# ====== CRUD ======

@router.get("/list")
async def list_trips(request: Request):
    user = get_current_user(request)
    user_id = user["user_id"] if user else None
    return {"trips": db.list_trips(user_id=user_id)}


@router.get("/{trip_id}")
async def get_trip(trip_id: str):
    trip = db.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    plan = TripPlan(**trip["plan_data"])
    plan.id = trip["id"]
    plan.share_token = trip.get("share_token")
    plan.cps_links = _build_cps_links(plan.city)
    return plan


@router.delete("/{trip_id}")
async def delete_trip(trip_id: str, request: Request):
    user = get_current_user(request)
    trip = db.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    if user and trip.get("user_id") and trip["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="无权删除此行程")
    if not db.delete_trip(trip_id):
        raise HTTPException(status_code=404, detail="行程不存在")
    return {"ok": True}


# ====== 分享 ======

@router.get("/share/{token}")
async def get_shared_trip(token: str):
    trip = db.get_trip_by_share_token(token)
    if not trip:
        raise HTTPException(status_code=404, detail="分享链接无效或已过期")
    plan = TripPlan(**trip["plan_data"])
    plan.id = trip["id"]
    plan.share_token = trip.get("share_token")
    plan.cps_links = _build_cps_links(plan.city)
    return plan


# ====== 收藏 ======

@router.post("/favorite/{trip_id}")
async def add_favorite(trip_id: str, request: Request):
    user = require_user(request)
    if not db.get_trip(trip_id):
        raise HTTPException(status_code=404, detail="行程不存在")
    ok = db.add_favorite(trip_id, user_id=user["user_id"])
    return {"ok": ok, "added": ok}


@router.delete("/favorite/{trip_id}")
async def remove_favorite(trip_id: str, request: Request):
    user = require_user(request)
    ok = db.remove_favorite(trip_id, user_id=user["user_id"])
    return {"ok": ok}


@router.get("/favorites/list")
async def list_favorites(request: Request):
    user = require_user(request)
    favs = db.list_favorites(user_id=user["user_id"])
    result = []
    for f in favs:
        trip = db.get_trip(f["id"])
        if trip:
            plan = TripPlan(**trip["plan_data"])
            plan.id = trip["id"]
            plan.share_token = trip.get("share_token")
            result.append(plan)
    return {"favorites": result}
