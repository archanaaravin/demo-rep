# from pathlib import Path
# import pandas as pd

# from sklearn.preprocessing import LabelEncoder
# from sklearn.model_selection import train_test_split
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.metrics import accuracy_score
# import joblib

# BASE_DIR = Path(__file__).resolve().parent
# DATASET_PATH = BASE_DIR / "dataset" / "accidents.csv"
# MODELS_DIR = BASE_DIR / "models"
# MODELS_DIR.mkdir(parents=True, exist_ok=True)

# # Read the dataset
# data = pd.read_csv(DATASET_PATH)

# print("Original Dataset:\n")
# print(data)

# # Create Label Encoders
# weather_encoder = LabelEncoder()
# traffic_encoder = LabelEncoder()
# road_encoder = LabelEncoder()
# time_encoder = LabelEncoder()
# risk_encoder = LabelEncoder()

# # Convert text into numbers
# data["Weather"] = weather_encoder.fit_transform(data["Weather"])
# data["TrafficDensity"] = traffic_encoder.fit_transform(data["TrafficDensity"])
# data["RoadCondition"] = road_encoder.fit_transform(data["RoadCondition"])
# data["TimeOfDay"] = time_encoder.fit_transform(data["TimeOfDay"])
# data["AccidentRisk"] = risk_encoder.fit_transform(data["AccidentRisk"])

# print("\nEncoded Dataset:\n")
# print(data)

# # -----------------------------
# # Separate Features and Target
# # -----------------------------

# X = data.drop("AccidentRisk", axis=1)
# y = data["AccidentRisk"]

# print("\nFeatures (X):")
# print(X)

# print("\nTarget (y):")
# print(y)

# # -----------------------------
# # Split the dataset
# # -----------------------------

# X_train, X_test, y_train, y_test = train_test_split(
#     X,
#     y,
#     test_size=0.2,
#     random_state=42
# )

# print("\nTraining Data Shape:", X_train.shape)
# print("Testing Data Shape:", X_test.shape)

# model = RandomForestClassifier(random_state=42)
# model.fit(X_train, y_train)

# # -----------------------------
# # Test the trained model
# # -----------------------------

# y_pred = model.predict(X_test)

# print("\nPredictions:")
# print(y_pred)

# print("\nActual Values:")
# print(y_test.values)
# # -----------------------------
# # Calculate Accuracy
# # -----------------------------

# accuracy = accuracy_score(y_test, y_pred)

# print(f"\nModel Accuracy: {accuracy * 100:.2f}%")
# # -----------------------------
# # Save the trained model
# # -----------------------------

# joblib.dump(model, MODELS_DIR / "accident_model.pkl")

# print("\n✅ Model saved as accident_model.pkl")
# # -----------------------------
# # Save the Label Encoders
# # -----------------------------

# joblib.dump(weather_encoder, MODELS_DIR / "weather_encoder.pkl")
# joblib.dump(traffic_encoder, MODELS_DIR / "traffic_encoder.pkl")
# joblib.dump(road_encoder, MODELS_DIR / "road_encoder.pkl")
# joblib.dump(time_encoder, MODELS_DIR / "time_encoder.pkl")
# joblib.dump(risk_encoder, MODELS_DIR / "risk_encoder.pkl")

# print("✅ All encoders saved successfully!")


