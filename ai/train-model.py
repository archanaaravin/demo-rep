from pathlib import Path
import pandas as pd

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset" / "accidents.csv"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Read the dataset
data = pd.read_csv(DATASET_PATH)

print("Original Dataset:\n")
print(data)

# Create Label Encoders
weather_encoder = LabelEncoder()
traffic_encoder = LabelEncoder()
road_encoder = LabelEncoder()
time_encoder = LabelEncoder()
risk_encoder = LabelEncoder()

# Convert text into numbers
data["Weather"] = weather_encoder.fit_transform(data["Weather"])
data["TrafficDensity"] = traffic_encoder.fit_transform(data["TrafficDensity"])
data["RoadCondition"] = road_encoder.fit_transform(data["RoadCondition"])
data["TimeOfDay"] = time_encoder.fit_transform(data["TimeOfDay"])
data["AccidentRisk"] = risk_encoder.fit_transform(data["AccidentRisk"])

print("\nEncoded Dataset:\n")
print(data)

# -----------------------------
# Separate Features and Target
# -----------------------------

X = data.drop("AccidentRisk", axis=1)
y = data["AccidentRisk"]

print("\nFeatures (X):")
print(X)

print("\nTarget (y):")
print(y)

# -----------------------------
# Split the dataset
# -----------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

print("\nTraining Data Shape:", X_train.shape)
print("Testing Data Shape:", X_test.shape)

model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# -----------------------------
# Test the trained model
# -----------------------------

y_pred = model.predict(X_test)

print("\nPredictions:")
print(y_pred)

print("\nActual Values:")
print(y_test.values)
# -----------------------------
# Calculate Accuracy
# -----------------------------

accuracy = accuracy_score(y_test, y_pred)

print(f"\nModel Accuracy: {accuracy * 100:.2f}%")
# -----------------------------
# Save the trained model
# -----------------------------

joblib.dump(model, MODELS_DIR / "accident_model.pkl")

print("\n✅ Model saved as accident_model.pkl")
# -----------------------------
# Save the Label Encoders
# -----------------------------

joblib.dump(weather_encoder, MODELS_DIR / "weather_encoder.pkl")
joblib.dump(traffic_encoder, MODELS_DIR / "traffic_encoder.pkl")
joblib.dump(road_encoder, MODELS_DIR / "road_encoder.pkl")
joblib.dump(time_encoder, MODELS_DIR / "time_encoder.pkl")
joblib.dump(risk_encoder, MODELS_DIR / "risk_encoder.pkl")

print("✅ All encoders saved successfully!")
