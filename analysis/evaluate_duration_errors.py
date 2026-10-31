
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "processed" / "case_level_dataset.csv"
EVENT_LOG_PATH = ROOT / "data" / "raw" / "sampled-log.xml"

df = pd.read_csv(DATA_PATH)

# Recreate start-time features from the original event log.
import pm4py

events = pm4py.convert_to_dataframe(
    pm4py.read_xes(str(EVENT_LOG_PATH))
)

events["time:timestamp"] = pd.to_datetime(
    events["time:timestamp"], errors="coerce", utc=True
)

starts = (
    events.dropna(subset=["time:timestamp"])
    .groupby("case:concept:name")["time:timestamp"]
    .min()
    .rename("start_time")
    .reset_index()
)

starts["start_month"] = starts["start_time"].dt.month
starts["start_weekday"] = starts["start_time"].dt.dayofweek

df = df.merge(
    starts[["case:concept:name", "start_month", "start_weekday"]],
    on="case:concept:name",
    how="left",
    validate="one_to_one",
)

numeric = [
    "case:RequestedAmount",
    "start_month",
    "start_weekday",
]

categorical = [
    "case:LoanGoal",
    "case:ApplicationType",
]

df["duration_hours"] = pd.to_numeric(
    df["duration_hours"], errors="coerce"
)
df = df.dropna(subset=["duration_hours"]).copy()

X = df[numeric + categorical]
y = df["duration_hours"].astype(float)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)

preprocessor = ColumnTransformer([
    ("num", SimpleImputer(strategy="median"), numeric),
    ("cat", make_pipeline(
        SimpleImputer(strategy="most_frequent"),
        OneHotEncoder(handle_unknown="ignore"),
    ), categorical),
])

model = make_pipeline(
    preprocessor,
    RandomForestRegressor(
        n_estimators=200,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    ),
)

model.fit(X_train, np.log1p(y_train))
predictions = np.maximum(
    np.expm1(model.predict(X_test)), 0
)

errors = pd.DataFrame({
    "actual_hours": y_test.to_numpy(),
    "predicted_hours": predictions,
})

errors["absolute_error_hours"] = (
    errors["actual_hours"] - errors["predicted_hours"]
).abs()

print("\n=== ERROR SUMMARY ===")
print(errors["absolute_error_hours"].describe().round(2))

print("\n=== EXAMPLE PREDICTIONS ===")
print(errors.head(15).round(2).to_string(index=False))

print("\n=== ERROR BY ACTUAL DURATION GROUP ===")
errors["duration_group"] = pd.cut(
    errors["actual_hours"],
    bins=[0, 168, 336, 720, np.inf],
    labels=["Under 7 days", "7–14 days", "14–30 days", "Over 30 days"],
    include_lowest=True,
)

print(
    errors.groupby("duration_group", observed=False)
    .agg(
        applications=("actual_hours", "count"),
        median_actual_hours=("actual_hours", "median"),
        median_absolute_error=("absolute_error_hours", "median"),
        mean_absolute_error=("absolute_error_hours", "mean"),
    )
    .round(2)
    .to_string()
)
