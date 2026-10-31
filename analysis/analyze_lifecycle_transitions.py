
from pathlib import Path
import pandas as pd
import pm4py

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "data" / "raw" / "sampled-log.xml"
OUTPUT_DIR = ROOT / "data" / "processed"

CASE = "case:concept:name"
ACTIVITY = "concept:name"
LIFECYCLE = "lifecycle:transition"
TIMESTAMP = "time:timestamp"


def main():
    print("Loading event log...")
    log = pm4py.read_xes(str(LOG_PATH))
    events = pm4py.convert_to_dataframe(log)

    required = {CASE, ACTIVITY, LIFECYCLE, TIMESTAMP}
    missing = required - set(events.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    events[TIMESTAMP] = pd.to_datetime(
        events[TIMESTAMP], errors="coerce", utc=True
    )
    events = events.dropna(
        subset=[CASE, ACTIVITY, LIFECYCLE, TIMESTAMP]
    ).copy()

    events[ACTIVITY] = (
        events[ACTIVITY].astype(str).str.strip()
    )
    events[LIFECYCLE] = (
        events[LIFECYCLE].astype(str).str.strip().str.lower()
    )

    # Preserve deterministic ordering when timestamps tie.
    events["_original_order"] = range(len(events))
    events = events.sort_values(
        [CASE, TIMESTAMP, "_original_order"], kind="stable"
    )

    # Construct consecutive event-record transitions within each case.
    events["next_activity"] = events.groupby(CASE)[ACTIVITY].shift(-1)
    events["next_lifecycle"] = events.groupby(CASE)[LIFECYCLE].shift(-1)
    events["next_timestamp"] = events.groupby(CASE)[TIMESTAMP].shift(-1)

    events["gap_hours"] = (
        events["next_timestamp"] - events[TIMESTAMP]
    ).dt.total_seconds() / 3600

    transitions = events.dropna(
        subset=[
            "next_activity",
            "next_lifecycle",
            "gap_hours",
        ]
    ).copy()

    # Negative gaps should not occur after sorting; flag them rather
    # than silently using them in waiting-time summaries.
    negative_gaps = int((transitions["gap_hours"] < 0).sum())
    transitions = transitions[transitions["gap_hours"] >= 0].copy()

    transitions["from_state"] = (
        transitions[ACTIVITY] + " [" + transitions[LIFECYCLE] + "]"
    )
    transitions["to_state"] = (
        transitions["next_activity"]
        + " ["
        + transitions["next_lifecycle"]
        + "]"
    )

    transitions["transition"] = (
        transitions["from_state"] + " -> " + transitions["to_state"]
    )

    # Aggregate transition frequency and gap distribution.
    summary = (
        transitions.groupby(
            ["from_state", "to_state", "transition"],
            dropna=False,
        )
        .agg(
            transition_count=("gap_hours", "size"),
            median_gap_hours=("gap_hours", "median"),
            mean_gap_hours=("gap_hours", "mean"),
            p90_gap_hours=("gap_hours", lambda s: s.quantile(0.90)),
            max_gap_hours=("gap_hours", "max"),
            applications=(CASE, "nunique"),
        )
        .reset_index()
    )

    # Save all transitions, including rare ones.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_path = OUTPUT_DIR / "lifecycle_transition_gaps.csv"
    summary.to_csv(all_path, index=False)

    # For interpretation, focus on transitions observed at least
    # 20 times. This threshold is a practical screening choice.
    common = summary[summary["transition_count"] >= 20].copy()

    frequent_path = OUTPUT_DIR / "lifecycle_transition_summary.csv"
    common.sort_values(
        "transition_count", ascending=False
    ).to_csv(frequent_path, index=False)

    print(f"\nEvent records used: {len(events)}")
    print(f"Consecutive transitions analysed: {len(transitions)}")
    print(f"Negative gaps excluded: {negative_gaps}")
    print(f"Distinct transition types: {len(summary)}")
    print(f"Transitions with at least 20 observations: {len(common)}")

    print("\n=== 15 MOST FREQUENT TRANSITIONS ===")
    print(
        common.sort_values(
            "transition_count", ascending=False
        ).head(15)[
            [
                "transition",
                "transition_count",
                "applications",
                "median_gap_hours",
                "mean_gap_hours",
                "p90_gap_hours",
            ]
        ].round(2).to_string(index=False)
    )

    print("\n=== 15 LONGEST MEDIAN GAPS: COMMON TRANSITIONS ===")
    print(
        common.sort_values(
            "median_gap_hours", ascending=False
        ).head(15)[
            [
                "transition",
                "transition_count",
                "applications",
                "median_gap_hours",
                "mean_gap_hours",
                "p90_gap_hours",
            ]
        ].round(2).to_string(index=False)
    )

    print(f"\nAll transition statistics saved to: {all_path}")
    print(f"Common transition summary saved to: {frequent_path}")

    print(
        "\nCaution: these are elapsed gaps between consecutive event records. "
        "They are not direct measurements of staff work time, queue time, "
        "or causal bottlenecks. Lifecycle states must be interpreted "
        "according to the event-log semantics."
    )


if __name__ == "__main__":
    main()
