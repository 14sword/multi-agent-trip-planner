"""
坐标数据 + 路线优化 + 地理编码兜底
"""
import math
import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# ── 城市中心坐标（纬度, 经度）─────────────────────────────
CITY_COORDS: Dict[str, Tuple[float, float]] = {
    "北京": (39.9042, 116.4074), "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644), "深圳": (22.5431, 114.0579),
    "成都": (30.5728, 104.0668), "杭州": (30.2741, 120.1551),
    "重庆": (29.5630, 106.5516), "武汉": (30.5928, 114.3055),
    "西安": (34.3416, 108.9398), "南京": (32.0603, 118.7969),
    "长沙": (28.2282, 112.9388), "郑州": (34.7466, 113.6253),
    "天津": (39.3434, 117.3616), "苏州": (31.2990, 120.5853),
    "厦门": (24.4798, 118.0894), "昆明": (25.0389, 102.7183),
    "大连": (38.9140, 121.6147), "济南": (36.6512, 116.9972),
    "青岛": (36.0671, 120.3826), "沈阳": (41.8057, 123.4315),
    "哈尔滨": (45.8038, 126.5350), "长春": (43.8868, 125.3245),
    "合肥": (31.8206, 117.2272), "福州": (26.0745, 119.2965),
    "南昌": (28.6820, 115.8579), "贵阳": (26.6470, 106.6302),
    "南宁": (22.8170, 108.3665), "兰州": (36.0611, 103.8343),
    "太原": (37.8706, 112.5489), "石家庄": (38.0428, 114.5149),
    "乌鲁木齐": (43.8256, 87.6168), "拉萨": (29.6500, 91.1000),
    "海口": (20.0174, 110.3492), "三亚": (18.2528, 109.5120),
    "丽江": (26.8721, 100.2299), "大理": (25.6065, 100.2676),
    "桂林": (25.2744, 110.2990), "珠海": (22.2710, 113.5767),
    "东莞": (23.0207, 113.7518), "佛山": (23.0218, 113.1218),
    "宁波": (29.8683, 121.5440), "温州": (28.0000, 120.6722),
}

# ── 城市消费等级 ──────────────────────────────────────────
CITY_TIERS = {
    1: {"cities": ["北京", "上海", "广州", "深圳"], "meal": "80-150", "hotel": "400-800", "multiplier": 1.2},
    2: {"cities": ["杭州", "成都", "重庆", "武汉", "南京", "西安", "苏州"], "meal": "50-120", "hotel": "300-600", "multiplier": 1.0},
    3: {"cities": ["长沙", "郑州", "青岛", "大连", "厦门", "昆明", "合肥", "福州", "宁波", "无锡"], "meal": "40-90", "hotel": "200-400", "multiplier": 0.85},
    4: {"cities": ["丽江", "大理", "桂林", "三亚", "拉萨", "海口"], "meal": "35-80", "hotel": "200-500", "multiplier": 0.8},
}


def get_city_tier(city: str) -> dict:
    for tier, info in CITY_TIERS.items():
        if city in info["cities"]:
            return {"tier": tier, "meal": info["meal"], "hotel": info["hotel"], "multiplier": info["multiplier"]}
    return {"tier": 3, "meal": "40-90", "hotel": "200-400", "multiplier": 0.9}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── 主要城市机场/车站坐标（经度, 纬度）GCJ-02 ────────────
