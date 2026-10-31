
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    balanced_accuracy_score,
    classification_report,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

df = pd.read_csv(DATA_DIR / "case_level_dataset.csv")

df["Accepted"] = (
    df["Accepted"].astype(str).str.strip().str.lower()
    .map({"true": 1, "false": 0})
)
df["start_time"] = pd.to_datetime(
    df["start_time"], utc=True, errors="coerce"
)
df["CreditScore"] = pd.to_numeric(
    df["CreditScore"], errors="coerce"
)

df = df.dropna(subset=["Accepted", "start_time"]).copy()
df["start_month"] = df["start_time"].dt.month
df["start_weekday"] = df["start_time"].dt.dayofweek
df["CreditScore_zero_flag"] = df["CreditScore"].eq(0).astype(int)
df["CreditScore_adjusted"] = df["CreditScore"].mask(
    df["CreditScore"].eq(0), np.nan
)

# Sort chronologically; use earliest 80% for training and latest 20% for testing.
df = df.sort_values("start_time").reset_index(drop=True)
split_index = int(len(df) * 0.80)

train = df.iloc[:split_index].copy()
test = df.iloc[split_index:].copy()

if train["Accepted"].nunique() < 2 or test["Accepted"].nunique() < 2:
    raise ValueError(
        "Train and test partitions must each contain both target classes."
    )

feature_sets = {
    "intake_only": [
        "case:LoanGoal",
        "case:RequestedAmount",
        "case:ApplicationType",
        "start_month",
        "start_weekday",
    ],
    "intake_plus_credit_score_exploratory": [
        "case:LoanGoal",
        "case:RequestedAmount",
        "case:ApplicationType",
        "start_month",
        "start_weekday",
        "CreditScore_adjusted",
        "CreditScore_zero_flag",
    ],
}

print("=" * 75)
print("TEMPORAL ACCEPTANCE VALIDATION")
print("=" * 75)
print("Training cases:", len(train))
print("Testing cases:", len(test))
print("Training period:", train["start_time"].min(), "to", train["start_time"].max())
print("Testing period:", test["start_time"].min(), "to", test["start_time"].max())
print("Train accepted rate:", round(train["Accepted"].mean(), 3))
print("Test accepted rate:", round(test["Accepted"].mean(), 3))

results = []

for name, features in feature_sets.items():
    X_train = train[features].copy()
    X_test = test[features].copy()
    y_train = train["Accepted"].astype(int)
    y_test = test["Accepted"].astype(int)

    categorical = [
        c for c in features
        if X_train[c].dtype == "object"
        or pd.api.types.is_string_dtype(X_train[c])
    ]
    numeric = [c for c in features if c not in categorical]

    preprocessor = ColumnTransformer([
        ("numeric", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), numeric),
        ("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical),
    ])

    model = Pipeline([
        ("preprocess", preprocessor),
        ("classifier", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        )),
    ])

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    result = {
        "feature_set": name,
        "balanced_accuracy": balanced_accuracy_score(y_test, predictions),
        "roc_auc": roc_auc_score(y_test, probabilities),
    }
    results.append(result)

    print(f"\n--- {name} ---")
    print("Balanced accuracy:", round(result["balanced_accuracy"], 4))
    print("ROC-AUC:", round(result["roc_auc"], 4))
    print(classification_report(
        y_test,
        predictions,
        labels=[0, 1],
        target_names=["Not accepted", "Accepted"],
        zero_division=0,
    ))

output = DATA_DIR / "acceptance_temporal_metrics.csv"
pd.DataFrame(results).to_csv(output, index=False)
print("Saved:", output)

print(
    "\nCaution: this is a single chronological holdout, not a full rolling "
    "backtest. Credit-score features remain exploratory until their "
    "meaning and availability at the prediction point are verified."
)
