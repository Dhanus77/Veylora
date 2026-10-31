
from pathlib import Path
import pandas as pd
import pm4py

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "data" / "raw" / "sampled-log.xml"

print("Loading event log...")
log = pm4py.read_xes(str(LOG_PATH))
events = pm4py.convert_to_dataframe(log)

case_col = "case:concept:name"
activity_col = "concept:name"
lifecycle_col = "lifecycle:transition"
timestamp_col = "time:timestamp"

print("\n=== LIFECYCLE VALUES ===")
print(events[lifecycle_col].value_counts(dropna=False).to_string())

print("\n=== LIFECYCLE BY ACTIVITY ===")
print(
    pd.crosstab(
        events[activity_col],
        events[lifecycle_col],
        dropna=False,
    )
    .sort_values(by=events[lifecycle_col].value_counts().index.tolist(),
                 ascending=False)
    .head(15)
    .to_string()
)

print("\n=== RAW RECORDS FOR W_COMPLETE APPLICATION ===")
columns = [
    column for column in [
        case_col,
        activity_col,
        lifecycle_col,
        timestamp_col,
        "EventID",
    ]
    if column in events.columns
]

sample_case = (
    events.loc[
        events[activity_col] == "W_Complete application",
        case_col,
    ]
    .dropna()
    .iloc[0]
)

sample = events[
    (events[case_col] == sample_case)
    & (events[activity_col] == "W_Complete application")
].sort_values(timestamp_col)

print(f"Sample application: {sample_case}")
print(sample[columns].to_string(index=False))

print("\n=== DISTINCT ACTIVITY COUNTS FOR SAMPLE CASE ===")
print(
    sample.groupby(
        [activity_col, lifecycle_col],
        dropna=False,
    )
    .size()
    .to_string()
)
