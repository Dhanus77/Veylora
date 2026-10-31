
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
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
y = df["Accepted"].astype(int)

start = pd.to_datetime(df["start_time"], utc=True, errors="coerce")
df["start_month"] = start.dt.month
df["start_weekday"] = start.dt.dayofweek

intake_features = [
    "case:LoanGoal",
    "case:RequestedAmount",
    "case:ApplicationType",
    "start_month",
    "start_weekday",
]

# Exploratory alternative: zero may mean unavailable/special-coded.
# Preserve an indicator and impute zero scores to the median of nonzero scores.
df["CreditScore"] = pd.to_numeric(df["CreditScore"], errors="coerce")
df["CreditScore_zero_flag"] = df["CreditScore"].eq(0).astype(int)
df["CreditScore_adjusted"] = df["CreditScore"].mask(
    df["CreditScore"].eq(0), np.nan
)

feature_sets = {
    "intake_only": intake_features,
    "intake_plus_credit_score_exploratory": intake_features + [
        "CreditScore_adjusted",
        "CreditScore_zero_flag",
    ],
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
rows = []

for set_name, features in feature_sets.items():
    X = df[features].copy()

    categorical = [
        c for c in X.columns
        if X[c].dtype == "object"
        or pd.api.types.is_string_dtype(X[c])
    ]
    numeric = [c for c in X.columns if c not in categorical]

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

    balanced_scores = []
    auc_scores = []

    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)[:, 1]

        balanced_scores.append(
            balanced_accuracy_score(y_test, predictions)
        )
        auc_scores.append(roc_auc_score(y_test, probabilities))

    rows.append({
        "feature_set": set_name,
        "balanced_accuracy_mean": np.mean(balanced_scores),
        "balanced_accuracy_std": np.std(balanced_scores, ddof=1),
        "roc_auc_mean": np.mean(auc_scores),
        "roc_auc_std": np.std(auc_scores, ddof=1),
    })

results = pd.DataFrame(rows)
output = DATA_DIR / "acceptance_feature_comparison.csv"
results.to_csv(output, index=False)

print("=" * 75)
print("ACCEPTANCE FEATURE COMPARISON — 5-FOLD CV")
print("=" * 75)
print(results.round(4).to_string(index=False))
print("\nSaved:", output)
print(
    "\nCaution: the credit-score experiment is exploratory. Do not interpret "
    "it as an intake-ready model until feature timing and score semantics "
    "are verified."
)
