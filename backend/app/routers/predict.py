from pathlib import Path
import sys
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai.predictor import predict_accident

router = APIRouter(
    prefix='/predict',
    tags=['Prediction']
)


class PredictionInput(BaseModel):
    weather: Optional[str] = None
    traffic: Optional[str] = None
    road: Optional[str] = None
    speed: Optional[float] = None
    time: Optional[str] = None
    road_type: Optional[str] = None
    road_condition: Optional[str] = None
    traffic_density: Optional[str] = None
    average_traffic_speed: Optional[float] = None
    temperature: Optional[float] = None
    lanes: Optional[int] = None


@router.post('/')
def predict(data: PredictionInput):
    result = predict_accident(
        weather=data.weather,
        traffic=data.traffic,
        road=data.road,
        speed=data.speed,
        time=data.time,
        road_type=data.road_type,
        road_condition=data.road_condition,
        traffic_density=data.traffic_density,
        average_traffic_speed=data.average_traffic_speed,
        temperature=data.temperature,
        lanes=data.lanes,
    )

    return {
        'prediction': result,
        'input': data.dict(),
    }
