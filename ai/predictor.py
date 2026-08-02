import joblib
from pathlib import Path
import pandas as pd
from sklearn.preprocessing import LabelEncoder

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
DATASET_PATH = BASE_DIR / "dataset" / "accidents_v2.csv"

MODEL_PATH = MODEL_DIR / "accident_model.pkl"
LABEL_ENCODERS_PATH = MODEL_DIR / "label_encoders.pkl"
FEATURE_COLUMNS_PATH = MODEL_DIR / "feature_columns.pkl"
LEGACY_PATHS = {
    "weather": MODEL_DIR / "weather_encoder.pkl",
    "traffic": MODEL_DIR / "traffic_encoder.pkl",
    "road": MODEL_DIR / "road_encoder.pkl",
    "time": MODEL_DIR / "time_encoder.pkl",
    "risk": MODEL_DIR / "risk_encoder.pkl",
}

model = joblib.load(MODEL_PATH)
# API requests are short, individual inference jobs. A single worker avoids
# spawning processes per request on Windows and in restricted runtimes.
if hasattr(model, "n_jobs"):
    model.n_jobs = 1
encoders = {}
feature_columns = None
legacy_mode = False
dataset_defaults = None

if LABEL_ENCODERS_PATH.exists() and FEATURE_COLUMNS_PATH.exists():
    encoders = joblib.load(LABEL_ENCODERS_PATH)
    feature_columns = joblib.load(FEATURE_COLUMNS_PATH)
    print("Predictor loaded generic model artifacts.")
elif all(path.exists() for path in LEGACY_PATHS.values()):
    encoders["weather"] = joblib.load(LEGACY_PATHS["weather"])
    encoders["traffic"] = joblib.load(LEGACY_PATHS["traffic"])
    encoders["road"] = joblib.load(LEGACY_PATHS["road"])
    encoders["time"] = joblib.load(LEGACY_PATHS["time"])
    encoders["risk"] = joblib.load(LEGACY_PATHS["risk"])
    legacy_mode = True
    print("Predictor loaded legacy model artifacts.")
else:
    raise FileNotFoundError("Predictor artifacts are missing. Please run ai/train_model.py and make sure model files exist.")


def _coerce_numeric(value):
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    return value


def _load_dataset_defaults():
    global dataset_defaults
    if dataset_defaults is not None:
        return dataset_defaults

    defaults = {}
    if feature_columns is None or not DATASET_PATH.exists():
        dataset_defaults = defaults
        return defaults

    df = pd.read_csv(DATASET_PATH, usecols=feature_columns)
    for col in feature_columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            defaults[col] = df[col].median()
        else:
            mode = df[col].mode()
            defaults[col] = mode.iloc[0] if not mode.empty else ""

    dataset_defaults = defaults
    return defaults


def _encode_value(column, value):
    if value is None:
        return None
    if column in encoders and isinstance(encoders[column], LabelEncoder):
        return encoders[column].transform([str(value)])[0]
    if isinstance(value, str):
        return _coerce_numeric(value)
    return value


def predict_accident(weather=None, traffic=None, road=None, speed=None, time=None,
                     road_type=None, road_condition=None, traffic_density=None,
                     average_traffic_speed=None, temperature=None, lanes=None):
    if legacy_mode:
        if weather is None or traffic is None or road is None or speed is None or time is None:
            raise ValueError("Missing required legacy prediction inputs")

        weather = encoders["weather"].transform([weather])[0]
        traffic = encoders["traffic"].transform([traffic])[0]
        road = encoders["road"].transform([road])[0]
        time = encoders["time"].transform([time])[0]
        prediction = model.predict([[weather, traffic, road, speed, time]])
        prediction = encoders["risk"].inverse_transform(prediction)
        return prediction[0]

    defaults = _load_dataset_defaults()
    input_row = defaults.copy()

    mapping = {
        "Weather": weather,
        "TrafficDensity": traffic_density or traffic,
        "RoadType": road_type,
        "RoadCondition": road_condition,
        "TimeOfDay": time,
        "SpeedLimit": speed,
        "AverageTrafficSpeed": average_traffic_speed,
        "Temperature": temperature,
        "NumberOfLanes": lanes,
    }

    for column, value in mapping.items():
        if value is not None:
            input_row[column] = value

    feature_vector = []
    for column in feature_columns:
        raw_value = input_row.get(column)
        if raw_value is None:
            raw_value = defaults.get(column)
        encoded = _encode_value(column, raw_value)
        if encoded is None and raw_value is not None:
            encoded = _coerce_numeric(raw_value)
        feature_vector.append(encoded)

    # Keep inference inside the API process. Some Windows deployments prevent
    # joblib from spawning worker processes for an individual web request.
    with joblib.parallel_backend("threading"):
        prediction = model.predict([feature_vector])
    if "AccidentRisk" in encoders:
        prediction = encoders["AccidentRisk"].inverse_transform(prediction)
    elif "risk" in encoders:
        prediction = encoders["risk"].inverse_transform(prediction)
    else:
        prediction = prediction.astype(str)
    return prediction[0]
