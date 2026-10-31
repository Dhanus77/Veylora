
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
path = ROOT / "data" / "processed" / "case_level_dataset.csv"
df = pd.read_csv(path)

print("\n=== DURATION DISTRIBUTION (HOURS) ===")
print(
    df["duration_hours"]
    .quantile([0, .1, .25, .5, .75, .9, .95, .99, 1])
    .round(2)
)

print("\n=== TARGET SKEWNESS ===")
print(round(df["duration_hours"].skew(), 3))

print("\n=== CORRELATION WITH DURATION ===")
numeric = [
    "duration_hours",
    "case:RequestedAmount",
    "event_count",
    "unique_activities",
]
print(df[numeric].corr().round(3).to_string())

print("\n=== APPLICATION ATTRIBUTE DIVERSITY ===")
for column in ["case:LoanGoal", "case:ApplicationType"]:
    print(f"\n{column}:")
    print(df[column].value_counts(dropna=False).head(10).to_string())

print("\n=== COMPLETION TIME BY ACCEPTANCE ===")
if "Accepted" in df.columns:
    print(
        df.groupby("Accepted")["duration_hours"]
        .agg(["count", "median", "mean"])
        .round(2)
    )
