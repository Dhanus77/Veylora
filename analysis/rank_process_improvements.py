
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

INPUT = DATA_DIR / "lifecycle_transition_summary.csv"
OUTPUT = DATA_DIR / "process_improvement_candidates.csv"

if not INPUT.exists():
    raise FileNotFoundError(f"Missing transition summary: {INPUT}")

df = pd.read_csv(INPUT)

required = [
    "from_state",
    "to_state",
    "transition",
    "transition_count",
    "median_gap_hours",
    "p90_gap_hours",
    "applications",
]

missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

for col in [
    "transition_count",
    "median_gap_hours",
    "p90_gap_hours",
    "applications",
]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=[
    "transition_count",
    "median_gap_hours",
    "p90_gap_hours",
    "applications",
]).copy()

# Very frequent transitions with zero/negligible gaps may simply represent
# immediate event logging, not an actionable delay.
df["is_same_activity"] = (
    df["from_state"].str.extract(r"^(.*?) \[", expand=False)
    .eq(df["to_state"].str.extract(r"^(.*?) \[", expand=False))
)

df["gap_is_material"] = df["median_gap_hours"] >= 1.0

# Transparent screening score:
#  - log frequency prevents high-volume transitions dominating everything
#  - log median delay gives more weight to substantial observed gaps
# This is not estimated savings or a causal effect.
df["screening_score"] = (
    np.log1p(df["transition_count"])
    * np.log1p(df["median_gap_hours"].clip(lower=0))
)

# Mark potential event-state/terminal transitions for human review.
terminal_terms = [
    "A_Cancelled",
    "A_Denied",
    "O_Cancelled",
    "O_Refused",
    "ate_abort",
    "withdraw",
]

def needs_semantics_review(row):
    text = f"{row['from_state']} {row['to_state']}"
    return any(term.lower() in text.lower() for term in terminal_terms)

df["requires_semantics_review"] = df.apply(
    needs_semantics_review, axis=1
)

df["candidate_type"] = np.select(
    [
        df["requires_semantics_review"],
        df["is_same_activity"] & df["gap_is_material"],
        df["gap_is_material"],
    ],
    [
        "Outcome/lifecycle transition: verify meaning",
        "Same activity with material gap: inspect lifecycle semantics",
        "Material inter-activity gap: investigate process context",
    ],
    default="Low elapsed-gap priority: inspect only if operationally relevant",
)

# A first shortlist excludes zero/negligible median gaps.
shortlist = df[df["gap_is_material"]].copy()
shortlist = shortlist.sort_values(
    ["screening_score", "applications"],
    ascending=[False, False],
)

shortlist.to_csv(OUTPUT, index=False)

print("=" * 85)
print("TOP 20 PROCESS IMPROVEMENT CANDIDATES")
print("=" * 85)

columns = [
    "transition",
    "transition_count",
    "applications",
    "median_gap_hours",
    "p90_gap_hours",
    "screening_score",
    "candidate_type",
]

print(shortlist[columns].head(20).round(2).to_string(index=False))

print("\nTotal transition types evaluated:", len(df))
print("Transitions with median gap >= 1 hour:", len(shortlist))
print("Saved:", OUTPUT)

print(
    "\nInterpretation limits:\n"
    "- Elapsed gaps are not confirmed queue time or staff work time.\n"
    "- Repeated transitions from one application may not be independent.\n"
    "- The score is a screening heuristic, not predicted time savings.\n"
    "- Verify lifecycle and business semantics before proposing interventions."
)
