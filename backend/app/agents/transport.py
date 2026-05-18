"""
城际交通查询 + 距离估算
"""
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.agents.coordinates import CITY_COORDS, AIRPORT_STATION_COORDS, haversine_km

logger = logging.getLogger(__name__)


def get_real_transport(dep_city: str, arr_city: str, date: str):
    """智能查询交通方案：根据距离自动选择最优交通方式（高铁/飞机）。"""
    from ..models.schemas import TransportInfo
    from ..services.transport_search import transport_search

    dep_coords = CITY_COORDS.get(dep_city)
    arr_coords = CITY_COORDS.get(arr_city)
    dist_km = 0
    if dep_coords and arr_coords:
        dist_km = haversine_km(dep_coords[0], dep_coords[1], arr_coords[0], arr_coords[1])

    logger.info(f"  {dep_city}→{arr_city} 直线距离: {int(dist_km)}km")

    search_trains = True
    search_flights = True
    prefer_mode = "train"
    if dist_km < 300:
        search_flights = False
        prefer_mode = "train"
    elif dist_km < 1000:
        prefer_mode = "train"
    else:
        prefer_mode = "flight"

    trains, flights = [], []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}
        if search_trains:
            futures[executor.submit(transport_search.search_trains, dep_city, arr_city, date)] = "trains"
        if search_flights:
            futures[executor.submit(transport_search.search_flights, dep_city, arr_city, date)] = "flights"
        for future in as_completed(futures):
            try:
                result = future.result(timeout=15)
                if futures[future] == "trains":
                    trains = result
                else:
                    flights = result
            except Exception as e:
                logger.warning(f"  交通查询失败: {e}")

    best_train = _pick_best_train(trains)
    best_flight = _pick_best_flight(flights)

    if best_train and best_flight:
        if prefer_mode == "train":
            train_price = best_train["price"]
            flight_price = best_flight["price"]
            if train_price > 0 and flight_price > 0 and train_price < flight_price * 1.5:
                return _build_transport(dep_city, arr_city, "train", best_train)
            else:
                return _build_transport(dep_city, arr_city, "flight", best_flight)
        else:
            return _build_transport(dep_city, arr_city, "flight", best_flight)
    elif best_train:
        return _build_transport(dep_city, arr_city, "train", best_train)
    elif best_flight:
        return _build_transport(dep_city, arr_city, "flight", best_flight)
    else:
        logger.info(f"  实时查询无结果，使用距离估算")
        return estimate_transport(dep_city, arr_city)


def _pick_best_train(trains: list) -> Optional[dict]:
    if not trains:
        return None
    buyable = [t for t in trains if t.get("can_buy")]
    pool = buyable if buyable else trains
    fast = [t for t in pool if t["train_code"][0] in ("G", "D", "C")]
    if fast:
        valid = [t for t in fast if 20 < t.get("price", 0) < 2000]
        return valid[0] if valid else fast[0]
    return pool[0] if pool else None


def _pick_best_flight(flights: list) -> Optional[dict]:
    if not flights:
        return None
    valid = [f for f in flights if f.get("price", 0) > 0]
    return valid[0] if valid else flights[0] if flights else None


def _build_transport(dep_city: str, arr_city: str, mode: str, data: dict):
    from ..models.schemas import TransportInfo

    arr_stations = AIRPORT_STATION_COORDS.get(arr_city, {})

    if mode == "train":
        arr_lng = arr_stations.get("高铁", (None, None))[0] if "高铁" in arr_stations else None
        arr_lat = arr_stations.get("高铁", (None, None))[1] if "高铁" in arr_stations else None
        return TransportInfo(
            departure_city=dep_city,
            destination_city=arr_city,
            recommended_mode="高铁",
            estimated_cost=int(data["price"]),
            estimated_duration=data.get("duration", ""),
            notes=f"{data['train_code']} {data['departure_station']}→{data['arrival_station']} {data['departure_time']}出发",
            arrival_longitude=arr_lng,
            arrival_latitude=arr_lat,
        )
    else:
        arr_lng = arr_stations.get("飞机", (None, None))[0] if "飞机" in arr_stations else None
        arr_lat = arr_stations.get("飞机", (None, None))[1] if "飞机" in arr_stations else None
        return TransportInfo(
            departure_city=dep_city,
            destination_city=arr_city,
            recommended_mode="飞机",
            estimated_cost=data["price"],
            estimated_duration=data.get("duration", ""),
            notes=f"{data['airline']} {data['flight_no']} {data['departure_time']}出发",
            arrival_longitude=arr_lng,
            arrival_latitude=arr_lat,
        )


def estimate_transport(departure_city: str, destination_city: str):
    from ..models.schemas import TransportInfo

    if not departure_city or departure_city == destination_city:
        return TransportInfo(
            departure_city=departure_city, destination_city=destination_city,
            recommended_mode="本地出行", estimated_cost=0,
            estimated_duration="无需城际交通", notes="出发地与目的地相同",
        )

    dep = CITY_COORDS.get(departure_city)
    dest = CITY_COORDS.get(destination_city)

    if not dep or not dest:
        return TransportInfo(
            departure_city=departure_city, destination_city=destination_city,
            recommended_mode="建议查询12306或携程", estimated_cost=0,
            estimated_duration="", notes="未收录城市坐标，无法自动估算",
        )

    dist = haversine_km(dep[0], dep[1], dest[0], dest[1])

    if dist < 300:
        mode, cost, duration = "高铁", 150, "约1-1.5小时"
    elif dist < 800:
        mode, cost, duration = "高铁", 350, "约2-4小时"
    elif dist < 1500:
        mode, cost, duration = "高铁或飞机", 700, "约3-5小时"
    else:
        mode, cost, duration = "飞机", 1200, f"约{max(2, int(dist / 800))}小时"

    arr_lng, arr_lat = None, None
    dest_stations = AIRPORT_STATION_COORDS.get(destination_city, {})
    if "飞机" in mode and "飞机" in dest_stations:
        arr_lng, arr_lat = dest_stations["飞机"]
    elif "高铁" in mode and "高铁" in dest_stations:
        arr_lng, arr_lat = dest_stations["高铁"]
    elif "飞机" in dest_stations:
        arr_lng, arr_lat = dest_stations["飞机"]
    elif "高铁" in dest_stations:
        arr_lng, arr_lat = dest_stations["高铁"]

    return TransportInfo(
        departure_city=departure_city, destination_city=destination_city,
        recommended_mode=mode, estimated_cost=cost,
        estimated_duration=duration,
        notes=f"直线距离约{int(dist)}公里",
        arrival_longitude=arr_lng,
        arrival_latitude=arr_lat,
    )
