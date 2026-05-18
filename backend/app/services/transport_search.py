"""
交通班次实时查询服务
- 12306 高铁/火车票查询
- 航班查询（Amadeus API / 备用估算）
"""
import re
import json
import logging
import time
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# 中国城市 IATA 代码（Amadeus 使用）
CITY_IATA = {
    "北京": "BJS", "上海": "SHA", "广州": "CAN", "深圳": "SZX",
    "成都": "CTU", "杭州": "HGH", "重庆": "CKG", "武汉": "WUH",
    "西安": "XIY", "南京": "NKG", "长沙": "CSX", "郑州": "CGO",
    "天津": "TSN", "苏州": "SZV", "厦门": "XMN", "昆明": "KMG",
    "大连": "DLC", "济南": "TNA", "青岛": "TAO", "沈阳": "SHE",
    "哈尔滨": "HRB", "长春": "CGQ", "合肥": "HFE", "福州": "FOC",
    "南昌": "KHN", "贵阳": "KWE", "南宁": "NNG", "兰州": "LHW",
    "太原": "TYN", "石家庄": "SJW", "乌鲁木齐": "URC", "拉萨": "LXA",
    "海口": "HAK", "三亚": "SYX", "丽江": "LJG", "大理": "DLU",
    "桂林": "KWL", "珠海": "ZUH", "宁波": "NGB", "温州": "WNZ",
    "呼和浩特": "HET", "银川": "INC", "西宁": "XNN",
}

# 12306 城市代码映射（部分常用）
STATION_CODES = {
    "北京": "BJP", "北京北": "VNP", "北京东": "BOP", "北京南": "VNP", "北京西": "BXP",
    "天津": "TJP", "天津西": "TXP", "天津南": "TIP",
    "上海": "SHH", "上海南": "SNH", "上海虹桥": "AOH",
    "广州": "GZQ", "广州南": "IZQ", "广州东": "GGQ",
    "深圳": "SZQ", "深圳北": "IOQ", "深圳西": "SBQ",
    "成都": "CDW", "成都东": "ICW", "成都南": "CNW",
    "重庆": "CQW", "重庆北": "CUW", "重庆西": "CXW",
    "杭州": "HZH", "杭州东": "HGH", "杭州南": "XHH",
    "武汉": "WHN", "武汉站": "WHN",
    "西安": "XAY", "西安北": "EAY",
    "南京": "NJH", "南京南": "NKH",
    "长沙": "CSQ", "长沙南": "CWQ",
    "郑州": "ZZF", "郑州东": "ZAF",
    "济南": "JNK", "济南西": "JGK",
    "沈阳": "SYT", "沈阳北": "SBT",
    "大连": "DLT", "大连北": "DFT",
    "哈尔滨": "HBB", "哈尔滨西": "VAB",
    "长春": "CCT", "长春西": "CRT",
    "苏州": "SZH", "苏州北": "OHH",
    "无锡": "WXH", "无锡东": "WGH",
    "合肥": "HFH", "合肥南": "ENH",
    "南昌": "NCG", "南昌西": "NXG",
    "福州": "FZS", "福州南": "FYS",
    "厦门": "XMS", "厦门北": "XKS",
    "贵阳": "GIW", "贵阳北": "KQW",
    "昆明": "KMM", "昆明南": "KOM",
    "兰州": "LZJ", "兰州西": "LAJ",
    "太原": "TYV", "太原南": "TNV",
    "石家庄": "SJP",
    "保定": "BDP", "唐山": "TSP", "秦皇岛": "QTP",
    "徐州": "XCH", "徐州东": "UUH",
    "潍坊": "WFK", "淄博": "ZBK",
    "洛阳": "LYF", "洛阳龙门": "LLF",
    "绵阳": "MYW", "德阳": "DYW",
    "遵义": "ZYW", "遵义南": "RNW",
    "桂林": "GLZ", "桂林北": "GBZ",
    "三亚": "SEQ", "海口": "VUQ",
    "呼和浩特": "HHC", "包头": "BTC",
    "银川": "YIJ", "西宁": "XNO",
    "乌鲁木齐": "WMR", "拉萨": "LSO",
}

