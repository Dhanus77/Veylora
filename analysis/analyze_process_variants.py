
from pathlib import Path
import pandas as pd
import pm4py

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "data" / "raw" / "sampled-log.xml"
OUTPUT_DIR = ROOT / "data" / "processed"

CASE_COL = "case:concept:name"
ACTIVITY_COL = "concept:name"
TIME_COL = "time:timestamp"
LIFECYCLE_COL = "lifecycle:transition"


def main():
    print("Loading event log...")
    log = pm4py.read_xes(str(LOG_PATH))
    events = pm4py.convert_to_dataframe(log)

    required = {CASE_COL, ACTIVITY_COL, TIME_COL, LIFECYCLE_COL}
    missing = required - set(events.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    events[TIME_COL] = pd.to_datetime(
        events[TIME_COL], errors="coerce", utc=True
    )

    events = events.dropna(
        subset=[CASE_COL, ACTIVITY_COL, TIME_COL]
    ).copy()

    # Initial variant definition:
    # retain records marked complete, then order them by timestamp.
    completed = events[
        events[LIFECYCLE_COL].astype(str).str.lower() == "complete"
    ].copy()

    completed = completed.sort_values(
        [CASE_COL, TIME_COL], kind="stable"
    )

    # Build one ordered activity sequence per application.
    case_sequences = (
        completed.groupby(CASE_COL, sort=False)[ACTIVITY_COL]
        .agg(tuple)
        .rename("activity_sequence")
        .reset_index()
    )

    # Identify unique sequences and how frequently they occur.
    variant_counts = (
        case_sequences.groupby("activity_sequence")
        .size()
        .rename("application_count")
        .reset_index()
    )

    variant_counts = variant_counts.sort_values(
        "application_count", ascending=False
    ).reset_index(drop=True)

    variant_counts["variant_id"] = [
        f"V{i:03d}" for i in range(1, len(variant_counts) + 1)
    ]

    variant_counts["activity_count"] = (
        variant_counts["activity_sequence"].apply(len)
    )

    variant_counts["activity_path"] = (
        variant_counts["activity_sequence"].apply(
            lambda sequence: " -> ".join(sequence)
        )
    )

    total_applications = len(case_sequences)
    unique_variants = len(variant_counts)

    variant_counts["application_share_pct"] = (
        variant_counts["application_count"]
        / total_applications * 100
    )

    # Save detailed variant information.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    detail_path = OUTPUT_DIR / "process_variants.csv"
    summary_path = OUTPUT_DIR / "process_variant_summary.csv"

    variant_counts[
        [
            "variant_id",
            "application_count",
            "application_share_pct",
            "activity_count",
            "activity_path",
        ]
    ].to_csv(detail_path, index=False)

    top_n = min(15, unique_variants)
    top_variants = variant_counts.head(top_n).copy()

    top_coverage = (
        top_variants["application_count"].sum()
        / total_applications * 100
    )

    summary = pd.DataFrame([{
        "applications_with_completed_events": total_applications,
        "unique_completed_event_variants": unique_variants,
        "top_5_variant_coverage_pct": (
            variant_counts.head(5)["application_count"].sum()
            / total_applications * 100
        ),
        "top_15_variant_coverage_pct": top_coverage,
    }])

    summary.to_csv(summary_path, index=False)

    print("\n=== PROCESS VARIANT SUMMARY ===")
    print(summary.round(2).to_string(index=False))

    print("\n=== TOP PROCESS VARIANTS ===")
    print(
        top_variants[
            [
                "variant_id",
                "application_count",
                "application_share_pct",
                "activity_count",
                "activity_path",
            ]
        ].to_string(index=False)
    )

    print(f"\nDetailed variants saved to: {detail_path}")
    print(f"Summary saved to: {summary_path}")

    print(
        "\nCaveat: variants use complete lifecycle records only. "
        "They do not capture the full sequence of scheduled, started, "
        "suspended, resumed, aborted, or withdrawn work."
    )


if __name__ == "__main__":
    main()
