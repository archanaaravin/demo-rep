import joblib
import os
# Path to model folder
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model")

# -----------------------------
# Load AI Model
# -----------------------------

model = joblib.load(os.path.join(MODEL_PATH, "accident_model.pkl"))
# -----------------------------
# Load Encoders
# -----------------------------

weather_encoder = joblib.load(os.path.join(MODEL_PATH, "weather_encoder.pkl"))

traffic_encoder = joblib.load(os.path.join(MODEL_PATH, "traffic_encoder.pkl"))

road_encoder = joblib.load(os.path.join(MODEL_PATH, "road_encoder.pkl"))

time_encoder = joblib.load(os.path.join(MODEL_PATH, "time_encoder.pkl"))

risk_encoder = joblib.load(os.path.join(MODEL_PATH, "risk_encoder.pkl"))
print("✅ Predictor loaded successfully!")

# -----------------------------
# Prediction Function
# -----------------------------

def predict_accident(weather, traffic, road, speed, time):
    weather = weather_encoder.transform([weather])[0]
    traffic = traffic_encoder.transform([traffic])[0]
    road = road_encoder.transform([road])[0]
    time = time_encoder.transform([time])[0]
    prediction = model.predict([[weather, traffic, road, speed, time]])

    prediction = risk_encoder.inverse_transform(prediction)

    return prediction[0]
# -----------------------------
# Test the function
# -----------------------------
