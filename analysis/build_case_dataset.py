
from pathlib import Path
import pandas as pd
import pm4py

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "data" / "raw" / "sampled-log.xml"
OUT_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading event log...")
log = pm4py.read_xes(str(LOG_PATH))
df = pm4py.convert_to_dataframe(log)

CASE = "case:concept:name"
ACTIVITY = "concept:name"
TIME = "time:timestamp"

df[TIME] = pd.to_datetime(df[TIME], errors="coerce")
df = df.dropna(subset=[CASE, ACTIVITY, TIME])
df = df.sort_values([CASE, TIME])

# Application-level features
cases = df.groupby(CASE).agg(
    start_time=(TIME, "min"),
    end_time=(TIME, "max"),
    event_count=(ACTIVITY, "size"),
    unique_activities=(ACTIVITY, "nunique"),
).reset_index()

cases["duration_hours"] = (
    cases["end_time"] - cases["start_time"]
).dt.total_seconds() / 3600

# First non-null value per case for attributes repeated across events
attributes = [
    "case:LoanGoal",
    "case:RequestedAmount",
    "case:ApplicationType",
    "Accepted",
    "CreditScore",
    "OfferedAmount",
    "MonthlyCost",
    "NumberOfTerms",
    "FirstWithdrawalAmount",
]

available = [c for c in attributes if c in df.columns]

for column in available:
    values = df.groupby(CASE)[column].agg(
        lambda s: s.dropna().iloc[0] if s.notna().any() else None
    )
    cases[column] = cases[CASE].map(values)

# Event activity counts per application
activity_pivot = pd.crosstab(df[CASE], df[ACTIVITY])
activity_pivot.columns = [
    "activity_count__" + str(c).replace(" ", "_")
    for c in activity_pivot.columns
]

cases = cases.merge(
    activity_pivot,
    left_on=CASE,
    right_index=True,
    how="left",
)

output = OUT_DIR / "case_level_dataset.csv"
cases.to_csv(output, index=False)

print("\n=== CASE-LEVEL DATASET ===")
print(f"Applications: {len(cases):,}")
print(f"Columns: {len(cases.columns)}")
print(f"Saved to: {output}")

print("\n=== ATTRIBUTE AVAILABILITY ===")
for column in available:
    print(
        f"{column}: "
        f"{cases[column].notna().sum():,} / {len(cases):,} applications populated"
    )

print("\n=== DURATION SUMMARY (HOURS) ===")
print(cases["duration_hours"].describe().round(2))

print("\n=== ACCEPTED VALUES ===")
if "Accepted" in cases.columns:
    print(cases["Accepted"].value_counts(dropna=False).head(10))

print("\n=== SAMPLE CASES ===")
print(cases.head(5).to_string(index=False))

print("\nCase-level dataset built successfully.")
