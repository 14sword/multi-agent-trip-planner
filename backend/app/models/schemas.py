from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import re

class Location(BaseModel):
    longitude: float = Field(..., description="经度", ge=-180, le=180)
    latitude: float = Field(..., description="纬度", ge=-90, le=90)

class Attraction(BaseModel):
    name: str = Field(..., description="景点名称")
    address: str = Field(default="", description="地址")
    location: Optional[Location] = Field(default=None, description="经纬度坐标")
    visit_duration: int = Field(default=60, description="建议游览时间(分钟)", gt=0)
    description: str = Field(default="", description="景点描述")
    category: Optional[str] = Field(default="景点", description="景点类别")
    rating: Optional[float] = Field(default=None, ge=0, le=5, description="评分")
    image_url: Optional[str] = Field(default=None, description="图片URL")
    ticket_price: int = Field(default=0, ge=0, description="门票价格(元)")

    @field_validator("visit_duration", mode="before")
    @classmethod
    def parse_visit_duration(cls, v):
        if isinstance(v, str):
            m = re.search(r'(\d+)', v)
            return int(m.group(1)) if m else 60
        return v

    @field_validator("ticket_price", mode="before")
    @classmethod
    def parse_ticket_price(cls, v):
        if isinstance(v, str):
            if "免费" in v:
                return 0
            m = re.search(r'(\d+)', v)
            return int(m.group(1)) if m else 0
        return v

class Meal(BaseModel):
    type: str = Field(..., description="餐饮类型：breakfast/lunch/dinner/snack")
    name: str = Field(..., description="餐饮名称")
    address: Optional[str] = Field(default=None, description="地址")
    location: Optional[Location] = Field(default=None, description="经纬度坐标")
    description: Optional[str] = Field(default=None, description="描述")
    estimated_cost: int = Field(default=0, ge=0, description="预估费用(元)")

class Hotel(BaseModel):
    name: str = Field(..., description="酒店名称")
    address: str = Field(default="", description="酒店地址")
    location: Optional[Location] = Field(default=None, description="酒店位置")
    price_range: str = Field(default="", description="价格范围")
    rating: Optional[float] = Field(default=None, ge=0, le=5, description="评分")
    distance: str = Field(default="", description="距离景点距离")
    type: str = Field(default="", description="酒店类型")
    estimated_cost: int = Field(default=0, ge=0, description="预估费用(元/晚)")

class TransportInfo(BaseModel):
    departure_city: str = Field(default="", description="出发城市")
    destination_city: str = Field(default="", description="目的地城市")
    recommended_mode: str = Field(default="", description="推荐交通方式：飞机/高铁/自驾")
    estimated_cost: int = Field(default=0, ge=0, description="预估交通费用(元)")
    estimated_duration: str = Field(default="", description="预估耗时")
    notes: str = Field(default="", description="交通建议备注")
    arrival_longitude: Optional[float] = Field(default=None, description="到达地点经度")
    arrival_latitude: Optional[float] = Field(default=None, description="到达地点纬度")

class Budget(BaseModel):
    total_attractions: int = Field(default=0, description="景点门票总费用")
    total_hotels: int = Field(default=0, description="酒店总费用")
    total_meals: int = Field(default=0, description="餐饮总费用")
    total_transportation: int = Field(default=0, description="交通总费用")
    total: int = Field(default=0, description="总费用")

class DayPlan(BaseModel):
    date: str = Field(..., description="日期")
    day_index: int = Field(..., description="第几天(从0开始)")
    description: str = Field(..., description="当日行程描述")
    transportation: str = Field(default="公共交通", description="交通方式")
    accommodation: str = Field(default="", description="住宿安排")
    hotel: Optional[Hotel] = Field(default=None, description="酒店信息")
    attractions: List[Attraction] = Field(default_factory=list, description="景点列表")
    meals: List[Meal] = Field(default_factory=list, description="餐饮安排")

class WeatherInfo(BaseModel):
    date: str = Field(..., description="日期")
    day_weather: str = Field(..., description="白天天气")
    night_weather: str = Field(..., description="夜间天气")
    day_temp: int = Field(..., description="白天温度(摄氏度)")
    night_temp: int = Field(..., description="夜间温度(摄氏度)")
    wind_direction: str = Field(..., description="风向")
    wind_power: str = Field(..., description="风力")

    @field_validator("day_temp", "night_temp", mode="before")
    @classmethod
    def parse_temp(cls, v):
        if isinstance(v, str):
            v = v.replace('°C', '').replace('℃', '').replace('°', '').strip()
            try:
                return int(v)
            except ValueError:
                return 0
        return v

class TripPlanRequest(BaseModel):
    city: str = Field(..., description="目的地城市", min_length=1, max_length=50)
    departure_city: str = Field(default="", description="出发城市", max_length=50)
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    days: int = Field(..., description="天数", gt=0, le=30)
    travelers: int = Field(default=1, description="出行人数", gt=0, le=20)
    preferences: list[str] = Field(default=["历史文化"], description="偏好标签（多选）")
    extra_info: str = Field(default="", description="补充信息（选填）")
    budget: str = Field(default="中等", description="预算")
    transportation: str = Field(default="公共交通", description="交通方式")
    accommodation: str = Field(default="经济型酒店", description="住宿类型")

    @property
    def preferences_text(self) -> str:
        """将偏好列表合并为文本，供下游 prompt 使用。"""
        parts = list(self.preferences)
        if self.extra_info:
            parts.append(self.extra_info)
        return "、".join(parts) if parts else "历史文化"

    @field_validator("city")
    @classmethod
    def sanitize_city(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r'^[一-龥a-zA-Z\s\-·]+$', v):
            raise ValueError("城市名称包含非法字符")
        return v

    @field_validator("departure_city")
    @classmethod
    def sanitize_departure_city(cls, v: str) -> str:
        v = v.strip()
        if v and not re.match(r'^[一-龥a-zA-Z\s\-·]+$', v):
            raise ValueError("出发城市名称包含非法字符")
        return v

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError("日期格式必须为 YYYY-MM-DD")
        return v

class TripPlan(BaseModel):
    id: Optional[str] = Field(default=None, description="行程ID")
    city: str = Field(..., description="目的地城市")
    departure_city: Optional[str] = Field(default=None, description="出发城市")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    days: List[DayPlan] = Field(default_factory=list, description="每日行程")
    weather_info: List[WeatherInfo] = Field(default_factory=list, description="天气信息")
    overall_suggestions: str = Field(..., description="总体建议")
    budget: Optional[Budget] = Field(default=None, description="预算信息")
    transport_info: Optional[TransportInfo] = Field(default=None, description="城际交通信息")
    share_token: Optional[str] = Field(default=None, description="分享令牌")
    cps_links: Optional[dict] = Field(default=None, description="CPS联盟链接")

    @field_validator("days", "weather_info", mode="before")
    @classmethod
    def parse_json_list(cls, v):
        if isinstance(v, str):
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
        return v

class TripEditRequest(BaseModel):
    trip_plan: TripPlan = Field(..., description="编辑后的行程计划")
