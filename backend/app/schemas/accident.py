from pydantic import BaseModel
from datetime import date, time

class AccidentResponse(BaseModel):
    accident_id: int
    accident_date: date
    accident_time: time
    latitude: float
    longitude: float
    road_name: str
    junction: str
    weather: str
    rainfall_mm: float
    temperature_c: float
    visibility: str
    traffic_density: str
    road_type: str
    speed_limit: int
    lanes: int
    vehicle_1: str
    vehicle_2: str
    cause: str
    severity: str
    casualties: int

    class Config:
        from_attributes = True