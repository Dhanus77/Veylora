from pathlib import Path
import shutil

import pandas as pd
import pm4py


ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "data" / "raw" / "sampled-log.xml"
OUT_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUT_DIR / "case_level_dataset.csv"
BACKUP_PATH = OUT_DIR / "case_level_dataset_before_last_accepted.csv"

CASE = "case:concept:name"
ACTIVITY = "concept:name"
TIME = "time:timestamp"
LIFECYCLE = "lifecycle:transition"


print("Loading event log...")
if not LOG_PATH.exists():
    raise FileNotFoundError(f"Event log not found: {LOG_PATH}")

log = pm4py.read_xes(str(LOG_PATH))
df = pm4py.convert_to_dataframe(log)

required_columns = [CASE, ACTIVITY, TIME]
missing_columns = [column for column in required_columns if column not in df.columns]
if missing_columns:
    raise ValueError(f"Required event-log columns are missing: {missing_columns}")

df[TIME] = pd.to_datetime(df[TIME], errors="coerce")
df = df.dropna(subset=[CASE, ACTIVITY, TIME]).copy()

# Stable sorting preserves original event order when timestamps are identical.
df = df.sort_values([CASE, TIME], kind="mergesort").reset_index(drop=True)


# ---------------------------------------------------------------------
# Application-level features
# ---------------------------------------------------------------------
cases = (
    df.groupby(CASE)
    .agg(
        start_time=(TIME, "min"),
        end_time=(TIME, "max"),
        event_count=(ACTIVITY, "size"),
        unique_activities=(ACTIVITY, "nunique"),
    )
    .reset_index()
)

cases["duration_hours"] = (
    cases["end_time"] - cases["start_time"]
).dt.total_seconds() / 3600


# ---------------------------------------------------------------------
# Case attributes
# Keep the original first-non-null approach for the other attributes.
# Accepted is handled separately below because it changes over time.
# ---------------------------------------------------------------------
attributes = [
    "case:LoanGoal",
    "case:RequestedAmount",
    "case:ApplicationType",
    "CreditScore",
    "OfferedAmount",
    "MonthlyCost",
    "NumberOfTerms",
    "FirstWithdrawalAmount",
]

available = [column for column in attributes if column in df.columns]

for column in available:
    values = df.groupby(CASE, sort=False)[column].agg(
        lambda series: series.dropna().iloc[0]
        if series.notna().any()
        else None
    )
    cases[column] = cases[CASE].map(values)


# ---------------------------------------------------------------------
# Acceptance target
# The audit established that every Accepted record belongs to
# O_Create Offer [complete]. Use the LAST such recorded value per case.
# ---------------------------------------------------------------------
if "Accepted" in df.columns:
    accepted_events = df.dropna(subset=["Accepted"]).copy()

    if accepted_events.empty:
        raise ValueError(
            "The event log contains no non-null Accepted values. "
            "The case-level dataset was not written."
        )

    # Guard against silently changing the target's event definition.
    if not (accepted_events[ACTIVITY] == "O_Create Offer").all():
        unexpected = (
            accepted_events.loc[
                accepted_events[ACTIVITY] != "O_Create Offer", ACTIVITY
            ]
            .value_counts()
            .to_dict()
        )
        raise ValueError(
            "Accepted values were found outside O_Create Offer. "
            f"Unexpected activities: {unexpected}. Dataset was not written."
        )

    if LIFECYCLE in accepted_events.columns:
        if not (accepted_events[LIFECYCLE] == "complete").all():
            unexpected = (
                accepted_events.loc[
                    accepted_events[LIFECYCLE] != "complete", LIFECYCLE
                ]
                .value_counts()
                .to_dict()
            )
            raise ValueError(
                "Accepted values were found on unexpected lifecycle events. "
                f"Unexpected lifecycle values: {unexpected}. "
                "Dataset was not written."
            )

    # Since the full event log is stably sorted by case and timestamp,
    # tail(1) selects the last recorded Accepted value per application.
    last_accepted = (
        accepted_events.groupby(CASE, sort=False)
        .tail(1)
        .set_index(CASE)["Accepted"]
    )

    cases["Accepted"] = cases[CASE].map(last_accepted)

    missing_targets = int(cases["Accepted"].isna().sum())
    if missing_targets:
        raise ValueError(
            f"{missing_targets} applications have no Accepted target. "
            "Dataset was not written."
        )

    # Report how many applications would differ from the old first-value rule.
    first_accepted = (
        accepted_events.groupby(CASE, sort=False)["Accepted"]
        .first()
    )
    first_aligned = cases[CASE].map(first_accepted)
    changed_targets = int(
        (first_aligned.astype(str) != cases["Accepted"].astype(str)).sum()
    )
else:
    changed_targets = None
    print("WARNING: Accepted column is absent; no acceptance target was created.")


# ---------------------------------------------------------------------
# Event activity counts per application
# These are full-case descriptive counts, not intake-time model features.
# ---------------------------------------------------------------------
activity_pivot = pd.crosstab(df[CASE], df[ACTIVITY])
activity_pivot.columns = [
    "activity_count__" + str(activity).replace(" ", "_")
    for activity in activity_pivot.columns
]

cases = cases.merge(
    activity_pivot,
    left_on=CASE,
    right_index=True,
    how="left",
    validate="one_to_one",
)


# ---------------------------------------------------------------------
# Preserve the current dataset before replacing it.
# The first backup is retained and is not overwritten on later runs.
# ---------------------------------------------------------------------
if OUTPUT_PATH.exists():
    if not BACKUP_PATH.exists():
        shutil.copy2(OUTPUT_PATH, BACKUP_PATH)
        print(f"\nExisting dataset backed up to: {BACKUP_PATH}")
    else:
        print(
            "\nBackup already exists; it will not be overwritten: "
            f"{BACKUP_PATH}"
        )

cases.to_csv(OUTPUT_PATH, index=False)


# ---------------------------------------------------------------------
# Build report
# ---------------------------------------------------------------------
print("\n=== CASE-LEVEL DATASET ===")
print(f"Applications: {len(cases):,}")
print(f"Columns: {len(cases.columns)}")
print(f"Saved to: {OUTPUT_PATH}")

print("\n=== ATTRIBUTE AVAILABILITY ===")
for column in available:
    print(
        f"{column}: "
        f"{cases[column].notna().sum():,} / {len(cases):,} applications populated"
    )

print("\n=== ACCEPTANCE TARGET AUDIT ===")
if "Accepted" in cases.columns:
    print("Target definition: last recorded O_Create Offer [complete] value")
    print(f"Applications changed from first-value target: {changed_targets:,}")
    print("Last Accepted value counts:")
    print(cases["Accepted"].value_counts(dropna=False).to_string())

print("\n=== DURATION SUMMARY (HOURS) ===")
print(cases["duration_hours"].describe().round(2))

print("\n=== SAMPLE CASES ===")
print(cases.head(5).to_string(index=False))

print("\nCase-level dataset built successfully.")
