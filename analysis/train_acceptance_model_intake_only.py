from pathlib import Path

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

INPUT = DATA_DIR / "case_level_dataset.csv"
OUTPUT = DATA_DIR / "acceptance_model_metrics.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.20

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


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Case-level dataset not found: {INPUT}")

    df = pd.read_csv(INPUT)

    required = ["Accepted", "start_time", *FEATURES[:3]]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Required columns are missing: {missing}")

    # The case-level builder now stores the LAST recorded offer outcome.
    target_text = df["Accepted"].astype(str).str.strip().str.lower()
    df["Accepted"] = target_text.map({"true": 1, "false": 0})

    invalid_target_count = int(df["Accepted"].isna().sum())
    if invalid_target_count:
        raise ValueError(
            f"{invalid_target_count} rows have invalid/missing Accepted values. "
            "Refusing to train."
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

    X = df[FEATURES].copy()
    y = df["Accepted"].astype(int)

    if y.nunique() != 2:
        raise ValueError("Acceptance target must contain both classes.")

    categorical_features = [
        column for column in X.columns
        if X[column].dtype == "object"
        or pd.api.types.is_string_dtype(X[column])
    ]
    numeric_features = [
        column for column in X.columns
        if column not in categorical_features
    ]

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

    print("=" * 75)
    print("ACCEPTANCE PREDICTION — INTAKE-ONLY BASELINE")
    print("=" * 75)
    print("Rows:", len(df))
    print("Target:", TARGET_DEFINITION)
    print("Features:", FEATURES)
    print("CreditScore excluded: yes")
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
            auc = float("nan")

        row = {
            "model": name,
            "target_definition": TARGET_DEFINITION,
            "features": ";".join(FEATURES),
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

        print(f"\n--- {name} ---")
        for metric, value in row.items():
            if metric not in {"model", "target_definition", "features"}:
                print(f"{metric}: {value:.4f}")

        print("Confusion matrix [rows=true, columns=predicted]:")
        print(confusion_matrix(y_test, predictions, labels=[0, 1]))
        print(classification_report(
            y_test,
            predictions,
            labels=[0, 1],
            target_names=["Not accepted", "Accepted"],
            zero_division=0,
        ))

    pd.DataFrame(results).to_csv(OUTPUT, index=False)
    print("\nSaved metrics:", OUTPUT)
    print("\nInterpretation:")
    print("- This is a random stratified holdout, not future-period validation.")
    print("- The target is the last recorded offer Accepted value.")
    print("- CreditScore and all later financial/outcome fields are excluded.")
    print("- Treat results as experimental; chronological validation is required.")


if __name__ == "__main__":
    main()
