"""
天气服务 — 高德REST API + wttr.in 备用。
"""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

_CITY_EN = {
    "北京": "Beijing", "上海": "Shanghai", "广州": "Guangzhou", "深圳": "Shenzhen",
    "成都": "Chengdu", "杭州": "Hangzhou", "武汉": "Wuhan", "西安": "Xian",
    "重庆": "Chongqing", "南京": "Nanjing", "厦门": "Xiamen", "苏州": "Suzhou",
    "昆明": "Kunming", "丽江": "Lijiang", "大理": "Dali", "桂林": "Guilin",
    "三亚": "Sanya", "青岛": "Qingdao", "长沙": "Changsha", "哈尔滨": "Harbin",
    "拉萨": "Lhasa", "兰州": "Lanzhou", "福州": "Fuzhou", "济南": "Jinan",
    "太原": "Taiyuan", "沈阳": "Shenyang", "大连": "Dalian", "无锡": "Wuxi",
    "宁波": "Ningbo", "温州": "Wenzhou", "珠海": "Zhuhai", "海口": "Haikou",
    "贵阳": "Guiyang", "南昌": "Nanchang", "合肥": "Hefei", "郑州": "Zhengzhou",
    "长春": "Changchun", "呼和浩特": "Hohhot", "银川": "Yinchuan",
    "西宁": "Xining", "乌鲁木齐": "Urumqi", "徐州": "Xuzhou", "泉州": "Quanzhou",
    "漳州": "Zhangzhou", "黄山": "Huangshan", "洛阳": "Luoyang", "开封": "Kaifeng",
    "凤凰": "Fenghuang", "平遥": "Pingyao",
}


def get_weather(city: str) -> list[dict]:
    """获取城市天气预报。优先高德API，失败用wttr.in。"""
    result = _get_weather_amap(city)
    if result:
        return result
    return _get_weather_wttr(city)


def _get_weather_amap(city: str) -> list[dict]:
    api_key = settings.AMAP_API_KEY
    if not api_key:
        return []
    try:
        resp = httpx.get(
            "https://restapi.amap.com/v3/weather/weatherInfo",
            params={"key": api_key, "city": city, "extensions": "all"},
            timeout=10.0,
            trust_env=False,
        )
        data = resp.json()
        if data.get("status") != "1":
            return []
        result = []
        for forecast in data.get("forecasts", []):
            for cast in forecast.get("casts", []):
                result.append({
                    "date": cast.get("date", ""),
                    "day_weather": cast.get("dayweather", ""),
                    "night_weather": cast.get("nightweather", ""),
                    "day_temp": int(cast.get("daytemp", 0)),
                    "night_temp": int(cast.get("nighttemp", 0)),
                    "wind_direction": cast.get("daywind", ""),
                    "wind_power": cast.get("daypower", ""),
                })
        return result
    except Exception as e:
        logger.debug(f"高德天气API失败: {e}")
        return []


def _get_weather_wttr(city: str) -> list[dict]:
    """wttr.in 免费天气API，无需key。"""
    en_city = _CITY_EN.get(city, city)
    try:
        resp = httpx.get(
            f"https://wttr.in/{en_city}?format=j1",
            timeout=10.0,
            trust_env=False,
        )
        data = resp.json()
        result = []
        for day in data.get("weather", []):
            hourly = day.get("hourly", [])
            day_w = hourly[4].get("weatherDesc", [{}])[0].get("value", "晴") if len(hourly) > 4 else "晴"
            night_w = hourly[7].get("weatherDesc", [{}])[0].get("value", "晴") if len(hourly) > 7 else "晴"
            result.append({
                "date": day.get("date", ""),
                "day_weather": _cn_weather(day_w),
                "night_weather": _cn_weather(night_w),
                "day_temp": int(day.get("maxtempC", 25)),
                "night_temp": int(day.get("mintempC", 18)),
                "wind_direction": hourly[4].get("winddir16Point", "") if len(hourly) > 4 else "",
                "wind_power": _cn_wind(hourly[4].get("windspeedKmph", "10")) if len(hourly) > 4 else "",
            })
        return result
    except Exception as e:
        logger.warning(f"wttr.in天气查询失败: {e}")
        return []


def _cn_weather(w: str) -> str:
    w_lower = w.strip().lower()
    m = {
        "sunny": "晴", "clear": "晴", "partly cloudy": "多云",
        "cloudy": "阴", "overcast": "阴",
        "patchy rain possible": "小雨", "patchy rain nearby": "小雨",
        "patchy light drizzle": "小雨", "patchy light rain": "小雨",
        "light rain": "小雨", "moderate rain": "中雨", "heavy rain": "大雨",
        "light drizzle": "毛毛雨", "mist": "薄雾", "fog": "雾",
        "thundery outbreaks possible": "雷阵雨",
        "light rain shower": "阵雨", "moderate or heavy rain shower": "大阵雨",
        "light snow": "小雪", "moderate snow": "中雪", "heavy snow": "大雪",
        "blizzard": "暴雪", "freezing fog": "冻雾",
        "rain": "雨", "snow": "雪", "thunderstorm": "雷阵雨",
        "light freezing rain": "冻雨", "patchy snow possible": "小雪",
        "patchy freezing drizzle possible": "冻雨",
        "ice pellets": "冰雹", "light sleet": "雨夹雪",
        "moderate or heavy sleet": "大雨夹雪",
    }
    return m.get(w_lower, w)


def _cn_wind(kmph: str) -> str:
    try:
        s = int(kmph)
    except (ValueError, TypeError):
        return ""
    if s < 12: return "2级"
    if s < 20: return "3级"
    if s < 29: return "4级"
    if s < 39: return "5级"
    return "6级"


def get_weather_str(city: str) -> str:
    items = get_weather(city)
    if not items:
        return f"暂无{city}天气数据"
    lines = []
    for item in items:
        lines.append(
            f"{item['date']}: 白天{item['day_weather']} {item['day_temp']}°C | "
            f"夜间{item['night_weather']} {item['night_temp']}°C | "
            f"风向{item['wind_direction']} 风力{item['wind_power']}"
        )
    return "\n".join(lines)
