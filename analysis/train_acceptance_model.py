
from pathlib import Path
import json

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"
MODEL_DIR = BASE_DIR / "models"

INPUT = DATA_DIR / "case_level_dataset.csv"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
TEST_SIZE = 0.20

df = pd.read_csv(INPUT)

# The existing dataset label is the target.
# True = accepted, False = not accepted according to this field.
df["Accepted"] = (
    df["Accepted"].astype(str).str.strip().str.lower()
    .map({"true": 1, "false": 0})
)

df = df.dropna(subset=["Accepted"]).copy()
y = df["Accepted"].astype(int)

# Restrict the initial experiment to features intended to be available
# near application intake. Do not use outcome/event counts or later
# financial/credit attributes in this first baseline.
candidate_features = [
    "case:LoanGoal",
    "case:RequestedAmount",
    "case:ApplicationType",
    "start_month",
    "start_weekday",
]

# Derive calendar features from the recorded start time.
start = pd.to_datetime(df["start_time"], utc=True, errors="coerce")
df["start_month"] = start.dt.month
df["start_weekday"] = start.dt.dayofweek

features = [c for c in candidate_features if c in df.columns]
X = df[features].copy()

categorical_features = [
    c for c in X.columns
    if X[c].dtype == "object" or
    pd.api.types.is_string_dtype(X[c])
]
numeric_features = [c for c in X.columns if c not in categorical_features]

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features),
])

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y,
)

models = {
    "majority_baseline": DummyClassifier(strategy="most_frequent"),
    "random_forest": Pipeline([
        ("preprocess", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )),
    ]),
}

results = []
fitted_models = {}

print("=" * 75)
print("ACCEPTANCE PREDICTION — INITIAL BASELINE")
print("=" * 75)
print("Rows:", len(df))
print("Features:", features)
print("Accepted rate:", round(y.mean() * 100, 2), "%")
print("Train cases:", len(X_train))
print("Test cases:", len(X_test))

for name, model in models.items():
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, probabilities)
    else:
        auc = np.nan

    row = {
        "model": name,
        "accuracy": accuracy_score(y_test, predictions),
        "balanced_accuracy": balanced_accuracy_score(y_test, predictions),
        "precision_accepted": precision_score(
            y_test, predictions, zero_division=0
        ),
        "recall_accepted": recall_score(
            y_test, predictions, zero_division=0
        ),
        "f1_accepted": f1_score(
            y_test, predictions, zero_division=0
        ),
        "roc_auc": auc,
    }
    results.append(row)
    fitted_models[name] = model

    print(f"\n--- {name} ---")
    for metric, value in row.items():
        if metric != "model":
            print(f"{metric}: {value:.4f}")

    print("Confusion matrix [rows=true, columns=predicted]:")
    print(confusion_matrix(y_test, predictions))
    print(classification_report(
        y_test,
        predictions,
        target_names=["Not accepted", "Accepted"],
        zero_division=0,
    ))

results_df = pd.DataFrame(results)
metrics_path = DATA_DIR / "acceptance_model_metrics.csv"
results_df.to_csv(metrics_path, index=False)

print("\nSaved metrics:", metrics_path)
print("\nReminder:")
print("- This is an initial random split, not a time-based validation.")
print("- The target is the dataset's Accepted field, not a reconstructed final status.")
print("- Predictive performance may be limited by the small dataset.")
print("- Features and model selection require validation before deployment.")
