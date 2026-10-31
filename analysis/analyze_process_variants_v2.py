
from pathlib import Path
import re
import pandas as pd
import pm4py

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "data" / "raw" / "sampled-log.xml"
OUTPUT_DIR = ROOT / "data" / "processed"

CASE_COL = "case:concept:name"
ACTIVITY_COL = "concept:name"
TIME_COL = "time:timestamp"
LIFECYCLE_COL = "lifecycle:transition"


def normalize_activity(value):
    """Normalize whitespace without merging different activity names."""
    return re.sub(r"\s+", " ", str(value)).strip()


def main():
    print("Loading event log...")
    log = pm4py.read_xes(str(LOG_PATH))
    events = pm4py.convert_to_dataframe(log)

    required = {CASE_COL, ACTIVITY_COL, TIME_COL, LIFECYCLE_COL}
    missing = required - set(events.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    events[TIME_COL] = pd.to_datetime(
        events[TIME_COL], errors="coerce", utc=True
    )

    events = events.dropna(
        subset=[CASE_COL, ACTIVITY_COL, TIME_COL]
    ).copy()

    # Preserve original labels so we can audit normalization.
    events["activity_original"] = events[ACTIVITY_COL].astype(str)
    events["activity_normalized"] = (
        events["activity_original"].map(normalize_activity)
    )

    print("\n=== ACTIVITY LABEL NORMALIZATION ===")
    label_audit = (
        events.groupby("activity_normalized")["activity_original"]
        .nunique()
        .sort_values(ascending=False)
    )
    print(label_audit[label_audit > 1].to_string())

    completed = events[
        events[LIFECYCLE_COL].astype(str).str.lower() == "complete"
    ].copy()

    completed = completed.sort_values(
        [CASE_COL, TIME_COL], kind="stable"
    )

    case_sequences = (
        completed.groupby(CASE_COL, sort=False)["activity_normalized"]
        .agg(tuple)
        .rename("activity_sequence")
        .reset_index()
    )

    # Keep the case-to-variant mapping for downstream analysis.
    variant_counts = (
        case_sequences.groupby("activity_sequence")
        .size()
        .rename("application_count")
        .reset_index()
        .sort_values("application_count", ascending=False)
        .reset_index(drop=True)
    )

    variant_counts["variant_id"] = [
        f"V{i:03d}" for i in range(1, len(variant_counts) + 1)
    ]

    variant_counts["activity_count"] = (
        variant_counts["activity_sequence"].map(len)
    )
    variant_counts["activity_path"] = (
        variant_counts["activity_sequence"].map(
            lambda seq: " -> ".join(seq)
        )
    )

    total_cases = len(case_sequences)
    unique_variants = len(variant_counts)

    variant_counts["application_share_pct"] = (
        variant_counts["application_count"] / total_cases * 100
    )

    case_mapping = case_sequences.merge(
        variant_counts[["activity_sequence", "variant_id"]],
        on="activity_sequence",
        how="left",
        validate="many_to_one",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    variants_path = OUTPUT_DIR / "process_variants_v2.csv"
    mapping_path = OUTPUT_DIR / "case_variant_mapping.csv"
    summary_path = OUTPUT_DIR / "process_variant_summary_v2.csv"

    variant_counts[
        [
            "variant_id",
            "application_count",
            "application_share_pct",
            "activity_count",
            "activity_path",
        ]
    ].to_csv(variants_path, index=False)

    case_mapping[
        [CASE_COL, "variant_id", "activity_sequence"]
    ].assign(
        activity_path=lambda x: x["activity_sequence"].map(
            lambda seq: " -> ".join(seq)
        )
    ).drop(columns=["activity_sequence"]).to_csv(
        mapping_path, index=False
    )

    summary = pd.DataFrame([{
        "applications_with_completed_events": total_cases,
        "unique_completed_event_variants": unique_variants,
        "top_5_variant_coverage_pct": (
            variant_counts.head(5)["application_count"].sum()
            / total_cases * 100
        ),
        "top_15_variant_coverage_pct": (
            variant_counts.head(15)["application_count"].sum()
            / total_cases * 100
        ),
    }])

    summary.to_csv(summary_path, index=False)

    print("\n=== NORMALIZED PROCESS VARIANT SUMMARY ===")
    print(summary.round(2).to_string(index=False))

    print("\n=== TOP 15 NORMALIZED VARIANTS ===")
    print(
        variant_counts.head(15)[
            [
                "variant_id",
                "application_count",
                "application_share_pct",
                "activity_count",
                "activity_path",
            ]
        ].to_string(index=False)
    )

    print(f"\nSaved variants: {variants_path}")
    print(f"Saved case mapping: {mapping_path}")
    print(f"Saved summary: {summary_path}")


if __name__ == "__main__":
    main()
