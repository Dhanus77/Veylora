
from pathlib import Path
import pandas as pd
import pm4py

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "data" / "raw" / "sampled-log.xml"
OUTPUT_DIR = ROOT / "data" / "processed"

print("Loading event log...")
log = pm4py.read_xes(str(LOG_PATH))
events = pm4py.convert_to_dataframe(log)

case_col = "case:concept:name"
activity_col = "concept:name"
timestamp_col = "time:timestamp"

required = {case_col, activity_col, timestamp_col}
missing = required - set(events.columns)

if missing:
    raise ValueError(f"Missing required columns: {sorted(missing)}")

events[timestamp_col] = pd.to_datetime(
    events[timestamp_col], errors="coerce", utc=True
)

events = events.dropna(
    subset=[case_col, activity_col, timestamp_col]
).copy()

events = events.sort_values([case_col, timestamp_col])

# Count how often each activity appears in each application.
activity_counts = (
    events.groupby([case_col, activity_col])
    .size()
    .unstack(fill_value=0)
)

# Summarize repeated activity counts per application.
repeat_summary = pd.DataFrame(index=activity_counts.index)
repeat_summary["total_events"] = activity_counts.sum(axis=1)
repeat_summary["unique_activities"] = (
    (activity_counts > 0).sum(axis=1)
)

for activity in [
    "W_Validate application",
    "W_Call incomplete files",
    "W_Call after offers",
    "W_Complete application",
]:
    if activity in activity_counts.columns:
        repeat_summary[
            f"count_{activity}"
        ] = activity_counts[activity]

        repeat_summary[
            f"repeats_{activity}"
        ] = (activity_counts[activity] - 1).clip(lower=0)

repeat_summary = repeat_summary.reset_index()

# Export application-level counts.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
case_output = OUTPUT_DIR / "case_rework_statistics.csv"
repeat_summary.to_csv(case_output, index=False)

print("\n=== REPEATED ACTIVITY SUMMARY ===")

repeat_columns = [
    column for column in repeat_summary.columns
    if column.startswith("repeats_")
]

for column in repeat_columns:
    values = repeat_summary[column]
    print(f"\n{column}")
    print(f"Applications with repeats: {(values > 0).sum()}")
    print(f"Total extra occurrences: {values.sum()}")
    print(f"Maximum extra occurrences in one application: {values.max()}")

print("\n=== APPLICATIONS WITH MOST RECORDED EVENTS ===")
print(
    repeat_summary.sort_values("total_events", ascending=False)
    .head(10)
    .to_string(index=False)
)

print(f"\nSaved application-level results to: {case_output}")