AIRPORT_STATION_COORDS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "北京": {"飞机": (116.6031, 40.0801), "高铁": (116.3783, 39.8652)},
    "上海": {"飞机": (121.8056, 31.1434), "高铁": (121.3272, 31.1942)},
    "广州": {"飞机": (113.2988, 23.3924), "高铁": (113.2644, 23.1492)},
    "深圳": {"飞机": (113.8104, 22.6385), "高铁": (114.0242, 22.6097)},
    "成都": {"飞机": (103.9272, 30.5785), "高铁": (104.0668, 30.6333)},
    "杭州": {"飞机": (120.4341, 30.2295), "高铁": (120.1551, 30.2741)},
    "重庆": {"飞机": (106.6329, 29.7192), "高铁": (106.5516, 29.5630)},
    "武汉": {"飞机": (114.2090, 30.7844), "高铁": (114.3055, 30.5928)},
    "西安": {"飞机": (108.7510, 34.4414), "高铁": (108.9398, 34.3416)},
    "南京": {"飞机": (118.8624, 31.7413), "高铁": (118.7969, 32.0603)},
    "长沙": {"飞机": (113.2200, 28.1892), "高铁": (112.9388, 28.2282)},
    "昆明": {"飞机": (102.7460, 24.9873), "高铁": (102.7183, 25.0389)},
    "厦门": {"飞机": (118.1260, 24.5582), "高铁": (118.0894, 24.4798)},
    "青岛": {"飞机": (120.3744, 36.3656), "高铁": (120.3826, 36.0671)},
    "三亚": {"飞机": (109.4085, 18.3060), "高铁": (109.5120, 18.2528)},
    "哈尔滨": {"飞机": (126.2516, 45.6294), "高铁": (126.5350, 45.8038)},
    "天津": {"高铁": (117.2142, 39.1373)},
    "大连": {"飞机": (121.5386, 38.9657), "高铁": (121.6520, 38.9753)},
    "沈阳": {"飞机": (123.4895, 41.6398), "高铁": (123.4303, 41.8152)},
    "济南": {"飞机": (117.2161, 36.8570), "高铁": (116.8903, 36.6776)},
    "郑州": {"飞机": (113.8436, 34.5193), "高铁": (113.7652, 34.7532)},
    "合肥": {"飞机": (117.0037, 31.9897), "高铁": (117.3042, 31.7951)},
    "石家庄": {"飞机": (114.6964, 38.2809), "高铁": (114.4890, 38.0058)},
    "太原": {"飞机": (112.6281, 37.7469), "高铁": (112.6181, 37.7842)},
    "苏州": {"高铁": (120.6205, 31.3165)},
    "无锡": {"高铁": (120.3016, 31.5745)},
    "南昌": {"高铁": (115.8035, 28.6820)},
    "贵阳": {"高铁": (106.6815, 26.6575)},
    "南宁": {"飞机": (108.1793, 22.6086), "高铁": (108.3518, 22.8170)},
    "兰州": {"飞机": (103.6262, 36.5146), "高铁": (103.8560, 36.0491)},
    "呼和浩特": {"飞机": (111.8227, 40.8515), "高铁": (111.7510, 40.8363)},
    "丽江": {"飞机": (100.2456, 26.6797)},
    "大理": {"飞机": (100.3192, 25.6493)},
    "珠海": {"飞机": (113.3760, 22.0105)},
    "宁波": {"高铁": (121.5447, 29.8535)},
    "福州": {"飞机": (119.6643, 25.9358), "高铁": (119.3720, 26.0453)},
}


