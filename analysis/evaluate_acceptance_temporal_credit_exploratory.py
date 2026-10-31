from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

INPUT = DATA_DIR / "case_level_dataset.csv"
OUTPUT = DATA_DIR / "acceptance_temporal_credit_exploratory_metrics.csv"

BASE_FEATURES = [
    "case:LoanGoal",
    "case:RequestedAmount",
    "case:ApplicationType",
    "start_month",
    "start_weekday",
]

CREDIT_FEATURES = [
    "CreditScore_adjusted",
    "CreditScore_zero_flag",
]


def main():
    df = pd.read_csv(INPUT)

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

    # Zero is treated as a special/missing code for this exploratory
    # comparison, based on the observed event-log pattern.
    df["CreditScore_zero_flag"] = df["CreditScore"].eq(0).astype(int)
    df["CreditScore_adjusted"] = df["CreditScore"].mask(
        df["CreditScore"].eq(0), np.nan
    )

    df = df.sort_values("start_time", kind="mergesort").reset_index(drop=True)
    split_index = int(len(df) * 0.80)
    train = df.iloc[:split_index].copy()
    test = df.iloc[split_index:].copy()

    if train["Accepted"].nunique() < 2 or test["Accepted"].nunique() < 2:
        raise ValueError("Train and test partitions must each contain both classes.")

    features = BASE_FEATURES + CREDIT_FEATURES
    X_train = train[features].copy()
    X_test = test[features].copy()
    y_train = train["Accepted"].astype(int)
    y_test = test["Accepted"].astype(int)

    categorical = [
        column for column in features
        if X_train[column].dtype == "object"
        or pd.api.types.is_string_dtype(X_train[column])
    ]
    numeric = [column for column in features if column not in categorical]

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
        "feature_set": "intake_plus_credit_score_exploratory",
        "status": "exploratory_not_for_primary_prediction",
        "features": ";".join(features),
        "train_cases": len(train),
        "test_cases": len(test),
        "balanced_accuracy": balanced_accuracy_score(y_test, predictions),
        "roc_auc": roc_auc_score(y_test, probabilities),
        "credit_score_warning": (
            "Non-zero scores were first recorded on O_Create Offer complete "
            "events or later; availability before offer time is unverified."
        ),
    }

    print("=" * 75)
    print("EXPLORATORY TEMPORAL CREDIT-SCORE COMPARISON — NOT PRIMARY")
    print("=" * 75)
    print("Training cases:", len(train))
    print("Testing cases:", len(test))
    print("Balanced accuracy:", round(result["balanced_accuracy"], 4))
    print("ROC-AUC:", round(result["roc_auc"], 4))
    print("\nWARNING:", result["credit_score_warning"])

    pd.DataFrame([result]).to_csv(OUTPUT, index=False)
    print("\nSaved exploratory metrics:", OUTPUT)


if __name__ == "__main__":
    main()
