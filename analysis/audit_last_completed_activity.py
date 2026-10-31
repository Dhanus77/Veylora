
from pathlib import Path
import pandas as pd
from pm4py.objects.log.importer.xes import importer as xes_importer

BASE_DIR = Path(__file__).resolve().parent
RAW_LOG = BASE_DIR / "data" / "raw" / "sampled-log.xml"
OUT_DIR = BASE_DIR / "data" / "processed"

print("Loading event log...")
log = xes_importer.apply(str(RAW_LOG))

rows = []

for trace in log:
    events = []

    for index, event in enumerate(trace):
        timestamp = pd.to_datetime(
            event.get("time:timestamp"), utc=True, errors="coerce"
        )
        events.append({
            "case_id": str(
                event.get(
                    "case:concept:name",
                    trace.attributes.get("concept:name", "")
                )
            ),
            "activity": str(event.get("concept:name", "UNKNOWN")).strip(),
            "lifecycle": str(
                event.get("lifecycle:transition", "UNKNOWN")
            ).strip().lower(),
            "timestamp": timestamp,
            "original_order": index,
        })

    if not events:
        continue

    event_df = pd.DataFrame(events).sort_values(
        ["timestamp", "original_order"],
        kind="stable",
        na_position="last",
    )

    completed = event_df[event_df["lifecycle"] == "complete"]

    if completed.empty:
        last_completed_activity = None
        last_completed_timestamp = pd.NaT
    else:
        last_completed = completed.iloc[-1]
        last_completed_activity = last_completed["activity"]
        last_completed_timestamp = last_completed["timestamp"]

    last_recorded = event_df.iloc[-1]

    rows.append({
        "case:concept:name": event_df.iloc[0]["case_id"],
        "last_completed_activity": last_completed_activity,
        "last_completed_timestamp": last_completed_timestamp,
        "last_recorded_activity": last_recorded["activity"],
        "last_recorded_lifecycle": last_recorded["lifecycle"],
        "event_count": len(event_df),
    })

result = pd.DataFrame(rows)

case_data = pd.read_csv(OUT_DIR / "case_level_dataset.csv")
result = result.merge(
    case_data[["case:concept:name", "Accepted", "duration_hours"]],
    on="case:concept:name",
    how="left",
    validate="one_to_one",
)

output = OUT_DIR / "last_completed_activity_audit.csv"
result.to_csv(output, index=False)

print("\n" + "=" * 75)
print("MOST COMMON LAST COMPLETED ACTIVITIES")
print("=" * 75)

print(
    result["last_completed_activity"]
    .value_counts(dropna=False)
    .head(25)
    .to_string()
)

print("\n" + "=" * 75)
print("LAST COMPLETED ACTIVITY BY ACCEPTED FIELD")
print("=" * 75)

print(
    result.groupby(
        ["last_completed_activity", "Accepted"],
        dropna=False,
    )
    .size()
    .sort_values(ascending=False)
    .head(35)
    .to_string()
)

print("\n" + "=" * 75)
print("LAST COMPLETED ACTIVITY VS LAST RECORDED LIFECYCLE")
print("=" * 75)

print(
    result.groupby(
        ["last_completed_activity", "last_recorded_lifecycle"],
        dropna=False,
    )
    .size()
    .sort_values(ascending=False)
    .head(25)
    .to_string()
)

print("\nSaved:", output)
print(
    "\nReminder: the last completed activity is not automatically "
    "the final business outcome."
)