"""
Accident Risk Model Trainer
----------------------------
Trains a RandomForestClassifier to predict AccidentRisk (Low/Medium/High)
from the synthetic Chennai road accident dataset.

Drop-in replacement for the original trainer, extended to handle the
new dataset's larger set of categorical/numeric columns automatically
instead of hardcoding four encoders.
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = r"C:\Users\archa\demo-AegisAI\demo-rep\ai\dataset\accidents_v2.csv"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Column that predicts risk. Other target-like columns (AccidentSeverity,
# Hotspot) are excluded from the features below to avoid leakage — they are
# generated together with AccidentRisk from the same underlying signals, so
# including them would let the model "cheat" instead of learning from real
# road/weather/traffic conditions.
TARGET_COLUMN = "AccidentRisk"

# Columns that are identifiers or other targets, not predictive features.
NON_FEATURE_COLUMNS = ["AccidentID", "AccidentSeverity", "Hotspot"]

# -----------------------------
# Read the dataset
# -----------------------------
data = pd.read_csv(DATASET_PATH)
print("Original Dataset:\n")
print(data.head())
print(f"\nShape: {data.shape}")

# -----------------------------
# Handle missing values
# -----------------------------
# The dataset has a small amount (<2%) of intentionally missing values.
# Numeric columns -> fill with column median.
# Categorical (text) columns -> fill with column mode.
numeric_cols = data.select_dtypes(include=["int64", "float64"]).columns.tolist()
categorical_cols = data.select_dtypes(include=["object"]).columns.tolist()

for col in numeric_cols:
    if data[col].isna().any():
        data[col] = data[col].fillna(data[col].median())

for col in categorical_cols:
    if data[col].isna().any():
        data[col] = data[col].fillna(data[col].mode().iloc[0])

# -----------------------------
# Build the feature/target split
# -----------------------------
feature_columns = [
    c for c in data.columns
    if c not in NON_FEATURE_COLUMNS and c != TARGET_COLUMN
]
categorical_feature_cols = [c for c in feature_columns if c in categorical_cols]

# -----------------------------
# Encode all categorical columns (features + target)
# -----------------------------
# A single dict of encoders replaces the old fixed set of four
# (weather_encoder, traffic_encoder, road_encoder, time_encoder) since the
# new dataset has many more text columns (RoadType, LightingCondition,
# Weekend, FestivalSeason, CurvePresent, BlackSpotReported, etc.).
encoders = {}

for col in categorical_feature_cols:
    le = LabelEncoder()
    data[col] = le.fit_transform(data[col])
    encoders[col] = le

target_encoder = LabelEncoder()
data[TARGET_COLUMN] = target_encoder.fit_transform(data[TARGET_COLUMN])
encoders[TARGET_COLUMN] = target_encoder

print("\nEncoded Dataset:\n")
print(data[feature_columns + [TARGET_COLUMN]].head())

# -----------------------------
# Separate Features and Target
# -----------------------------
X = data[feature_columns]
y = data[TARGET_COLUMN]

print("\nFeatures (X):")
print(X.head())
print("\nTarget (y):")
print(y.head())

# -----------------------------
# Split the dataset
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

print("\nTraining Data Shape:", X_train.shape)
print("Testing Data Shape:", X_test.shape)

# -----------------------------
# Train the model
# -----------------------------
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    random_state=42,
    n_jobs=-1,
)
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

print("\nClassification Report:")
print(
    classification_report(
        y_test, y_pred, target_names=target_encoder.classes_
    )
)

# -----------------------------
# Feature importance (useful for the analytics dashboard / recommendation engine)
# -----------------------------
importances = (
    pd.Series(model.feature_importances_, index=feature_columns)
    .sort_values(ascending=False)
)
print("\nTop 10 Feature Importances:")
print(importances.head(10))

# -----------------------------
# Save the trained model
# -----------------------------
joblib.dump(model, MODELS_DIR / "accident_model.pkl")
print("\n✅ Model saved as accident_model.pkl")

# -----------------------------
# Save the Label Encoders
# -----------------------------
# Saved as a single dict keyed by column name (encoders["Weather"], etc.)
# so it scales to however many categorical columns the dataset has,
# instead of one .pkl file per column.
joblib.dump(encoders, MODELS_DIR / "label_encoders.pkl")

# Also persist the exact feature column order used for training — required
# at inference time so a new row can be encoded/ordered the same way.
joblib.dump(feature_columns, MODELS_DIR / "feature_columns.pkl")

print("✅ All encoders saved successfully (models/label_encoders.pkl)!")
print("✅ Feature column order saved (models/feature_columns.pkl)!")
