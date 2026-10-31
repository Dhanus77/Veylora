
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

df = pd.read_csv(DATA_DIR / "case_level_dataset.csv")

print("=" * 75)
print("1. CREDIT SCORE DATA QUALITY")
print("=" * 75)

if "CreditScore" in df.columns:
    scores = pd.to_numeric(df["CreditScore"], errors="coerce")
    zero_mask = scores.eq(0)
    missing_mask = scores.isna()

    print(f"Total applications: {len(df):,}")
    print(f"Zero scores: {zero_mask.sum():,} ({zero_mask.mean() * 100:.2f}%)")
    print(f"Missing scores: {missing_mask.sum():,}")

    for label, mask in [
        ("Score is zero", zero_mask),
        ("Score is nonzero", scores.notna() & ~zero_mask),
        ("Score is missing", missing_mask),
    ]:
        durations = pd.to_numeric(
            df.loc[mask, "duration_hours"], errors="coerce"
        ).dropna()

        print(
            f"{label}: cases={int(mask.sum())}, "
            f"median_duration_hours="
            f"{durations.median():.2f}" if len(durations) else
            f"{label}: cases={int(mask.sum())}, no duration data"
        )

print("\n" + "=" * 75)
print("2. OUTCOME EVENT OVERLAP")
print("=" * 75)

outcomes = {
    "Application cancelled": "activity_count__A_Cancelled",
    "Application denied": "activity_count__A_Denied",
    "Application completed": "activity_count__A_Complete",
    "Offer accepted": "activity_count__O_Accepted",
    "Offer cancelled": "activity_count__O_Cancelled",
    "Offer refused": "activity_count__O_Refused",
    "Offer returned": "activity_count__O_Returned",
}

available = {label: col for label, col in outcomes.items() if col in df.columns}

flags = pd.DataFrame({
    label: pd.to_numeric(df[col], errors="coerce").fillna(0).gt(0)
    for label, col in available.items()
}, index=df.index)

print("\nApplications containing each event:")
for label in flags.columns:
    print(f"{label}: {int(flags[label].sum()):,}")

print("\nApplications with multiple outcome-related events:")
event_total = flags.sum(axis=1)
for n in sorted(event_total.unique()):
    print(f"{int(n)} event types: {int(event_total.eq(n).sum()):,} applications")

print("\nPairwise event overlaps:")
for i, first in enumerate(flags.columns):
    for second in flags.columns[i + 1:]:
        overlap = flags[first] & flags[second]
        if overlap.any():
            print(
                f"{first} + {second}: {int(overlap.sum())} applications"
            )

print("\n" + "=" * 75)
print("3. ACCEPTED FIELD VS EVENT INDICATORS")
print("=" * 75)

accepted = (
    df["Accepted"].astype(str).str.strip().str.lower()
    .map({"true": True, "false": False})
)

for label, col in available.items():
    present = pd.to_numeric(df[col], errors="coerce").fillna(0).gt(0)

    print(f"\n{label}")
    print(pd.crosstab(
        accepted,
        present,
        rownames=["Accepted field"],
        colnames=["Event present"],
        dropna=False
    ).to_string())

print("\n" + "=" * 75)
print("4. DATA AUDIT COMPLETE")
print("=" * 75)
print("No labels were modified. This script only audits the data.")
