
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

df = pd.read_csv(DATA_DIR / "case_level_dataset.csv")

df["Accepted"] = (
    df["Accepted"].astype(str).str.strip().str.lower()
    .map({"true": 1, "false": 0})
)

df = df.dropna(subset=["Accepted"]).copy()

start = pd.to_datetime(df["start_time"], utc=True, errors="coerce")
df["start_month"] = start.dt.month
df["start_weekday"] = start.dt.dayofweek

features = [
    "case:LoanGoal",
    "case:RequestedAmount",
    "case:ApplicationType",
    "start_month",
    "start_weekday",
]

X = df[features].copy()
y = df["Accepted"].astype(int)

categorical = [
    col for col in X.columns
    if X[col].dtype == "object"
    or pd.api.types.is_string_dtype(X[col])
]
numeric = [col for col in X.columns if col not in categorical]

# Logistic regression benefits from scaled numeric inputs.
logistic_preprocessor = ColumnTransformer([
    ("numeric", Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ]), numeric),
    ("categorical", Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ]), categorical),
])

# Random forests do not require numeric scaling.
forest_preprocessor = ColumnTransformer([
    ("numeric", SimpleImputer(strategy="median"), numeric),
    ("categorical", Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ]), categorical),
])

models = {
    "majority_baseline": DummyClassifier(strategy="most_frequent"),
    "logistic_regression": Pipeline([
        ("preprocess", logistic_preprocessor),
        ("classifier", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        )),
    ]),
    "random_forest": Pipeline([
        ("preprocess", forest_preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )),
    ]),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
rows = []

print("=" * 75)
print("5-FOLD STRATIFIED CROSS-VALIDATION")
print("=" * 75)
print("Cases:", len(df))
print("Features:", features)
print("Accepted rate:", round(y.mean() * 100, 2), "%")

for name, model in models.items():
    fold_scores = {
        "accuracy": [],
        "balanced_accuracy": [],
        "f1_accepted": [],
        "roc_auc": [],
    }

    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model.fit(X_train, y_train)
        predictions = model.predict(X_test)

        fold_scores["accuracy"].append(
            accuracy_score(y_test, predictions)
        )
        fold_scores["balanced_accuracy"].append(
            balanced_accuracy_score(y_test, predictions)
        )
        fold_scores["f1_accepted"].append(
            f1_score(y_test, predictions, zero_division=0)
        )

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(X_test)[:, 1]
            fold_scores["roc_auc"].append(
                roc_auc_score(y_test, probabilities)
            )

    row = {"model": name}

    for metric, values in fold_scores.items():
        row[f"{metric}_mean"] = float(np.mean(values))
        row[f"{metric}_std"] = float(np.std(values, ddof=1))

    rows.append(row)

results = pd.DataFrame(rows)
output = DATA_DIR / "acceptance_cross_validation_metrics.csv"
results.to_csv(output, index=False)

print("\nResults (mean and standard deviation across folds):")
print(results.round(4).to_string(index=False))
print("\nSaved:", output)

print(
    "\nInterpretation: these are cross-validation estimates, not proof "
    "of real-world performance. The features are intake-oriented, but "
    "their actual availability at prediction time must still be verified."
)
