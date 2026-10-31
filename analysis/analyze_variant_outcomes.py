
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "processed"

VARIANT_PATH = DATA_DIR / "case_variant_mapping.csv"
CASE_PATH = DATA_DIR / "case_level_dataset.csv"

OUTPUT_PATH = DATA_DIR / "variant_outcome_analysis.csv"

CASE_COL = "case:concept:name"

# --------------------------------------------------
# 1. Load existing results
# --------------------------------------------------

variants = pd.read_csv(VARIANT_PATH)
cases = pd.read_csv(CASE_PATH)

required_variant = {CASE_COL, "variant_id", "activity_path"}
required_case = {CASE_COL, "duration_hours", "Accepted"}

if not required_variant.issubset(variants.columns):
    raise ValueError(
        f"Missing variant columns: {required_variant - set(variants.columns)}"
    )

if not required_case.issubset(cases.columns):
    raise ValueError(
        f"Missing case columns: {required_case - set(cases.columns)}"
    )

df = variants.merge(
    cases,
    on=CASE_COL,
    how="inner",
    validate="one_to_one",
)

df["duration_hours"] = pd.to_numeric(
    df["duration_hours"], errors="coerce"
)

df = df.dropna(subset=["duration_hours"]).copy()

# Interpret the Accepted case attribute.
accepted_text = df["Accepted"].astype(str).str.strip().str.lower()
df["is_accepted"] = accepted_text.isin(["true", "1", "yes"])

# These indicate whether the completed-event sequence contains
# the corresponding activity. They do not independently establish
# the official business outcome.
df["path_has_cancellation"] = df["activity_path"].str.contains(
    r"(?:^| -> )A_Cancelled(?: -> |$)", regex=True, na=False
)

df["path_has_denial"] = df["activity_path"].str.contains(
    r"(?:^| -> )A_Denied(?: -> |$)", regex=True, na=False
)

# --------------------------------------------------
# 2. Summarize each process variant
# --------------------------------------------------

summary = (
    df.groupby(["variant_id", "activity_path"], dropna=False)
    .agg(
        applications=(CASE_COL, "nunique"),
        median_duration_hours=("duration_hours", "median"),
        mean_duration_hours=("duration_hours", "mean"),
        accepted_count=("is_accepted", "sum"),
        acceptance_rate_pct=("is_accepted", "mean"),
        paths_with_cancellation=("path_has_cancellation", "sum"),
        paths_with_denial=("path_has_denial", "sum"),
    )
    .reset_index()
)

summary["acceptance_rate_pct"] *= 100

# Keep the sample-size threshold explicit.
# Variants with fewer than five cases are too small for our
# primary comparison, but remain in the full output.
summary["sample_size_flag"] = summary["applications"].apply(
    lambda n: "Primary comparison" if n >= 5 else "Small sample"
)

summary = summary.sort_values(
    ["applications", "median_duration_hours"],
    ascending=[False, False],
)

summary.to_csv(OUTPUT_PATH, index=False)

# --------------------------------------------------
# 3. Print useful comparisons
# --------------------------------------------------

print(f"Applications analysed: {len(df)}")
print(f"Distinct variants analysed: {summary['variant_id'].nunique()}")

print("\n=== MOST COMMON VARIANTS ===")
print(
    summary.sort_values("applications", ascending=False)
    .head(15)[
        [
            "variant_id",
            "applications",
            "median_duration_hours",
            "acceptance_rate_pct",
            "paths_with_cancellation",
            "paths_with_denial",
            "sample_size_flag",
            "activity_path",
        ]
    ]
    .round(2)
    .to_string(index=False)
)

print("\n=== LONGEST-MEDIAN-DURATION VARIANTS WITH AT LEAST 5 CASES ===")
eligible = summary[summary["applications"] >= 5]

print(
    eligible.sort_values(
        "median_duration_hours", ascending=False
    ).head(15)[
        [
            "variant_id",
            "applications",
            "median_duration_hours",
            "acceptance_rate_pct",
            "paths_with_cancellation",
            "paths_with_denial",
            "activity_path",
        ]
    ]
    .round(2)
    .to_string(index=False)
)

print(f"\nSaved variant outcome analysis to: {OUTPUT_PATH}")
print(
    "\nCaution: these are descriptive comparisons. "
    "Variant membership is not randomly assigned, so differences "
    "do not prove that a path causes longer duration or a particular outcome."
)
