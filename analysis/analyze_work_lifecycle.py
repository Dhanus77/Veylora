
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
lifecycle_col = "lifecycle:transition"
timestamp_col = "time:timestamp"

required = {
    case_col,
    activity_col,
    lifecycle_col,
    timestamp_col,
}

missing = required - set(events.columns)
if missing:
    raise ValueError(f"Missing columns: {sorted(missing)}")

events[timestamp_col] = pd.to_datetime(
    events[timestamp_col],
    errors="coerce",
    utc=True,
)

events = events.dropna(
    subset=[case_col, activity_col, lifecycle_col, timestamp_col]
).copy()

# Restrict this analysis to work activities.
work = events[
    events[activity_col].astype(str).str.startswith("W_")
].copy()

# Count each lifecycle state per activity.
profile = (
    work.groupby([activity_col, lifecycle_col])
    .agg(
        records=(case_col, "size"),
        applications=(case_col, "nunique"),
    )
    .reset_index()
)

profile_wide = profile.pivot(
    index=activity_col,
    columns=lifecycle_col,
    values="records",
).fillna(0)

profile_wide.columns = [
    f"records_{column}" for column in profile_wide.columns
]

# Count distinct applications per work activity.
case_activity = (
    work.groupby([case_col, activity_col, lifecycle_col])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

for state in [
    "schedule",
    "start",
    "suspend",
    "resume",
    "complete",
    "ate_abort",
    "withdraw",
]:
    if state not in case_activity.columns:
        case_activity[state] = 0

# Aggregate across applications for each activity.
summary = case_activity.groupby(activity_col).agg(
    applications=(case_col, "nunique"),
    total_schedules=("schedule", "sum"),
    total_starts=("start", "sum"),
    total_suspends=("suspend", "sum"),
    total_resumes=("resume", "sum"),
    total_completions=("complete", "sum"),
    total_aborts=("ate_abort", "sum"),
    total_withdrawals=("withdraw", "sum"),
)

summary["abort_to_start_ratio"] = (
    summary["total_aborts"]
    / summary["total_starts"].replace(0, pd.NA)
)

summary["suspend_to_start_ratio"] = (
    summary["total_suspends"]
    / summary["total_starts"].replace(0, pd.NA)
)

summary = summary.reset_index().merge(
    profile_wide.reset_index(),
    on=activity_col,
    how="left",
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
output_path = OUTPUT_DIR / "work_lifecycle_summary.csv"
summary.to_csv(output_path, index=False)

print("\n=== WORK ACTIVITY LIFECYCLE SUMMARY ===")
print(
    summary.sort_values("total_aborts", ascending=False)
    .head(20)
    .round(3)
    .to_string(index=False)
)

print(f"\nSaved to: {output_path}")
print(
    "\nInterpretation caution: lifecycle event counts are not necessarily "
    "one-to-one with work-item instances. Ratios above 1 may occur when "
    "a work item is suspended or resumed multiple times."
)