class CoordinateManager:
    """路线优化 + 数据校验 + 地理编码兜底 + 文本提取"""

    def __init__(self, mcp_client=None):
        self.mcp_client = mcp_client

    # ── 路线优化 ──────────────────────────────────────────

    def optimize_daily_route(self, day: dict, start_coords: tuple,
                             variant_key: str = "classic") -> None:
        attractions = day.get("attractions", [])
        if len(attractions) < 2:
            return

        indexed = []
        for idx, attr in enumerate(attractions):
            loc = attr.get("location") if isinstance(attr, dict) else None
            if loc and isinstance(loc, dict):
                lng = loc.get("longitude")
                lat = loc.get("latitude")
                if lng and lat and (lng != 0 or lat != 0):
                    indexed.append((idx, lng, lat))

        if len(indexed) < 2:
            return

        def _dist(c1, c2):
            return haversine_km(c1[1], c1[0], c2[1], c2[0])

        if variant_key == "relaxed":
            ordered = list(range(len(indexed)))
            total_orig = sum(
                _dist((indexed[ordered[j]][1], indexed[ordered[j]][2]),
                      (indexed[ordered[j + 1]][1], indexed[ordered[j + 1]][2]))
                for j in range(len(ordered) - 1)
            )
            improved = True
            while improved:
                improved = False
                for k in range(len(ordered) - 1):
                    trial = ordered[:k] + [ordered[k + 1], ordered[k]] + ordered[k + 2:]
                    trial_dist = sum(
                        _dist((indexed[trial[j]][1], indexed[trial[j]][2]),
                              (indexed[trial[j + 1]][1], indexed[trial[j + 1]][2]))
                        for j in range(len(trial) - 1)
                    )
                    if trial_dist < total_orig * 0.5:
                        ordered = trial
                        total_orig = trial_dist
                        improved = True

        elif variant_key == "deep":
            cat_groups: Dict[str, List[int]] = {}
            no_cat: List[int] = []
            for j, (orig_idx, lng, lat) in enumerate(indexed):
                attr = attractions[orig_idx]
                cat = attr.get("category", "") if isinstance(attr, dict) else ""
                if cat:
                    cat_groups.setdefault(cat, []).append(j)
                else:
                    no_cat.append(j)

            ordered = []
            current = start_coords
            all_groups = list(cat_groups.values()) + ([no_cat] if no_cat else [])
            while any(g for g in all_groups if g):
                def _group_dist(gi):
                    g = all_groups[gi]
                    if not g:
                        return float('inf')
                    return min(_dist(current, (indexed[j][1], indexed[j][2])) for j in g)

                best_group = min(range(len(all_groups)), key=_group_dist)
                group = all_groups[best_group]
                while group:
                    best_j = min(group, key=lambda j: _dist(current, (indexed[j][1], indexed[j][2])))
                    ordered.append(best_j)
                    current = (indexed[best_j][1], indexed[best_j][2])
                    group.remove(best_j)
        else:
            # classic: 严格最近邻
            ordered = []
            remaining = list(range(len(indexed)))
            current = start_coords
            while remaining:
                best_idx = min(remaining, key=lambda j: _dist(current, (indexed[j][1], indexed[j][2])))
                ordered.append(best_idx)
                current = (indexed[best_idx][1], indexed[best_idx][2])
                remaining.remove(best_idx)

        no_coords = [attractions[j] for j in range(len(attractions))
                     if j not in {x[0] for x in indexed}]
        reordered = [attractions[indexed[x][0]] for x in ordered] + no_coords
        day["attractions"] = reordered

    # ── 数据校验 ──────────────────────────────────────────

    def validate_and_fix_plan(self, plan_data: dict, request, variant_key: str = "classic") -> None:
        days = plan_data.get("days", [])
        if not isinstance(days, list):
            return

        # 城市坐标边界：确保所有 POI 在目的地城市范围内（排除出发城市坐标）
        city = getattr(request, 'city', '')
        city_center = CITY_COORDS.get(city)
        departure_city = getattr(request, 'departure_city', '')
        departure_center = CITY_COORDS.get(departure_city) if departure_city else None

        def _in_city_bounds(lng: float, lat: float) -> bool:
            """检查坐标是否在目的地城市 100km 范围内"""
            if not city_center:
                return True  # 未知城市不做过滤
            dist = haversine_km(city_center[0], city_center[1], lat, lng)
            return dist < 100

        def _is_departure_city(lng: float, lat: float) -> bool:
            """检查坐标是否在出发城市范围内"""
            if not departure_center:
                return False
            dist = haversine_km(departure_center[0], departure_center[1], lat, lng)
            return dist < 30

        for i, day in enumerate(days):
            if not isinstance(day, dict):
                continue

            for attr in day.get("attractions", []):
                if not isinstance(attr, dict):
                    continue
                dur = attr.get("visit_duration", 60)
                if isinstance(dur, (int, float)):
                    attr["visit_duration"] = max(30, min(240, int(dur)))
                loc = attr.get("location")
                if isinstance(loc, dict):
                    lat = loc.get("latitude", 0) or 0
                    lng = loc.get("longitude", 0) or 0
                    if lat == 0 or lng == 0 or lat < 15 or lat > 55 or lng < 70 or lng > 140:
                        attr["location"] = None
                    elif not _in_city_bounds(lng, lat):
                        logger.warning(f"景点 {attr.get('name')} 坐标在城市范围外，清除")
                        attr["location"] = None

            hotel = day.get("hotel")
            if isinstance(hotel, dict):
                hloc = hotel.get("location")
                if isinstance(hloc, dict):
                    hlat = hloc.get("latitude", 0) or 0
                    hlng = hloc.get("longitude", 0) or 0
                    if hlat == 0 or hlng == 0 or hlat < 15 or hlat > 55 or hlng < 70 or hlng > 140:
                        hotel["location"] = None
                    elif not _in_city_bounds(hlng, hlat):
                        logger.warning(f"酒店 {hotel.get('name')} 坐标在城市范围外，清除")
                        hotel["location"] = None
                hcost = hotel.get("estimated_cost")
                if not isinstance(hcost, (int, float)) or hcost <= 0:
                    hotel["estimated_cost"] = 300

            meals = day.get("meals", [])
            if isinstance(meals, list):
                for meal in meals:
                    if isinstance(meal, dict):
                        cost = meal.get("estimated_cost", 0)
                        if not isinstance(cost, (int, float)) or cost <= 0:
                            meal["estimated_cost"] = 50
                        mloc = meal.get("location")
                        if isinstance(mloc, dict):
                            mlat = mloc.get("latitude", 0) or 0
                            mlng = mloc.get("longitude", 0) or 0
                            if mlat == 0 or mlng == 0 or mlat < 15 or mlat > 55 or mlng < 70 or mlng > 140:
                                meal["location"] = None
                            elif _is_departure_city(mlng, mlat):
                                logger.warning(f"餐厅 {meal.get('name')} 坐标在出发城市，清除")
                                meal["location"] = None

        if len(days) > request.days:
            plan_data["days"] = days[:request.days]

        transport_info = plan_data.get("transport_info") or {}
        for i, day in enumerate(plan_data.get("days", [])):
            if not isinstance(day, dict):
                continue
            attractions = day.get("attractions", [])
            if len(attractions) < 2:
                continue
            if i == 0:
                arr_lng = transport_info.get("arrival_longitude")
                arr_lat = transport_info.get("arrival_latitude")
                if arr_lng and arr_lat:
                    start = (arr_lng, arr_lat)
                else:
                    hotel = day.get("hotel", {})
                    hloc = hotel.get("location") if isinstance(hotel, dict) else None
                    start = (hloc["longitude"], hloc["latitude"]) if hloc else None
            else:
                prev_hotel = plan_data["days"][i - 1].get("hotel", {}) if i > 0 else {}
                prev_loc = prev_hotel.get("location") if isinstance(prev_hotel, dict) else None
                start = (prev_loc["longitude"], prev_loc["latitude"]) if prev_loc else None
            if start:
                self.optimize_daily_route(day, start, variant_key)

    # ── 地理编码兜底 ──────────────────────────────────────

    def geocode_missing_coords(self, plan_data: dict, city: str) -> None:
        if not self.mcp_client:
            return
        geocoded = 0
        for day in plan_data.get("days", []):
            if not isinstance(day, dict):
                continue
            for attr in day.get("attractions", []):
                if not isinstance(attr, dict):
                    continue
                loc = attr.get("location")
                if isinstance(loc, dict) and loc.get("longitude") and loc.get("latitude"):
                    continue
                address = attr.get("address", "")
                name = attr.get("name", "")
                query = address or (f"{name} {city}" if name else "")
                if not query:
                    continue
                result = self.mcp_client.geocode(query, city)
                if result:
                    attr["location"] = result
                    geocoded += 1

            hotel = day.get("hotel")
            if isinstance(hotel, dict):
                loc = hotel.get("location")
                if not (isinstance(loc, dict) and loc.get("longitude") and loc.get("latitude")):
                    query = hotel.get("address", "") or (f"{hotel.get('name', '')} {city}" if hotel.get("name") else "")
                    if query:
                        result = self.mcp_client.geocode(query, city)
                        if result:
                            hotel["location"] = result
                            geocoded += 1

            for meal in day.get("meals", []):
                if not isinstance(meal, dict):
                    continue
                loc = meal.get("location")
                if isinstance(loc, dict) and loc.get("longitude") and loc.get("latitude"):
                    continue
                query = meal.get("address", "") or (f"{meal.get('name', '')} {city}" if meal.get("name") else "")
                if query:
                    result = self.mcp_client.geocode(query, city)
                    if result:
                        meal["location"] = result
                        geocoded += 1
        if geocoded > 0:
            logger.info(f"  地理编码补充了 {geocoded} 个坐标")

    # ── 数据补全 ──────────────────────────────────────────

    def enrich_empty_days(self, plan_data: dict, attraction_info: str,
                          hotel_info: str, budget: str = "中等") -> None:
        days = plan_data.get("days", [])
        if not isinstance(days, list):
            return

        extracted = extract_attractions_from_text(attraction_info)
        logger.info(f"  从文本提取到景点: {len(extracted)} 个")

        extracted_hotels = extract_hotels_from_text(hotel_info)
        logger.info(f"  从文本提取到酒店: {len(extracted_hotels)} 个")

        for i, day in enumerate(days):
            if not isinstance(day, dict):
                continue

            day.setdefault("day_index", i)
            if not day.get("date"):
                from datetime import datetime, timedelta
                try:
                    start = datetime.strptime(plan_data.get("start_date", ""), "%Y-%m-%d")
                    day["date"] = (start + timedelta(days=i)).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    day["date"] = plan_data.get("start_date", "")
            day.setdefault("description", f"第{i+1}天行程")

            attrs = day.get("attractions", [])
            if (not attrs or len(attrs) == 0) and extracted:
                day["attractions"] = extracted[:3]
                extracted[:] = extracted[3:]
                logger.info(f"  补全 day {i+1} attractions: {len(day['attractions'])} 个")
            elif not attrs or len(attrs) == 0:
                logger.warning(f"  day {i+1} 无景点数据（MCP/LLM 均未提供）")

            meals = day.get("meals", [])
            if not meals or len(meals) < 2:
                budget_costs = {
                    "经济型": {"breakfast": 15, "lunch": 35, "dinner": 40},
                    "经济": {"breakfast": 15, "lunch": 35, "dinner": 40},
                    "中等": {"breakfast": 25, "lunch": 60, "dinner": 80},
                    "舒适": {"breakfast": 40, "lunch": 100, "dinner": 120},
                    "豪华": {"breakfast": 60, "lunch": 150, "dinner": 200},
                }
                costs = budget_costs.get(budget, budget_costs["中等"])
                day["meals"] = [
                    {"type": "breakfast", "name": "酒店早餐/当地早茶", "estimated_cost": costs["breakfast"]},
                    {"type": "lunch", "name": "当地特色午餐", "estimated_cost": costs["lunch"]},
                    {"type": "dinner", "name": "风味晚餐", "estimated_cost": costs["dinner"]},
                ]
                logger.info(f"  补全 day {i+1} meals: 3 餐")

            # 坐标兜底
            ref_loc = None
            for a in day.get("attractions", []):
                loc = a.get("location")
                if isinstance(loc, dict) and loc.get("longitude") and loc.get("latitude"):
                    ref_loc = loc
                    break

            if not ref_loc and i > 0:
                prev_day = days[i - 1]
                for a in prev_day.get("attractions", []):
                    loc = a.get("location")
                    if isinstance(loc, dict) and loc.get("longitude") and loc.get("latitude"):
                        ref_loc = loc
                        break

            if not ref_loc:
                city = plan_data.get("city", "")
                if city in CITY_COORDS:
                    lat, lng = CITY_COORDS[city]
                    ref_loc = {"longitude": lng, "latitude": lat}

            hotel = day.get("hotel")
            if isinstance(hotel, dict) and ref_loc:
                hloc = hotel.get("location")
                has_valid = isinstance(hloc, dict) and hloc.get("longitude") and hloc.get("latitude")
                if not has_valid:
                    h_name = hotel.get("name", "")
                    matched = None
                    if extracted_hotels:
                        matched = next((eh for eh in extracted_hotels
                                        if eh["name"] in h_name or h_name in eh["name"]), None)
                        if not matched:
                            matched = extracted_hotels[0]
                    if matched and matched.get("location"):
                        hotel["location"] = matched["location"]
                    else:
                        hotel["location"] = ref_loc.copy()
                    logger.info(f"  day {i+1} 酒店坐标兜底: {hotel.get('name', '?')}")

            meal_ref = ref_loc
            hotel = day.get("hotel")
            if isinstance(hotel, dict):
                hloc = hotel.get("location")
                if isinstance(hloc, dict) and hloc.get("longitude") and hloc.get("latitude"):
                    meal_ref = hloc
            meal_offsets = {
                "breakfast": (0.0005, 0.0003), "早餐": (0.0005, 0.0003),
                "lunch": (-0.0005, -0.0004), "午餐": (-0.0005, -0.0004),
                "dinner": (0.0003, -0.0005), "晚餐": (0.0003, -0.0005),
            }
            for meal in day.get("meals", []):
                if isinstance(meal, dict) and meal_ref:
                    mloc = meal.get("location")
                    has_valid = isinstance(mloc, dict) and mloc.get("longitude") and mloc.get("latitude")
                    if not has_valid:
                        mtype = meal.get("type", "")
                        dlng, dlat = meal_offsets.get(mtype, (0.0004, -0.0003))
                        meal["location"] = {
                            "longitude": round(meal_ref["longitude"] + dlng, 6),
                            "latitude": round(meal_ref["latitude"] + dlat, 6),
                        }

            if not day.get("description"):
                attr_names = [a.get("name", "") for a in day.get("attractions", [])]
                day["description"] = "、".join(attr_names) + "之旅" if attr_names else f"第{day.get('day_index', 0) + 1}天行程"
            if not day.get("date"):
                day["date"] = plan_data.get("start_date", "")


