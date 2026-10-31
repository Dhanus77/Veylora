
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    mean_absolute_error,
    median_absolute_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent

DATA_PATH = ROOT / "data" / "processed" / "case_level_dataset.csv"
EVENT_LOG_PATH = ROOT / "data" / "raw" / "sampled-log.xml"
OUTPUT_PATH = ROOT / "data" / "processed" / "duration_model_metrics_v2.csv"


# --------------------------------------------------
# 2. Load the case-level dataset
# --------------------------------------------------

df = pd.read_csv(DATA_PATH)

target = "duration_hours"

if target not in df.columns:
    raise ValueError(f"Target column '{target}' was not found.")

# Check whether calendar features already exist.
if not {"start_month", "start_weekday"}.issubset(df.columns):

    print("Creating calendar features from the original event log...")

    # Import PM4Py only when the features need to be created.
    import pm4py

    if not EVENT_LOG_PATH.exists():
        raise FileNotFoundError(
            f"Event log not found: {EVENT_LOG_PATH}"
        )

    event_log = pm4py.read_xes(str(EVENT_LOG_PATH))
    events = pm4py.convert_to_dataframe(event_log)

    case_col = "case:concept:name"
    timestamp_col = "time:timestamp"

    if case_col not in events.columns or timestamp_col not in events.columns:
        raise ValueError(
            "The event log must contain case:concept:name "
            "and time:timestamp columns."
        )

    events[timestamp_col] = pd.to_datetime(
        events[timestamp_col], errors="coerce", utc=True
    )

    start_times = (
        events.dropna(subset=[timestamp_col])
        .groupby(case_col)[timestamp_col]
        .min()
        .rename("start_time")
        .reset_index()
    )

    start_times["start_month"] = start_times["start_time"].dt.month
    start_times["start_weekday"] = start_times["start_time"].dt.dayofweek

    # Match the case identifier in the case-level dataset.
    df = df.merge(
        start_times[[case_col, "start_month", "start_weekday"]],
        on=case_col,
        how="left",
        validate="one_to_one",
    )

    print("Calendar features created.")


# --------------------------------------------------
# 3. Prepare features and target
# --------------------------------------------------

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

missing_columns = [column for column in features if column not in df.columns]

if missing_columns:
    raise ValueError(f"Missing feature columns: {missing_columns}")

df[target] = pd.to_numeric(df[target], errors="coerce")
df = df.dropna(subset=[target]).copy()

X = df[features].copy()
y = df[target].astype(float)

if (y < 0).any():
    raise ValueError("Duration contains negative values.")

print(f"Applications used: {len(df)}")


# --------------------------------------------------
# 4. Split data
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
)


# --------------------------------------------------
# 5. Preprocess features
# --------------------------------------------------

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            SimpleImputer(strategy="median"),
            numeric_features,
        ),
        (
            "categorical",
            make_pipeline(
                SimpleImputer(strategy="most_frequent"),
                OneHotEncoder(handle_unknown="ignore"),
            ),
            categorical_features,
        ),
    ]
)


# --------------------------------------------------
# 6. Compare three approaches
# --------------------------------------------------

models = {
    "random_forest_raw": RandomForestRegressor(
        n_estimators=200,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    ),
    "random_forest_log_target": RandomForestRegressor(
        n_estimators=200,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    ),
}

results = []

# Simple baseline: predict the training-set median.
baseline_predictions = np.full(len(y_test), y_train.median())

results.append(
    {
        "model": "median_baseline",
        "MAE_hours": mean_absolute_error(y_test, baseline_predictions),
        "MedianAE_hours": median_absolute_error(y_test, baseline_predictions),
        "R2": r2_score(y_test, baseline_predictions),
    }
)

for name, model in models.items():

    pipeline = make_pipeline(preprocessor, model)

    if name == "random_forest_log_target":
        pipeline.fit(X_train, np.log1p(y_train))
        predictions = np.expm1(pipeline.predict(X_test))
    else:
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)

    predictions = np.maximum(predictions, 0)

    results.append(
        {
            "model": name,
            "MAE_hours": mean_absolute_error(y_test, predictions),
            "MedianAE_hours": median_absolute_error(y_test, predictions),
            "R2": r2_score(y_test, predictions),
        }
    )


# --------------------------------------------------
# 7. Save and display results
# --------------------------------------------------

results_df = (
    pd.DataFrame(results)
    .sort_values("MAE_hours")
    .reset_index(drop=True)
)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
results_df.to_csv(OUTPUT_PATH, index=False)

print("\n=== DURATION MODEL COMPARISON ===")
print(results_df.round(3).to_string(index=False))

print(f"\nResults saved to: {OUTPUT_PATH}")
print("\nLower MAE is better. Compare each model against the median baseline.")
