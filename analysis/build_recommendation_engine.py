
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "processed"
OUTPUT = DATA / "improvement_recommendations.csv"

CANDIDATES_FILE = DATA / "process_improvement_candidates.csv"
TRANSITIONS_FILE = DATA / "lifecycle_transition_summary.csv"
SCENARIOS_FILE = DATA / "process_optimization_scenarios.csv"
CASES_FILE = DATA / "case_level_dataset.csv"
VARIANTS_FILE = DATA / "case_variant_mapping.csv"


def load_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)


def find_column(df, candidates, description):
    for name in candidates:
        if name in df.columns:
            return name
    raise ValueError(
        f"Could not find {description}. "
        f"Available columns: {list(df.columns)}"
    )


def main():
    candidates = load_csv(CANDIDATES_FILE)
    transitions = load_csv(TRANSITIONS_FILE)
    scenarios = load_csv(SCENARIOS_FILE)
    cases = load_csv(CASES_FILE)
    variants = load_csv(VARIANTS_FILE)

    # Resolve the column names from the actual source files.
    transition_col = find_column(
        candidates, ["transition"], "transition column"
    )
    count_col = find_column(
        candidates, ["transition_count"], "transition count"
    )
    median_col = find_column(
        candidates,
        ["median_gap_hours", "baseline_median_gap_hours"],
        "median gap column",
    )
    p90_col = find_column(
        candidates, ["p90_gap_hours"], "90th percentile gap column"
    )
    score_col = find_column(
        candidates, ["screening_score", "score"],
        "candidate screening score"
    )

    transition_key = find_column(
        transitions, ["transition"], "transition key"
    )
    transition_median = find_column(
        transitions, ["median_gap_hours"], "transition median gap"
    )
    transition_p90 = find_column(
        transitions, ["p90_gap_hours"], "transition p90 gap"
    )
    transition_apps = find_column(
        transitions, ["applications"], "application count"
    )

    # Use a consistent transition key to attach detailed gap statistics.
    evidence = candidates.merge(
        transitions[
            [transition_key, transition_median, transition_p90, transition_apps]
        ].rename(
            columns={
                transition_key: transition_col,
                transition_median: "verified_median_gap_hours",
                transition_p90: "verified_p90_gap_hours",
                transition_apps: "applications_observed",
            }
        ),
        on=transition_col,
        how="left",
        validate="many_to_one",
    )

    # Outcome context is descriptive only; these flags do not prove causality.
    activity_counts = [
        c for c in cases.columns
        if c.startswith("activity_count__")
    ]

    def activity_count(name):
        col = f"activity_count__{name}"
        if col not in cases.columns:
            return None
        return pd.to_numeric(cases[col], errors="coerce").fillna(0)

    outcome_flags = {
        "cases_with_application_cancellation":
            activity_count("A_Cancelled"),
        "cases_with_application_denial":
            activity_count("A_Denied"),
        "cases_with_offer_cancellation":
            activity_count("O_Cancelled"),
        "cases_with_offer_refusal":
            activity_count("O_Refused"),
    }

    outcome_summary = {}
    for label, values in outcome_flags.items():
        if values is not None:
            outcome_summary[label] = int((values > 0).sum())

    total_cases = len(cases)
    accepted_col = "Accepted" if "Accepted" in cases.columns else None
    if accepted_col:
        accepted_rate = (
            cases[accepted_col].astype(str).str.lower()
            .isin(["true", "1", "yes"]).mean()
        )
    else:
        accepted_rate = np.nan

    # Variant concentration helps describe how diverse the observed process is.
    variant_col = find_column(
        variants, ["variant_id"], "variant ID"
    )
    variant_count = variants[variant_col].nunique()

    rows = []
    for _, row in evidence.iterrows():
        transition = str(row[transition_col])
        lower = transition.lower()

        count = pd.to_numeric(row[count_col], errors="coerce")
        median_gap = pd.to_numeric(
            row.get("verified_median_gap_hours", row[median_col]),
            errors="coerce",
        )
        p90_gap = pd.to_numeric(
            row.get("verified_p90_gap_hours", row[p90_col]),
            errors="coerce",
        )
        score = pd.to_numeric(row[score_col], errors="coerce")
        applications = pd.to_numeric(
            row.get("applications_observed", np.nan),
            errors="coerce",
        )

        if pd.isna(count) or pd.isna(median_gap):
            evidence_quality = "Needs data validation"
        elif count < 20 or (
            not pd.isna(applications) and applications < 20
        ):
            evidence_quality = "Low sample size"
        else:
            evidence_quality = "Descriptive evidence; causality untested"

        if "a_cancelled" in lower or "o_cancelled" in lower:
            recommendation_type = "Outcome pathway investigation"
            action = (
                "Inspect case timelines and business rules to determine "
                "whether cancellation was expected, customer-driven, or "
                "associated with an avoidable process delay."
            )
        elif "suspend" in lower and "resume" in lower:
            recommendation_type = "Suspension and follow-up investigation"
            action = (
                "Sample cases with long suspend-to-resume gaps. Check "
                "whether they reflect customer response time, scheduled "
                "follow-up, missing information, or internal delay."
            )
        elif "ate_abort" in lower:
            recommendation_type = "Aborted work-item investigation"
            action = (
                "Inspect the surrounding lifecycle records and case outcome "
                "before deciding whether the abort was expected or avoidable."
            )
        else:
            recommendation_type = "Handoff and elapsed-gap investigation"
            action = (
                "Review representative case timelines and validate what "
                "the transition means with a process owner."
            )

        rows.append({
            "transition": transition,
            "transition_count": count,
            "applications_observed": applications,
            "median_gap_hours": median_gap,
            "p90_gap_hours": p90_gap,
            "screening_score": score,
            "recommendation_type": recommendation_type,
            "recommended_investigation": action,
            "evidence_quality": evidence_quality,
            "causal_effect_established": False,
            "confirmed_queue_time": False,
            "scenario_reduction_is_assumption": True,
        })

    result = pd.DataFrame(rows)

    # High score is useful for screening, not proof of business value.
    result = result.sort_values(
        ["screening_score", "transition_count"],
        ascending=[False, False],
        na_position="last",
    ).reset_index(drop=True)

    result.insert(0, "priority_rank", range(1, len(result) + 1))
    result["dataset_case_count"] = total_cases
    result["dataset_variant_count"] = variant_count
    result["dataset_accepted_rate_descriptive"] = accepted_rate

    for label, value in outcome_summary.items():
        result[label] = value

    result["interpretation_warning"] = (
        "Elapsed event-log gaps are not confirmed queue or work time. "
        "Rank is a screening heuristic. Recommendations require case review "
        "and process-owner validation; no causal impact is established."
    )

    DATA.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False)

    print("=" * 90)
    print("PROCESS IMPROVEMENT RECOMMENDATION ENGINE")
    print("=" * 90)
    print(f"Cases in source dataset: {total_cases}")
    print(f"Distinct process variants: {variant_count}")
    print(f"Candidates ranked: {len(result)}")
    print(f"Descriptive accepted rate: {accepted_rate:.2%}")
    print("\nOutcome event context (cases may overlap):")
    for label, value in outcome_summary.items():
        print(f"  {label}: {value}")

    print("\nTop 10 investigation priorities:")
    display_cols = [
        "priority_rank",
        "transition",
        "transition_count",
        "median_gap_hours",
        "p90_gap_hours",
        "recommendation_type",
        "evidence_quality",
    ]
    print(result[display_cols].head(10).to_string(index=False))

    print(f"\nSaved recommendations: {OUTPUT}")
    print("\nInterpretation:")
    print("- These are investigation priorities, not proven root causes.")
    print("- Scenario reductions remain hypothetical.")
    print("- Outcome event counts can overlap and must not be added together.")


if __name__ == "__main__":
    main()