# ── 文本提取（模块级函数）──────────────────────────────────

def extract_attractions_from_text(text: str) -> list:
    if not text:
        return []
    attractions = []

    patterns = [
        r'【([^】]+)】[：:]?\s*(.*?)(?=【|\n\n|\Z)',
        r'[*•]\s*([^：:]+)[：:]\s*(.*?)(?=[*•]|\n\n|\Z)',
        r'\d+[.、]\s*([^：:]+)[：:]\s*(.*?)(?=\d+[.、]|\n\n|\Z)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for name, desc in matches:
            name = name.strip()
            name = re.sub(r'^\d+\s*', '', name)
            name = re.sub(r'[\n\r]+', '', name)
            name = re.sub(r'^\d+[.、]\s*', '', name)
            name = re.sub(r'[（(][^）)]*[）)]', '', name).strip()
            desc = re.sub(r'\s+', ' ', desc.strip())[:200]

            location = None
            coord_match = re.search(r'坐标[：:]\s*([\d.]+)\s*[,，]\s*([\d.]+)', desc)
            if not coord_match:
                coord_match = re.search(r'(\d{2,3}\.\d+)\s*[,，]\s*(\d+\.\d+)', desc)
            if coord_match:
                lng, lat = float(coord_match.group(1)), float(coord_match.group(2))
                if 70 < lng < 140 and 15 < lat < 55:
                    location = {"longitude": lng, "latitude": lat}
                    desc = desc[:coord_match.start()].strip()

            if name and 2 <= len(name) <= 15 and not any(x in name for x in ['景点信息', '酒店信息', '天气信息', '推荐', '简介', '美食']):
                attr = {
                    "name": name, "address": "", "visit_duration": 90,
                    "description": desc, "ticket_price": 0, "category": "景点",
                }
                if location:
                    attr["location"] = location
                attractions.append(attr)
        if attractions:
            break

    return attractions[:8]


def extract_hotels_from_text(text: str) -> list:
    hotels = []
    if not text:
        return hotels

    blocks = re.split(r'(?=【)', text)
    for block in blocks:
        name_match = re.match(r'【([^】]+)】', block)
        if not name_match:
            continue
        name = name_match.group(1).strip()
        desc = block[name_match.end():].strip()

        location = None
        coord_match = re.search(r'坐标[：:]\s*([\d.]+)\s*[,，\s]+([\d.]+)', desc)
        if not coord_match:
            coord_match = re.search(r'\(\s*([\d.]+)\s*[,，]\s*([\d.]+)\s*\)', desc)
        if not coord_match:
            coord_match = re.search(r'(\d{2,3}\.\d+)\s*[,，]\s*(\d+\.\d+)', desc)
        if coord_match:
            try:
                lng, lat = float(coord_match.group(1)), float(coord_match.group(2))
                if 70 < lng < 140 and 15 < lat < 55:
                    location = {"longitude": lng, "latitude": lat}
            except (ValueError, IndexError):
                pass

        addr_match = re.search(r'地址[：:]\s*([^\|｜\n]+)', desc)
        address = addr_match.group(1).strip() if addr_match else ""

        rating_match = re.search(r'评分[：:]\s*([\d.]+)', desc)
        rating = float(rating_match.group(1)) if rating_match else None

        price_match = re.search(r'(?:参考价|价格|均价)[：:]\s*(\d+)', desc)
        price = int(price_match.group(1)) if price_match else None

        if name:
            hotels.append({
                "name": name, "address": address, "location": location,
                "rating": rating, "price": price,
            })

    return hotels[:6]
