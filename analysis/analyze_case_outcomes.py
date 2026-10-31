
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

INPUT = DATA_DIR / "case_level_dataset.csv"
OUTPUT_SUMMARY = DATA_DIR / "case_outcome_summary.csv"
OUTPUT_GROUPS = DATA_DIR / "case_outcome_duration_comparison.csv"
OUTPUT_CORRELATIONS = DATA_DIR / "case_feature_correlations.csv"

if not INPUT.exists():
    raise FileNotFoundError(f"Missing input file: {INPUT}")

df = pd.read_csv(INPUT)

required = [
    "case:concept:name",
    "duration_hours",
    "Accepted",
    "event_count",
    "unique_activities",
]

missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Required columns missing: {missing}")

# Normalize the Accepted field without treating missing values as False.
df["Accepted"] = (
    df["Accepted"].astype(str).str.strip().str.lower()
    .map({"true": True, "false": False})
)

# Outcome activity indicators. These are event-presence indicators,
# not mutually exclusive final outcomes.
outcome_columns = {
    "Cancellation event": "activity_count__A_Cancelled",
    "Denial event": "activity_count__A_Denied",
    "Application completion event": "activity_count__A_Complete",
    "Incomplete event": "activity_count__A_Incomplete",
    "Pending event": "activity_count__A_Pending",
    "Offer accepted event": "activity_count__O_Accepted",
    "Offer cancelled event": "activity_count__O_Cancelled",
    "Offer refused event": "activity_count__O_Refused",
    "Offer returned event": "activity_count__O_Returned",
}

summary_rows = []

print("\n" + "=" * 78)
print("DATASET OVERVIEW")
print("=" * 78)
print(f"Applications: {len(df):,}")
print(f"Unique application IDs: {df['case:concept:name'].nunique():,}")
print(f"Missing duration values: {df['duration_hours'].isna().sum():,}")
print(f"Missing Accepted values: {df['Accepted'].isna().sum():,}")

print("\nACCEPTED FIELD DISTRIBUTION")
print(df["Accepted"].value_counts(dropna=False).to_string())

for label, column in outcome_columns.items():
    if column not in df.columns:
        print(f"\nSkipping missing indicator column: {column}")
        continue

    indicator = pd.to_numeric(df[column], errors="coerce").fillna(0) > 0
    durations = df.loc[indicator, "duration_hours"].dropna()
    no_event_durations = df.loc[~indicator, "duration_hours"].dropna()

    summary_rows.append({
        "outcome_or_event": label,
        "applications_with_event": int(indicator.sum()),
        "percentage_of_applications": round(indicator.mean() * 100, 2),
        "median_duration_with_event_hours": (
            round(durations.median(), 2) if len(durations) else np.nan
        ),
        "median_duration_without_event_hours": (
            round(no_event_durations.median(), 2)
            if len(no_event_durations) else np.nan
        ),
    })

summary = pd.DataFrame(summary_rows)
summary.to_csv(OUTPUT_SUMMARY, index=False)

print("\n" + "=" * 78)
print("OUTCOME / EVENT PRESENCE")
print("=" * 78)
print(summary.to_string(index=False))

# Compare duration distributions for binary event presence.
group_rows = []

for label, column in outcome_columns.items():
    if column not in df.columns:
        continue

    present = pd.to_numeric(df[column], errors="coerce").fillna(0) > 0

    for group_name, mask in [
        ("Event present", present),
        ("Event absent", ~present),
    ]:
        durations = df.loc[mask, "duration_hours"].dropna()

        group_rows.append({
            "event": label,
            "group": group_name,
            "case_count": int(mask.sum()),
            "median_hours": (
                round(durations.median(), 2) if len(durations) else np.nan
            ),
            "mean_hours": (
                round(durations.mean(), 2) if len(durations) else np.nan
            ),
            "p90_hours": (
                round(durations.quantile(0.90), 2)
                if len(durations) else np.nan
            ),
        })

# Compare recorded acceptance groups.
for accepted_value, group_name in [
    (True, "Accepted=True"),
    (False, "Accepted=False"),
]:
    mask = df["Accepted"].eq(accepted_value)
    durations = df.loc[mask, "duration_hours"].dropna()

    group_rows.append({
        "event": "Accepted field",
        "group": group_name,
        "case_count": int(mask.sum()),
        "median_hours": (
            round(durations.median(), 2) if len(durations) else np.nan
        ),
        "mean_hours": (
            round(durations.mean(), 2) if len(durations) else np.nan
        ),
        "p90_hours": (
            round(durations.quantile(0.90), 2)
            if len(durations) else np.nan
        ),
    })

groups = pd.DataFrame(group_rows)
groups.to_csv(OUTPUT_GROUPS, index=False)

print("\n" + "=" * 78)
print("DURATION COMPARISONS")
print("=" * 78)
print(groups.to_string(index=False))

# Exploratory correlations for numeric process and business attributes.
numeric_candidates = [
    "duration_hours",
    "event_count",
    "unique_activities",
    "case:RequestedAmount",
    "CreditScore",
    "OfferedAmount",
    "MonthlyCost",
    "NumberOfTerms",
    "FirstWithdrawalAmount",
]

available = [c for c in numeric_candidates if c in df.columns]
numeric = df[available].apply(pd.to_numeric, errors="coerce")

correlations = numeric.corr(method="spearman")["duration_hours"].drop(
    labels=["duration_hours"], errors="ignore"
)

corr_df = correlations.rename("spearman_correlation_with_duration").reset_index()
corr_df = corr_df.rename(columns={"index": "feature"})
corr_df["absolute_correlation"] = corr_df[
    "spearman_correlation_with_duration"
].abs()
corr_df = corr_df.sort_values("absolute_correlation", ascending=False)

corr_df.to_csv(OUTPUT_CORRELATIONS, index=False)

print("\n" + "=" * 78)
print("EXPLORATORY SPEARMAN CORRELATIONS WITH DURATION")
print("=" * 78)
print(corr_df.to_string(index=False))

print("\nFiles saved:")
print(OUTPUT_SUMMARY)
print(OUTPUT_GROUPS)
print(OUTPUT_CORRELATIONS)

print(
    "\nInterpretation warning: event presence and duration associations are "
    "descriptive. They do not establish causation. Event indicators can "
    "overlap, and some business attributes may be recorded only after "
    "part of the application process."
)
