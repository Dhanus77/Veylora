
from pathlib import Path

import pandas as pd
import pm4py


SOURCE = Path(
    r"D:\intern\BusinessProcessAI\data\raw\sampled-log.xml"
)

OUTPUT = Path(
    r"D:\intern\Veylora\data\processed\offer_level_dataset.csv"
)

print("Reading event log...")
df = pm4py.read_xes(str(SOURCE))

if not isinstance(df, pd.DataFrame):
    raise TypeError(
        f"Expected DataFrame from PM4Py, got {type(df)}"
    )

required = {
    "case:concept:name",
    "concept:name",
    "time:timestamp",
    "EventID",
    "OfferID",
}

missing = required - set(df.columns)
if missing:
    raise ValueError(f"Missing required columns: {sorted(missing)}")

df["time:timestamp"] = pd.to_datetime(
    df["time:timestamp"], utc=True, errors="coerce"
)

df["case:concept:name"] = (
    df["case:concept:name"].astype("string").str.strip()
)

# Offer creation events: EventID contains the offer identifier.
created = df.loc[
    df["concept:name"].eq("O_Create Offer")
].copy()

created["offer_id"] = (
    created["EventID"].astype("string").str.strip()
)

created = created.rename(
    columns={
        "time:timestamp": "offer_created_at",
        "case:concept:name": "application_id",
    }
)

# Offer resolution events: OfferID links back to the creation event.
resolved = df.loc[
    df["concept:name"].isin(["O_Accepted", "O_Cancelled"])
].copy()

resolved["offer_id"] = (
    resolved["OfferID"].astype("string").str.strip()
)

resolved = resolved.rename(
    columns={
        "time:timestamp": "offer_resolved_at",
        "case:concept:name": "application_id",
        "concept:name": "resolution_event",
    }
)

created = created.loc[
    created["offer_id"].notna()
    & created["offer_id"].ne("")
].copy()

resolved = resolved.loc[
    resolved["offer_id"].notna()
    & resolved["offer_id"].ne("")
].copy()

# Check uniqueness before joining.
duplicate_creations = created.duplicated(
    ["application_id", "offer_id"], keep=False
)

if duplicate_creations.any():
    raise ValueError(
        "Duplicate offer creation keys found. "
        "Do not continue until these are investigated."
    )

duplicate_resolutions = resolved.duplicated(
    ["application_id", "offer_id"], keep=False
)

if duplicate_resolutions.any():
    raise ValueError(
        "Multiple resolution events found for an offer. "
        "Do not silently choose one."
    )

# Keep the offer attributes recorded at creation.
attribute_columns = [
    "case:RequestedAmount",
    "case:ApplicationType",
    "case:LoanGoal",
    "CreditScore",
    "OfferedAmount",
    "MonthlyCost",
    "NumberOfTerms",
    "FirstWithdrawalAmount",
    "Selected",
    "Accepted",
]

available_attributes = [
    column for column in attribute_columns
    if column in created.columns
]

offer_data = created[
    [
        "application_id",
        "offer_id",
        "offer_created_at",
        *available_attributes,
    ]
].copy()

resolution_data = resolved[
    [
        "application_id",
        "offer_id",
        "offer_resolved_at",
        "resolution_event",
    ]
].copy()

offers = offer_data.merge(
    resolution_data,
    on=["application_id", "offer_id"],
    how="left",
    validate="one_to_one",
)

offers["outcome"] = offers["resolution_event"].map(
    {
        "O_Accepted": "accepted",
        "O_Cancelled": "cancelled",
    }
).fillna("unresolved")

offers["resolution_hours"] = (
    offers["offer_resolved_at"] - offers["offer_created_at"]
).dt.total_seconds() / 3600

# Sequence offers chronologically within each application.
offers = offers.sort_values(
    ["application_id", "offer_created_at", "offer_id"]
).reset_index(drop=True)

offers["offer_sequence"] = (
    offers.groupby("application_id").cumcount() + 1
)

# Negative resolution times indicate a linkage or timestamp problem.
negative_times = offers["resolution_hours"].dropna().lt(0)

if negative_times.any():
    raise ValueError(
        f"Found {negative_times.sum()} negative resolution durations."
    )

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
offers.to_csv(OUTPUT, index=False)

print("\nEXTRACTION COMPLETE")
print("Rows:", len(offers))
print("Applications:", offers["application_id"].nunique())
print("\nOutcome counts:")
print(offers["outcome"].value_counts(dropna=False))
print("\nMissing resolution timestamps:",
      offers["offer_resolved_at"].isna().sum())
print("\nOutput:", OUTPUT)
print("\nColumns:")
print(offers.columns.tolist())
