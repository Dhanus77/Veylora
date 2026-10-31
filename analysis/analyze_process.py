
from pathlib import Path
import pandas as pd
import pm4py

PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "raw" / "sampled-log.xml"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading event log...")
log = pm4py.read_xes(str(DATA_PATH))
df = pm4py.convert_to_dataframe(log)

CASE = "case:concept:name"
ACTIVITY = "concept:name"
TIMESTAMP = "time:timestamp"

required = [CASE, ACTIVITY, TIMESTAMP]
missing = [col for col in required if col not in df.columns]

if missing:
    raise ValueError(f"Required columns missing: {missing}")

df[TIMESTAMP] = pd.to_datetime(df[TIMESTAMP], errors="coerce")
df = df.dropna(subset=required)
df = df.sort_values([CASE, TIMESTAMP]).reset_index(drop=True)

# 1. Activity frequency
activity_counts = (
    df[ACTIVITY]
    .value_counts()
    .rename_axis("activity")
    .reset_index(name="event_count")
)
activity_counts.to_csv(OUTPUT_DIR / "activity_counts.csv", index=False)

# 2. Application-level statistics
case_stats = df.groupby(CASE).agg(
    start_time=(TIMESTAMP, "min"),
    end_time=(TIMESTAMP, "max"),
    event_count=(ACTIVITY, "size"),
    unique_activities=(ACTIVITY, "nunique"),
).reset_index()

case_stats["duration_hours"] = (
    case_stats["end_time"] - case_stats["start_time"]
).dt.total_seconds() / 3600

case_stats.to_csv(OUTPUT_DIR / "case_statistics.csv", index=False)

# 3. Activity-to-activity transitions within each application
df["next_activity"] = df.groupby(CASE)[ACTIVITY].shift(-1)

transitions = df.dropna(subset=["next_activity"])
transition_counts = (
    transitions.groupby([ACTIVITY, "next_activity"])
    .size()
    .reset_index(name="transition_count")
    .sort_values("transition_count", ascending=False)
)

transition_counts.to_csv(OUTPUT_DIR / "activity_transitions.csv", index=False)

# 4. Time between consecutive events in each application
df["previous_timestamp"] = df.groupby(CASE)[TIMESTAMP].shift(1)
df["wait_hours"] = (
    df[TIMESTAMP] - df["previous_timestamp"]
).dt.total_seconds() / 3600

wait_stats = (
    df.dropna(subset=["wait_hours"])
    .groupby(ACTIVITY)["wait_hours"]
    .agg(
        event_count="count",
        median_wait_hours="median",
        mean_wait_hours="mean",
    )
    .reset_index()
    .sort_values("median_wait_hours", ascending=False)
)

wait_stats.to_csv(OUTPUT_DIR / "activity_wait_statistics.csv", index=False)

# 5. Display findings
print("\n=== APPLICATION DURATION (ELAPSED TIME) ===")
print(case_stats["duration_hours"].describe().round(2))

print("\n=== TOP 10 ACTIVITIES ===")
print(activity_counts.head(10).to_string(index=False))

print("\n=== TOP 10 TRANSITIONS ===")
print(transition_counts.head(10).to_string(index=False))

print("\n=== ACTIVITIES WITH LONGEST MEDIAN EVENT GAPS ===")
print(wait_stats.head(10).round(2).to_string(index=False))

print(f"\nResults saved in: {OUTPUT_DIR}")
print("Analysis completed.")