# 城市名到拼音（用于12306搜索）
CITY_PINYIN = {
    "北京": "beijing", "天津": "tianjin", "上海": "shanghai", "广州": "guangzhou",
    "深圳": "shenzhen", "成都": "chengdu", "重庆": "chongqing", "杭州": "hangzhou",
    "武汉": "wuhan", "西安": "xian", "南京": "nanjing", "长沙": "changsha",
    "郑州": "zhengzhou", "济南": "jinan", "沈阳": "shenyang", "大连": "dalian",
    "哈尔滨": "haerbin", "长春": "changchun", "苏州": "suzhou", "无锡": "wuxi",
    "合肥": "hefei", "南昌": "nanchang", "福州": "fuzhou", "厦门": "xiamen",
    "贵阳": "guiyang", "昆明": "kunming", "兰州": "lanzhou", "太原": "taiyuan",
    "石家庄": "shijiazhuang", "海口": "haikou", "三亚": "sanya",
    "呼和浩特": "huhehaote", "银川": "yinchuan", "西宁": "xining",
    "乌鲁木齐": "wulumuqi", "拉萨": "lasa",
}


def _date_to_12306(date_str: str) -> str:
    """YYYY-MM-DD → YYMMDD (12306日期格式)"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%y%m%d")
    except ValueError:
        return ""


def _parse_train_number(name: str) -> str:
    """从列车名中提取车次号"""
    m = re.search(r'([GDCZKLT]\d{1,4})', name.upper())
    return m.group(1) if m else name


class TransportSearchService:
    """交通班次实时查询"""

    def __init__(self):
        self._cache: Dict[str, tuple] = {}
        self._CACHE_TTL = 1800  # 30分钟缓存
        self._amadeus_token: Optional[str] = None
        self._amadeus_token_expires: float = 0

    def _get_amadeus_token(self) -> Optional[str]:
        """获取 Amadeus API access token（OAuth2 client_credentials）"""
        api_key = os.environ.get("AMADEUS_API_KEY", "")
        api_secret = os.environ.get("AMADEUS_API_SECRET", "")
        if not api_key or not api_secret or api_key.startswith("your_"):
            return None

        if self._amadeus_token and time.time() < self._amadeus_token_expires:
            return self._amadeus_token

        try:
            resp = httpx.post(
                "https://api.amadeus.com/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": api_key,
                    "client_secret": api_secret,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            self._amadeus_token = data["access_token"]
            self._amadeus_token_expires = time.time() + data.get("expires_in", 1799) - 60
            logger.info("Amadeus token 获取成功")
            return self._amadeus_token
        except Exception as e:
            logger.warning(f"Amadeus token 获取失败: {e}")
            return None

    def _search_flights_amadeus(self, dep_iata: str, arr_iata: str, date: str) -> List[Dict]:
        """通过 Amadeus API 查询真实航班"""
        token = self._get_amadeus_token()
        if not token:
            return []

        try:
            resp = httpx.get(
                "https://api.amadeus.com/v2/shopping/flight-offers",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "originLocationCode": dep_iata,
                    "destinationLocationCode": arr_iata,
                    "departureDate": date,
                    "adults": 1,
                    "max": 10,
                    "currencyCode": "CNY",
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return self._parse_amadeus_response(data)
        except Exception as e:
            logger.warning(f"Amadeus 航班查询失败: {e}")
            return []

    def _parse_amadeus_response(self, data: dict) -> List[Dict]:
        """解析 Amadeus API 响应为统一格式"""
        results = []
        for offer in data.get("data", []):
            try:
                itin = offer.get("itineraries", [{}])[0]
                segments = itin.get("segments", [])
                if not segments:
                    continue

                first_seg = segments[0]
                last_seg = segments[-1]

                dep_time_raw = first_seg.get("departure", {}).get("at", "")
                arr_time_raw = last_seg.get("arrival", {}).get("at", "")

                dep_time = dep_time_raw[11:16] if len(dep_time_raw) >= 16 else ""
                arr_time = arr_time_raw[11:16] if len(arr_time_raw) >= 16 else ""

                carrier_code = first_seg.get("carrierCode", "")
                flight_num = first_seg.get("number", "")
                airline_name = self._resolve_airline(carrier_code)

                dep_airport = first_seg.get("departure", {}).get("iataCode", "")
                arr_airport = last_seg.get("arrival", {}).get("iataCode", "")

                duration_str = itin.get("duration", "")
                dur_match = re.match(r'PT(\d+)H(\d+)M', duration_str)
                duration = f"{dur_match.group(1)}h{dur_match.group(2)}m" if dur_match else ""

                price = int(offer.get("price", {}).get("total", 0))

                results.append({
                    "flight_no": f"{carrier_code}{flight_num}",
                    "airline": airline_name,
                    "departure_city": "",
                    "arrival_city": "",
                    "departure_airport": dep_airport,
                    "arrival_airport": arr_airport,
                    "departure_time": dep_time,
                    "arrival_time": arr_time,
                    "duration": duration,
                    "price": price,
                    "date": "",
                    "can_buy": True,
                    "is_estimate": False,
                })
            except Exception as e:
                logger.debug(f"解析 Amadeus 航班失败: {e}")
                continue

        return results

    @staticmethod
    def _resolve_airline(code: str) -> str:
        """将航司代码解析为中文名"""
        airlines = {
            "CA": "中国国航", "MU": "东方航空", "CZ": "南方航空",
            "HU": "海南航空", "ZH": "深圳航空", "3U": "四川航空",
            "MF": "厦门航空", "FM": "上海航空", "SC": "山东航空",
            "GS": "天津航空", "JD": "首都航空", "EU": "成都航空",
            "HO": "吉祥航空", "KN": "联航", "9C": "春秋航空",
            "G8": "西藏航空", "NS": "河北航空", "GX": "北部湾航空",
        }
        return airlines.get(code, code)

    def _get_station_code(self, city: str) -> Optional[str]:
        """获取城市对应的12306车站代码"""
        # 直接匹配
        if city in STATION_CODES:
            return STATION_CODES[city]
        # 模糊匹配（如"北京南" → "VNP"）
        for name, code in STATION_CODES.items():
            if city in name or name in city:
                return code
        return None

    def search_trains(self, departure_city: str, arrival_city: str, date: str) -> List[Dict[str, Any]]:
        """
        查询12306高铁/火车班次。
        返回: [{train_no, train_code, departure_station, arrival_station, departure_time, arrival_time,
                duration, price, can_buy, date}]
        """
        cache_key = f"train|{departure_city}|{arrival_city}|{date}"
        # L1: 内存缓存 (30min)
        if cache_key in self._cache:
            cached_at, cached_data = self._cache[cache_key]
            if time.time() - cached_at < self._CACHE_TTL:
                return cached_data

        # L2: 数据库缓存 (24h)
        try:
            from app.database import get_transport_cache
            db_cached = get_transport_cache(cache_key)
            if db_cached is not None:
                self._cache[cache_key] = (time.time(), db_cached)
                return db_cached
        except Exception:
            pass

        dep_code = self._get_station_code(departure_city)
        arr_code = self._get_station_code(arrival_city)

        if not dep_code or not arr_code:
            logger.warning(f"未找到车站代码: {departure_city}→{dep_code}, {arrival_city}→{arr_code}")
            return []

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
            }

            # 必须先访问 init 页面获取 session cookie
            with httpx.Client(verify=False, trust_env=False, follow_redirects=True, timeout=10.0) as client:
                client.get("https://kyfw.12306.cn/otn/leftTicket/init", headers=headers)

                # 查询列车
                url = "https://kyfw.12306.cn/otn/leftTicket/queryZ"
                params = {
                    "leftTicketDTO.train_date": date,
                    "leftTicketDTO.from_station": dep_code,
                    "leftTicketDTO.to_station": arr_code,
                    "purpose_codes": "ADULT",
                }
                resp = client.get(url, params=params, headers={
                    **headers, "X-Requested-With": "XMLHttpRequest"
                })
                data = resp.json()

            results = []
            if data.get("httpstatus") == 200 and data.get("data", {}).get("result"):
                station_map = self._parse_station_map(data["data"])
                for item in data["data"]["result"]:
                    train = self._parse_train_item(item, station_map, departure_city, arrival_city, date)
                    if train:
                        results.append(train)

            results.sort(key=lambda x: x.get("departure_time", ""))
            self._cache[cache_key] = (time.time(), results)
            # 写入 DB 缓存
            try:
                from app.database import save_transport_cache
                save_transport_cache(cache_key, results)
            except Exception:
                pass
            logger.info(f"12306查询成功: {departure_city}→{arrival_city} {date}, {len(results)}趟列车")
            return results

        except Exception as e:
            logger.error(f"12306查询异常: {e}")
            return []

    def _parse_station_map(self, data: dict) -> dict:
        """解析12306车站名映射"""
        station_map = {}
        for key in ("map", "station_map"):
            raw = data.get(key, "")
            if isinstance(raw, dict):
                station_map = raw
                break
            elif isinstance(raw, str) and raw:
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        station_map = parsed
                        break
                except (json.JSONDecodeError, TypeError):
                    pass
        return station_map

    def _parse_train_item(self, item: str, station_map: dict,
                          dep_city: str, arr_city: str, date: str) -> Optional[Dict]:
        """解析单条12306列车数据"""
        try:
            fields = item.split("|")
            if len(fields) < 30:
                return None

            secret = fields[0]  # 加密串
            train_no = fields[2]  # 列车编号
            train_code = fields[3]  # 车次号（G1234）
            start_station_code = fields[4]
            end_station_code = fields[5]
            dep_station_code = fields[6]
            arr_station_code = fields[7]
            dep_time = fields[8]  # 出发时间
            arr_time = fields[9]  # 到达时间
            duration = fields[10]  # 历时
            can_buy = fields[11]  # Y:可购 N:不可购

            # 解析票价 — field[54] 编码格式: 9{xxx}M{二等座}O{一等座}W{商务座}
            prices = {}
            f54 = fields[54] if len(fields) > 54 else ""
            if f54:
                # 匹配座位代码+价格: M0096 → 二等座 ¥96
                seat_price_map = {"M": "二等座", "O": "一等座", "W": "商务座", "S": "特等座", "Y": "软卧", "Z": "硬卧"}
                for match in re.finditer(r'([MOWXSYZ])(\d{3,})', f54):
                    seat_code = match.group(1)
                    raw_price = int(match.group(2))
                    # 价格通常除以10得到实际元价，但如果>1000则可能是整数
                    price = raw_price if raw_price > 100 else raw_price
                    if seat_code in seat_price_map and price > 0:
                        prices[seat_price_map[seat_code]] = price

            # 选择最优价格（二等座 > 一等座 > 硬座）
            best_price = 0
            for seat in ["二等座", "一等座", "商务座", "硬座", "硬卧"]:
                if seat in prices:
                    best_price = prices[seat]
                    break

            dep_station = station_map.get(dep_station_code, dep_station_code)
            arr_station = station_map.get(arr_station_code, arr_station_code)

            return {
                "train_no": train_no,
                "train_code": train_code,
                "departure_station": dep_station,
                "arrival_station": arr_station,
                "departure_time": dep_time,
                "arrival_time": arr_time,
                "duration": duration,
                "can_buy": can_buy == "Y",
                "price": best_price,
                "prices": prices,
                "date": date,
                "from_city": dep_city,
                "to_city": arr_city,
            }
        except Exception as e:
            logger.debug(f"解析列车数据异常: {e}")
            return None

    def search_flights(self, departure_city: str, arrival_city: str, date: str) -> List[Dict[str, Any]]:
        """
        查询航班信息。
        返回: [{flight_no, airline, departure_airport, arrival_airport,
                departure_time, arrival_time, duration, price, date}]
        """
        cache_key = f"flight|{departure_city}|{arrival_city}|{date}"
        # L1: 内存缓存 (30min)
        if cache_key in self._cache:
            cached_at, cached_data = self._cache[cache_key]
            if time.time() - cached_at < self._CACHE_TTL:
                return cached_data

        # L2: 数据库缓存 (24h)
        try:
            from app.database import get_transport_cache
            db_cached = get_transport_cache(cache_key)
            if db_cached is not None:
                self._cache[cache_key] = (time.time(), db_cached)
                return db_cached
        except Exception:
            pass

        results = self._search_flights_via_web(departure_city, arrival_city, date)

        self._cache[cache_key] = (time.time(), results)
        # 写入 DB 缓存
        try:
            from app.database import save_transport_cache
            save_transport_cache(cache_key, results)
        except Exception:
            pass
        return results

    def _search_flights_via_web(self, dep_city: str, arr_city: str, date: str) -> List[Dict]:
        """查询航班：Amadeus 真实API → 本地估算兜底"""
        dep_iata = CITY_IATA.get(dep_city, "")
        arr_iata = CITY_IATA.get(arr_city, "")

        if dep_iata and arr_iata:
            results = self._search_flights_amadeus(dep_iata, arr_iata, date)
            if results:
                logger.info(f"Amadeus 返回 {len(results)} 个航班")
                return results

        logger.info(f"Amadeus 无结果/未配置，使用本地估算")
        return self._generate_flight_estimate(dep_city, arr_city, date)

    def _generate_flight_estimate(self, dep_city: str, arr_city: str, date: str) -> List[Dict]:
        """
        基于已知航线数据生成航班估算。
        注意：这是基于常见航线的估算数据，实际使用时应替换为真实API。
        """
        # 常见航线基础数据（航司、大致时间、大致价格）
        KNOWN_ROUTES = {
            ("北京", "上海"): [
                {"airline": "中国国航", "flight_prefix": "CA", "duration": "2h15m", "base_price": 800},
                {"airline": "东方航空", "flight_prefix": "MU", "duration": "2h20m", "base_price": 750},
                {"airline": "南方航空", "flight_prefix": "CZ", "duration": "2h25m", "base_price": 780},
                {"airline": "海南航空", "flight_prefix": "HU", "duration": "2h15m", "base_price": 720},
            ],
            ("北京", "广州"): [
                {"airline": "中国国航", "flight_prefix": "CA", "duration": "3h10m", "base_price": 1200},
                {"airline": "南方航空", "flight_prefix": "CZ", "duration": "3h05m", "base_price": 1100},
                {"airline": "东方航空", "flight_prefix": "MU", "duration": "3h15m", "base_price": 1150},
            ],
            ("上海", "广州"): [
                {"airline": "南方航空", "flight_prefix": "CZ", "duration": "2h35m", "base_price": 900},
                {"airline": "东方航空", "flight_prefix": "MU", "duration": "2h40m", "base_price": 950},
                {"airline": "中国国航", "flight_prefix": "CA", "duration": "2h45m", "base_price": 920},
            ],
            ("北京", "深圳"): [
                {"airline": "中国国航", "flight_prefix": "CA", "duration": "3h10m", "base_price": 1250},
                {"airline": "深圳航空", "flight_prefix": "ZH", "duration": "3h05m", "base_price": 1100},
                {"airline": "南方航空", "flight_prefix": "CZ", "duration": "3h15m", "base_price": 1180},
            ],
            ("北京", "成都"): [
                {"airline": "中国国航", "flight_prefix": "CA", "duration": "3h00m", "base_price": 1100},
                {"airline": "四川航空", "flight_prefix": "3U", "duration": "3h05m", "base_price": 950},
                {"airline": "东方航空", "flight_prefix": "MU", "duration": "3h10m", "base_price": 1050},
            ],
            ("上海", "成都"): [
                {"airline": "东方航空", "flight_prefix": "MU", "duration": "3h10m", "base_price": 1000},
                {"airline": "四川航空", "flight_prefix": "3U", "duration": "3h05m", "base_price": 900},
                {"airline": "中国国航", "flight_prefix": "CA", "duration": "3h15m", "base_price": 1050},
            ],
            ("广州", "成都"): [
                {"airline": "南方航空", "flight_prefix": "CZ", "duration": "2h30m", "base_price": 850},
                {"airline": "四川航空", "flight_prefix": "3U", "duration": "2h35m", "base_price": 800},
            ],
            ("北京", "杭州"): [
                {"airline": "中国国航", "flight_prefix": "CA", "duration": "2h15m", "base_price": 800},
                {"airline": "东方航空", "flight_prefix": "MU", "duration": "2h20m", "base_price": 780},
            ],
            ("上海", "重庆"): [
                {"airline": "东方航空", "flight_prefix": "MU", "duration": "2h50m", "base_price": 900},
                {"airline": "四川航空", "flight_prefix": "3U", "duration": "2h45m", "base_price": 850},
            ],
            ("北京", "西安"): [
                {"airline": "中国国航", "flight_prefix": "CA", "duration": "2h10m", "base_price": 750},
                {"airline": "东方航空", "flight_prefix": "MU", "duration": "2h15m", "base_price": 700},
            ],
            ("北京", "昆明"): [
                {"airline": "中国国航", "flight_prefix": "CA", "duration": "3h30m", "base_price": 1300},
                {"airline": "东方航空", "flight_prefix": "MU", "duration": "3h35m", "base_price": 1200},
            ],
            ("上海", "三亚"): [
                {"airline": "中国国航", "flight_prefix": "CA", "duration": "3h00m", "base_price": 1100},
                {"airline": "南方航空", "flight_prefix": "CZ", "duration": "3h05m", "base_price": 1000},
            ],
        }

        route_key = (dep_city, arr_city)
        route_data = KNOWN_ROUTES.get(route_key, [])
        if not route_data:
            return []

        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return []

        results = []
        import random
        random.seed(hash(f"{dep_city}{arr_city}{date}") % 10000)

        for i, route in enumerate(route_data):
            # 生成合理的航班号
            flight_num = f"{route['flight_prefix']}{random.randint(1000, 9999)}"

            # 生成出发时间（6:00-21:00之间）
            hour = 6 + i * 3 + random.randint(0, 2)
            minute = random.choice([0, 10, 15, 20, 30, 40, 45, 50])
            dep_time = f"{hour:02d}:{minute:02d}"

            # 解析时长
            dur_match = re.match(r'(\d+)h(\d+)m', route["duration"])
            if dur_match:
                dur_hours = int(dur_match.group(1))
                dur_mins = int(dur_match.group(2))
            else:
                dur_hours, dur_mins = 2, 30

            # 计算到达时间
            dep_dt = dt.replace(hour=hour, minute=minute)
            arr_dt = dep_dt + timedelta(hours=dur_hours, minutes=dur_mins)
            arr_time = arr_dt.strftime("%H:%M")

            # 价格浮动 ±15%
            price = int(route["base_price"] * (1 + random.uniform(-0.15, 0.15)))

            results.append({
                "flight_no": flight_num,
                "airline": route["airline"],
                "departure_city": dep_city,
                "arrival_city": arr_city,
                "departure_time": dep_time,
                "arrival_time": arr_time,
                "duration": route["duration"],
                "price": price,
                "date": date,
                "is_estimate": True,  # 标记为估算数据
            })

        return results


# 单例
transport_search = TransportSearchService()
