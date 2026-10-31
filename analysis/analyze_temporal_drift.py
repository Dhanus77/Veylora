
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

df = pd.read_csv(DATA_DIR / "case_level_dataset.csv")

df["start_time"] = pd.to_datetime(
    df["start_time"], utc=True, errors="coerce"
)
df["Accepted"] = (
    df["Accepted"].astype(str).str.strip().str.lower()
    .map({"true": 1, "false": 0})
)
df["CreditScore"] = pd.to_numeric(
    df["CreditScore"], errors="coerce"
)
df = df.dropna(subset=["start_time", "Accepted"]).copy()
df = df.sort_values("start_time").reset_index(drop=True)

# Reproduce the exact 80/20 chronological partition.
split_index = int(len(df) * 0.80)
df["partition"] = "train"
df.loc[split_index:, "partition"] = "test"
df["start_month"] = df["start_time"].dt.to_period("M").astype(str)

print("=" * 75)
print("MONTHLY DATA DISTRIBUTION")
print("=" * 75)

monthly = df.groupby("start_month").agg(
    applications=("case:concept:name", "size"),
    accepted_rate=("Accepted", "mean"),
    median_duration_hours=("duration_hours", "median"),
    zero_credit_score_rate=("CreditScore", lambda s: s.eq(0).mean()),
).reset_index()

monthly["accepted_rate_pct"] = monthly["accepted_rate"] * 100
monthly["zero_credit_score_pct"] = monthly["zero_credit_score_rate"] * 100

print(monthly[[
    "start_month",
    "applications",
    "accepted_rate_pct",
    "median_duration_hours",
    "zero_credit_score_pct",
]].round(2).to_string(index=False))

print("\n" + "=" * 75)
print("TRAIN VS TEST DISTRIBUTION")
print("=" * 75)

comparison = df.groupby("partition").agg(
    applications=("case:concept:name", "size"),
    accepted_rate=("Accepted", "mean"),
    median_duration_hours=("duration_hours", "median"),
    median_requested_amount=("case:RequestedAmount", "median"),
    zero_credit_score_rate=("CreditScore", lambda s: s.eq(0).mean()),
    start_date_min=("start_time", "min"),
    start_date_max=("start_time", "max"),
).reset_index()

comparison["accepted_rate_pct"] = comparison["accepted_rate"] * 100
comparison["zero_credit_score_pct"] = (
    comparison["zero_credit_score_rate"] * 100
)

print(comparison[[
    "partition",
    "applications",
    "start_date_min",
    "start_date_max",
    "accepted_rate_pct",
    "median_duration_hours",
    "median_requested_amount",
    "zero_credit_score_pct",
]].round(2).to_string(index=False))

output = DATA_DIR / "temporal_drift_analysis.csv"
monthly.to_csv(output, index=False)
print("\nSaved monthly analysis:", output)
