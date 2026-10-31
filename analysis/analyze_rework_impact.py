
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "processed"

COMPLETED_PATH = DATA_DIR / "completed_activity_counts.csv"
CASE_PATH = DATA_DIR / "case_level_dataset.csv"

# Keep the original output untouched during validation.
OUTPUT_PATH = DATA_DIR / "rework_impact_summary_corrected.csv"

CASE_COL = "case:concept:name"
ACTIVITY_COL = "concept:name"

SELECTED_ACTIVITIES = [
    "W_Validate application",
    "W_Call incomplete files",
    "W_Call after offers",
    "W_Complete application",
]


def main():
    completed = pd.read_csv(COMPLETED_PATH)
    cases = pd.read_csv(CASE_PATH)

    required_completed = {
        CASE_COL,
        ACTIVITY_COL,
        "completed_instances",
    }
    required_cases = {
        CASE_COL,
        "duration_hours",
        "Accepted",
    }

    if not required_completed.issubset(completed.columns):
        raise ValueError(
            f"Missing completed-count columns: "
            f"{required_completed - set(completed.columns)}"
        )

    if not required_cases.issubset(cases.columns):
        raise ValueError(
            f"Missing case columns: "
            f"{required_cases - set(cases.columns)}"
        )

    if cases[CASE_COL].duplicated().any():
        raise ValueError("Case-level dataset contains duplicate applications.")

    if completed.duplicated([CASE_COL, ACTIVITY_COL]).any():
        raise ValueError(
            "Completed activity data contains duplicate "
            "application/activity pairs."
        )

    completed["completed_instances"] = pd.to_numeric(
        completed["completed_instances"],
        errors="coerce",
    )

    if completed["completed_instances"].isna().any():
        raise ValueError("Completed-instance counts contain missing values.")

    if (completed["completed_instances"] < 1).any():
        raise ValueError("Completed-instance counts must be at least one.")

    # Keep only the selected activities.
    selected = completed[
        completed[ACTIVITY_COL].isin(SELECTED_ACTIVITIES)
    ].copy()

    # Create one column per activity, with completed execution counts.
    counts = selected.pivot(
        index=CASE_COL,
        columns=ACTIVITY_COL,
        values="completed_instances",
    )

    counts = counts.reindex(columns=SELECTED_ACTIVITIES)
    counts = counts.fillna(0)

    # Merge with all applications so applications without a completed
    # instance of a selected activity are classified as zero.
    df = cases.merge(
        counts,
        left_on=CASE_COL,
        right_index=True,
        how="left",
        validate="one_to_one",
    )

    df[SELECTED_ACTIVITIES] = (
        df[SELECTED_ACTIVITIES].fillna(0)
    )

    df["duration_hours"] = pd.to_numeric(
        df["duration_hours"],
        errors="coerce",
    )

    summary_rows = []

    for activity in SELECTED_ACTIVITIES:
        repeat_count = (df[activity] - 1).clip(lower=0)
        has_repeats = repeat_count > 0

        for repeated, group_name in [
            (False, "No repeats"),
            (True, "Has repeats"),
        ]:
            group = df.loc[has_repeats == repeated].copy()

            if group.empty:
                continue

            accepted = (
                group["Accepted"]
                .astype(str)
                .str.strip()
                .str.lower()
                .isin(["true", "1", "yes"])
            )

            summary_rows.append({
                "activity_repeat_column": f"repeats_{activity}",
                "group": group_name,
                "applications": len(group),
                "median_duration_hours": (
                    group["duration_hours"].median()
                ),
                "mean_duration_hours": (
                    group["duration_hours"].mean()
                ),
                "accepted_count": int(accepted.sum()),
                "acceptance_rate_pct": (
                    accepted.mean() * 100
                ),
                "median_repeat_count": (
                    repeat_count.loc[group.index].median()
                ),
            })

    summary = pd.DataFrame(summary_rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_PATH, index=False)

    print("Completed-execution-based rework impact analysis")
    print("Applications:", len(df))
    print("Output:", OUTPUT_PATH)

    print("\n=== REPEATS VS APPLICATION OUTCOMES ===")
    print(summary.round(2).to_string(index=False))

    print(
        "\nDefinition: repeats are completed executions "
        "beyond the first completed execution per application "
        "and activity."
    )
    print(
        "Interpretation: these are descriptive associations, "
        "not proof that repeated activities cause longer durations "
        "or change acceptance outcomes."
    )


if __name__ == "__main__":
    main()
