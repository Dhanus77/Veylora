
from pathlib import Path
import json

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, median_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "processed" / "case_level_dataset.csv"
MODEL_DIR = ROOT / "models"
OUTPUT_DIR = ROOT / "data" / "processed"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH, parse_dates=["start_time"])

# Target: elapsed time between the first and last recorded event.
df = df.dropna(subset=["duration_hours"]).copy()
df = df[df["duration_hours"] >= 0].copy()

# Use only information plausibly available at application start.
df["start_month"] = df["start_time"].dt.month
df["start_weekday"] = df["start_time"].dt.dayofweek

numeric_features = [
    "case:RequestedAmount",
    "start_month",
    "start_weekday",
]

categorical_features = [
    "case:LoanGoal",
    "case:ApplicationType",
]

features = numeric_features + categorical_features
X = df[features]
y = df["duration_hours"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features),
])

models = {
    "median_baseline": DummyRegressor(strategy="median"),
    "random_forest": RandomForestRegressor(
        n_estimators=200,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1,
    ),
}

results = []
trained = {}

for name, estimator in models.items():
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", estimator),
    ])

    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)

    results.append({
        "model": name,
        "MAE_hours": mean_absolute_error(y_test, predictions),
        "MedianAE_hours": median_absolute_error(y_test, predictions),
        "R2": r2_score(y_test, predictions),
    })

    trained[name] = pipeline

results_df = pd.DataFrame(results).sort_values("MAE_hours")
results_path = OUTPUT_DIR / "duration_model_metrics.csv"
results_df.to_csv(results_path, index=False)

joblib.dump(trained["random_forest"], MODEL_DIR / "duration_model.joblib")

print("\n=== TEST-SET MODEL COMPARISON ===")
print(results_df.round(3).to_string(index=False))
print(f"\nTest applications: {len(y_test)}")
print(f"Metrics saved to: {results_path}")
print(f"Model saved to: {MODEL_DIR / 'duration_model.joblib'}")
print("\nLower MAE is better. Compare the forest against the baseline.")
