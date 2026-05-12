from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import re

class Location(BaseModel):
    longitude: float = Field(..., description="经度", ge=-180, le=180)
    latitude: float = Field(..., description="纬度", ge=-90, le=90)

class Attraction(BaseModel):
    name: str = Field(..., description="景点名称")
    address: str = Field(..., description="地址")
    location: Location = Field(..., description="经纬度坐标")
    visit_duration: int = Field(..., description="建议游览时间(分钟)", gt=0)
    description: str = Field(..., description="景点描述")
    category: Optional[str] = Field(default="景点", description="景点类别")
    rating: Optional[float] = Field(default=None, ge=0, le=5, description="评分")
    image_url: Optional[str] = Field(default=None, description="图片URL")
    ticket_price: int = Field(default=0, ge=0, description="门票价格(元)")

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
    transportation: str = Field(..., description="交通方式")
    accommodation: str = Field(..., description="住宿安排")
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
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    days: int = Field(..., description="天数", gt=0, le=30)
    preferences: str = Field(default="历史文化", description="偏好")
    budget: str = Field(default="中等", description="预算")
    transportation: str = Field(default="公共交通", description="交通方式")
    accommodation: str = Field(default="经济型酒店", description="住宿类型")

    @field_validator("city")
    @classmethod
    def sanitize_city(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r'^[一-龥a-zA-Z\s\-·]+$', v):
            raise ValueError("城市名称包含非法字符")
        return v

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError("日期格式必须为 YYYY-MM-DD")
        return v

class TripPlan(BaseModel):
    city: str = Field(..., description="目的地城市")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    days: List[DayPlan] = Field(default_factory=list, description="每日行程")
    weather_info: List[WeatherInfo] = Field(default_factory=list, description="天气信息")
    overall_suggestions: str = Field(..., description="总体建议")
    budget: Optional[Budget] = Field(default=None, description="预算信息")

class TripEditRequest(BaseModel):
    trip_plan: TripPlan = Field(..., description="编辑后的行程计划")
