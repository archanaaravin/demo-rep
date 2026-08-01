from fastapi import APIRouter
from pydantic import BaseModel
import joblib
import pandas as pd

router = APIRouter(
    prefix="/predict",
    tags=["Prediction"]
)

# Load trained model
model = joblib.load("trained_model.pkl")

class PredictionInput(BaseModel):
    rainfall_mm: float
    temperature_c: float
    speed_limit: int
    lanes: int

@router.post("/")
def predict(data: PredictionInput):

    input_data = pd.DataFrame([{
        "rainfall_mm": data.rainfall_mm,
        "temperature_c": data.temperature_c,
        "speed_limit": data.speed_limit,
        "lanes": data.lanes
    }])

    prediction = model.predict(input_data)[0]

    severity = {
        0: "Minor",
        1: "Major",
        2: "Fatal"
    }

    return {
        "predicted_severity": severity[int(prediction)]
    }