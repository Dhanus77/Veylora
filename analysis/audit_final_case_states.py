
from pathlib import Path
import pandas as pd
from pm4py.objects.log.importer.xes import importer as xes_importer

BASE_DIR = Path(__file__).resolve().parent
RAW_LOG = BASE_DIR / "data" / "raw" / "sampled-log.xml"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

if not RAW_LOG.exists():
    raise FileNotFoundError(f"Raw event log not found: {RAW_LOG}")

print("Loading original event log...")
log = xes_importer.apply(str(RAW_LOG))

rows = []

for trace in log:
    events = list(trace)
    if not events:
        continue

    case_id = str(events[0].get("case:concept:name", trace.attributes.get("concept:name", "")))

    normalized = []
    for index, event in enumerate(events):
        timestamp = pd.to_datetime(
            event.get("time:timestamp"), utc=True, errors="coerce"
        )
        normalized.append({
            "case_id": case_id,
            "activity": str(event.get("concept:name", "UNKNOWN")).strip(),
            "lifecycle": str(event.get("lifecycle:transition", "UNKNOWN")).strip().lower(),
            "timestamp": timestamp,
            "original_order": index,
        })

    event_df = pd.DataFrame(normalized)
    event_df = event_df.sort_values(
        ["timestamp", "original_order"], kind="stable", na_position="last"
    )

    first_event = event_df.iloc[0]
    last_event = event_df.iloc[-1]

    # Count all lifecycle records for each application.
    activity_lifecycle_counts = (
        event_df.groupby(["activity", "lifecycle"])
        .size()
        .to_dict()
    )

    rows.append({
        "case:concept:name": case_id,
        "first_activity": first_event["activity"],
        "first_lifecycle": first_event["lifecycle"],
        "last_activity": last_event["activity"],
        "last_lifecycle": last_event["lifecycle"],
        "last_timestamp": last_event["timestamp"],
        "event_records": len(event_df),
        "complete_records": int(event_df["lifecycle"].eq("complete").sum()),
        "suspend_records": int(event_df["lifecycle"].eq("suspend").sum()),
        "resume_records": int(event_df["lifecycle"].eq("resume").sum()),
    })

result = pd.DataFrame(rows)

case_data_path = PROCESSED_DIR / "case_level_dataset.csv"
case_data = pd.read_csv(case_data_path)

merged = result.merge(
    case_data[["case:concept:name", "Accepted", "duration_hours"]],
    on="case:concept:name",
    how="left",
    validate="one_to_one",
)

output_path = PROCESSED_DIR / "final_case_states.csv"
merged.to_csv(output_path, index=False)

print("\n" + "=" * 75)
print("FINAL RECORDED STATES")
print("=" * 75)

print("\nMost common final activity/lifecycle combinations:")
print(
    merged.groupby(["last_activity", "last_lifecycle"])
    .size()
    .sort_values(ascending=False)
    .head(25)
    .to_string()
)

print("\nFinal activity/lifecycle combinations by Accepted field:")
print(
    merged.groupby(
        ["last_activity", "last_lifecycle", "Accepted"],
        dropna=False,
    ).size().sort_values(ascending=False).head(30).to_string()
)

print("\nAccepted field by final lifecycle state:")
print(pd.crosstab(
    merged["Accepted"],
    merged["last_lifecycle"],
    dropna=False,
).to_string())

print("\nApplications with a final suspend/resume/start/schedule/abort state:")
unfinished = merged[
    merged["last_lifecycle"].isin(
        ["suspend", "resume", "start", "schedule", "ate_abort"]
    )
]
print("Count:", len(unfinished))
print(unfinished[
    [
        "case:concept:name",
        "last_activity",
        "last_lifecycle",
        "Accepted",
        "duration_hours",
    ]
].head(15).to_string(index=False))

print("\nSaved:", output_path)
print(
    "\nCaution: the last recorded event is not necessarily the true business "
    "outcome. The observation window may end before the application is resolved."
)
