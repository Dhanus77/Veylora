
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

INPUT = DATA_DIR / "process_improvement_candidates.csv"
OUTPUT = DATA_DIR / "process_optimization_scenarios.csv"

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing candidate file: {INPUT}\n"
        "Run rank_process_improvements.py first."
    )

df = pd.read_csv(INPUT)

required = [
    "transition",
    "transition_count",
    "applications",
    "median_gap_hours",
    "p90_gap_hours",
    "screening_score",
    "candidate_type",
]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

for col in [
    "transition_count",
    "applications",
    "median_gap_hours",
    "p90_gap_hours",
    "screening_score",
]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=[
    "transition_count",
    "applications",
    "median_gap_hours",
]).copy()

# Keep the top 10 candidates for the initial scenario report.
# These are investigation candidates, not proven bottlenecks.
candidates = df.sort_values(
    "screening_score", ascending=False
).head(10).copy()

# User-configurable hypothetical reductions.
reduction_scenarios = [0.10, 0.20, 0.30]

rows = []

for _, candidate in candidates.iterrows():
    count = int(candidate["transition_count"])
    median_gap = float(candidate["median_gap_hours"])
    p90_gap = float(candidate["p90_gap_hours"])

    for reduction in reduction_scenarios:
        new_median = median_gap * (1 - reduction)
        new_p90 = p90_gap * (1 - reduction)

        # Aggregate illustration across observed transition occurrences.
        # This is NOT per-case savings and does not account for overlap,
        # causal feasibility, or downstream effects.
        illustrative_hours = count * median_gap * reduction

        rows.append({
            "transition": candidate["transition"],
            "transition_count": count,
            "applications": int(candidate["applications"]),
            "candidate_type": candidate["candidate_type"],
            "scenario_reduction_pct": reduction * 100,
            "baseline_median_gap_hours": round(median_gap, 2),
            "hypothetical_median_gap_hours": round(new_median, 2),
            "baseline_p90_gap_hours": round(p90_gap, 2),
            "hypothetical_p90_gap_hours": round(new_p90, 2),
            "illustrative_aggregate_hours_reduced": round(
                illustrative_hours, 2
            ),
        })

results = pd.DataFrame(rows)
results.to_csv(OUTPUT, index=False)

print("=" * 95)
print("PROCESS OPTIMIZATION — WHAT-IF SCENARIOS")
print("=" * 95)
print("Candidates simulated:", len(candidates))
print("Reduction assumptions:", reduction_scenarios)

for reduction in reduction_scenarios:
    scenario = results[
        results["scenario_reduction_pct"] == reduction * 100
    ]

    print(f"\n--- Hypothetical {int(reduction * 100)}% reduction ---")
    print(
        scenario[[
            "transition",
            "transition_count",
            "baseline_median_gap_hours",
            "hypothetical_median_gap_hours",
            "illustrative_aggregate_hours_reduced",
        ]].to_string(index=False)
    )

print("\nSaved:", OUTPUT)
print(
    "\nIMPORTANT INTERPRETATION LIMITS:\n"
    "1. Reductions are user-defined assumptions, not measured effects.\n"
    "2. Elapsed gaps are not confirmed queue time or staff work time.\n"
    "3. Aggregate hours are calculated over transition occurrences; "
    "they are not unique-case savings or end-to-end duration reductions.\n"
    "4. Transition occurrences can overlap within the same application.\n"
    "5. Do not sum these estimates across transitions to claim total savings."
)
