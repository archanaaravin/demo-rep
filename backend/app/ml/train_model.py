import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to PostgreSQL
engine = create_engine(DATABASE_URL)

# Read accident data
df = pd.read_sql("SELECT * FROM accidents", engine)
print(df.head())
print(df["severity"].unique())
print(df.shape)

# Select features
features = [
    "rainfall_mm",
    "temperature_c",
    "speed_limit",
    "lanes"
]

# Convert severity into numbers
severity_map = {
    "Minor": 0,
    "Major": 1,
    "Fatal": 2
}

df["severity"] = df["severity"].map(severity_map)

# Remove missing values
df = df.dropna(subset=features + ["severity"])

X = df[features]
y = df["severity"]

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Train model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)

print(f"Model Accuracy: {accuracy * 100:.2f}%")

# Save model
joblib.dump(model, "trained_model.pkl")

print("Model saved successfully.")