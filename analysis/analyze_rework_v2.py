
from pathlib import Path
import pandas as pd
import pm4py

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "data" / "raw" / "sampled-log.xml"
OUTPUT_DIR = ROOT / "data" / "processed"

print("Loading original event log...")
log = pm4py.read_xes(str(LOG_PATH))
events = pm4py.convert_to_dataframe(log)

case_col = "case:concept:name"
activity_col = "concept:name"
lifecycle_col = "lifecycle:transition"
timestamp_col = "time:timestamp"

required = {case_col, activity_col, lifecycle_col, timestamp_col}
missing = required - set(events.columns)

if missing:
    raise ValueError(f"Missing required columns: {sorted(missing)}")

events[timestamp_col] = pd.to_datetime(
    events[timestamp_col], errors="coerce", utc=True
)

print("\n=== LIFECYCLE COUNTS BY ACTIVITY TYPE ===")
print(
    events.groupby([activity_col, lifecycle_col])
    .size()
    .rename("records")
    .reset_index()
    .sort_values(["concept:name", "records"], ascending=[True, False])
    .head(40)
    .to_string(index=False)
)

# Keep all original events for lifecycle diagnostics.
# For this analysis, count complete records as completed activity instances.
completed = events[
    events[lifecycle_col].astype(str).str.lower() == "complete"
].copy()

completed = completed.dropna(
    subset=[case_col, activity_col, timestamp_col]
)

# Count completed instances per application and activity.
completed_counts = (
    completed.groupby([case_col, activity_col])
    .size()
    .rename("completed_instances")
    .reset_index()
)

completed_counts["extra_completed_instances"] = (
    completed_counts["completed_instances"] - 1
).clip(lower=0)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

detail_path = OUTPUT_DIR / "completed_activity_counts.csv"
completed_counts.to_csv(detail_path, index=False)

# Summarize the repeated completed instances by activity.
activity_summary = (
    completed_counts.groupby("concept:name")
    .agg(
        applications=("case:concept:name", "nunique"),
        total_completed_instances=("completed_instances", "sum"),
        applications_with_repeats=(
            "extra_completed_instances",
            lambda values: int((values > 0).sum()),
        ),
        total_extra_completed_instances=(
            "extra_completed_instances", "sum"
        ),
        max_extra_instances=("extra_completed_instances", "max"),
    )
    .reset_index()
    .sort_values("total_extra_completed_instances", ascending=False)
)

summary_path = OUTPUT_DIR / "rework_summary_v2.csv"
activity_summary.to_csv(summary_path, index=False)

print("\n=== COMPLETED-INSTANCE REWORK SUMMARY ===")
print(activity_summary.head(25).to_string(index=False))

print("\n=== LIFECYCLE COUNTS FOR SELECTED WORK ACTIVITIES ===")
selected = [
    "W_Validate application",
    "W_Call incomplete files",
    "W_Call after offers",
    "W_Complete application",
]

selected_events = events[events[activity_col].isin(selected)]

print(
    pd.crosstab(
        selected_events[activity_col],
        selected_events[lifecycle_col],
        dropna=False,
    ).to_string()
)

print(f"\nSaved detailed counts to: {detail_path}")
print(f"Saved activity summary to: {summary_path}")

print(
    "\nImportant: complete records are a proxy for completed activity "
    "instances. Validate the lifecycle semantics before treating every "
    "extra completed instance as unnecessary rework."
)
