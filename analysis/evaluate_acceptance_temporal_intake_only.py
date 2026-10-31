from pathlib import Path
import shutil

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

INPUT = DATA_DIR / "case_level_dataset.csv"
OUTPUT = DATA_DIR / "acceptance_temporal_metrics.csv"
BACKUP = DATA_DIR / "acceptance_temporal_metrics_before_intake_only.csv"

TARGET_DEFINITION = (
    "Last recorded Accepted value on O_Create Offer [complete] "
    "for each application"
)

FEATURES = [
    "case:LoanGoal",
    "case:RequestedAmount",
    "case:ApplicationType",
    "start_month",
    "start_weekday",
]

TRAIN_FRACTION = 0.80


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Case-level dataset not found: {INPUT}")

    df = pd.read_csv(INPUT)

    required = ["Accepted", "start_time", *FEATURES[:3]]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Required columns are missing: {missing}")

    target_text = df["Accepted"].astype(str).str.strip().str.lower()
    df["Accepted"] = target_text.map({"true": 1, "false": 0})

    invalid_targets = int(df["Accepted"].isna().sum())
    if invalid_targets:
        raise ValueError(
            f"{invalid_targets} rows have invalid/missing Accepted values. "
            "Refusing to evaluate."
        )

    df["start_time"] = pd.to_datetime(
        df["start_time"], utc=True, errors="coerce"
    )
    df = df.dropna(subset=["start_time"]).copy()

    df["start_month"] = df["start_time"].dt.month
    df["start_weekday"] = df["start_time"].dt.dayofweek

    absent_features = [column for column in FEATURES if column not in df.columns]
    if absent_features:
        raise ValueError(f"Required model features are missing: {absent_features}")

    df = df.sort_values("start_time", kind="mergesort").reset_index(drop=True)
    split_index = int(len(df) * TRAIN_FRACTION)

    train = df.iloc[:split_index].copy()
    test = df.iloc[split_index:].copy()

    if train.empty or test.empty:
        raise ValueError("Chronological train/test split produced an empty partition.")

    if train["Accepted"].nunique() < 2 or test["Accepted"].nunique() < 2:
        raise ValueError(
            "Train and test partitions must each contain both target classes."
        )

    X_train = train[FEATURES].copy()
    X_test = test[FEATURES].copy()
    y_train = train["Accepted"].astype(int)
    y_test = test["Accepted"].astype(int)

    categorical = [
        column for column in FEATURES
        if X_train[column].dtype == "object"
        or pd.api.types.is_string_dtype(X_train[column])
    ]
    numeric = [column for column in FEATURES if column not in categorical]

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
        "feature_set": "intake_only_logistic_regression",
        "target_definition": TARGET_DEFINITION,
        "features": ";".join(FEATURES),
        "train_cases": len(train),
        "test_cases": len(test),
        "train_start": train["start_time"].min(),
        "train_end": train["start_time"].max(),
        "test_start": test["start_time"].min(),
        "test_end": test["start_time"].max(),
        "train_accepted_rate": y_train.mean(),
        "test_accepted_rate": y_test.mean(),
        "balanced_accuracy": balanced_accuracy_score(y_test, predictions),
        "roc_auc": roc_auc_score(y_test, probabilities),
    }

    print("=" * 75)
    print("TEMPORAL ACCEPTANCE VALIDATION — INTAKE-ONLY PRIMARY MODEL")
    print("=" * 75)
    print("Target:", TARGET_DEFINITION)
    print("Features:", FEATURES)
    print("CreditScore excluded: yes")
    print("Training cases:", len(train))
    print("Testing cases:", len(test))
    print("Training period:", result["train_start"], "to", result["train_end"])
    print("Testing period:", result["test_start"], "to", result["test_end"])
    print("Train accepted rate:", round(result["train_accepted_rate"], 3))
    print("Test accepted rate:", round(result["test_accepted_rate"], 3))
    print("\nBalanced accuracy:", round(result["balanced_accuracy"], 4))
    print("ROC-AUC:", round(result["roc_auc"], 4))
    print(classification_report(
        y_test,
        predictions,
        labels=[0, 1],
        target_names=["Not accepted", "Accepted"],
        zero_division=0,
    ))

    # Preserve the earlier two-row temporal file (which included the
    # exploratory credit-score comparison) before replacing the primary file.
    if OUTPUT.exists() and not BACKUP.exists():
        shutil.copy2(OUTPUT, BACKUP)
        print("\nPrevious temporal metrics backed up to:", BACKUP)

    pd.DataFrame([result]).to_csv(OUTPUT, index=False)
    print("\nSaved primary temporal metrics:", OUTPUT)
    print("\nCaution:")
    print("- This is one chronological holdout, not a rolling backtest.")
    print("- CreditScore is excluded because the event log does not establish")
    print("  that it was available before the first offer was created.")
    print("- Results are experimental and do not establish production readiness.")


if __name__ == "__main__":
    main()
