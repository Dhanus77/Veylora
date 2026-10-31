"""Small deterministic analytics functions with explicit metric definitions."""

from __future__ import annotations

import numpy as np
import pandas as pd


def parse_boolean_series(series: pd.Series) -> pd.Series:
    """Parse common CSV boolean encodings; unknown values become NA."""
    mapping = {
        "true": True, "1": True, "yes": True, "y": True,
        "false": False, "0": False, "no": False, "n": False,
    }
    normalized = series.astype("string").str.strip().str.lower()
    return normalized.map(mapping).astype("boolean")


def overview_metrics(cases: pd.DataFrame) -> dict[str, float | int | None]:
    """Calculate transparent case-level overview metrics.

    Acceptance rate excludes rows where Accepted cannot be parsed as a boolean.
    Duration quantiles are computed from finite numeric durations only.
    """
    if cases.empty:
        return {
            "case_count": 0,
            "event_count": 0,
            "acceptance_rate": None,
            "median_duration_hours": None,
            "mean_duration_hours": None,
            "p90_duration_hours": None,
            "invalid_duration_count": 0,
        }

    event_count = pd.to_numeric(cases["event_count"], errors="coerce")
    durations = pd.to_numeric(cases["duration_hours"], errors="coerce")
    durations = durations[np.isfinite(durations) & (durations >= 0)]
    accepted = parse_boolean_series(cases["Accepted"]).dropna()

    return {
        "case_count": int(len(cases)),
        "event_count": int(event_count.fillna(0).sum()),
        "acceptance_rate": float(accepted.mean()) if not accepted.empty else None,
        "median_duration_hours": float(durations.median()) if not durations.empty else None,
        "mean_duration_hours": float(durations.mean()) if not durations.empty else None,
        "p90_duration_hours": float(durations.quantile(0.90)) if not durations.empty else None,
        "invalid_duration_count": int(len(cases) - len(durations)),
    }


def validate_recommendations(recommendations: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with stable numeric fields and an evidence warning.

    No causal effect or financial savings is inferred by this function.
    """
    out = recommendations.copy()
    aliases = {
        "priority_rank": ["priority_rank", "rank"],
        "transition_count": ["transition_count", "count"],
        "median_gap_hours": ["median_gap_hours", "verified_median_gap_hours", "baseline_median_gap_hours"],
        "p90_gap_hours": ["p90_gap_hours", "verified_p90_gap_hours"],
        "screening_score": ["screening_score", "score"],
    }
    for target, candidates in aliases.items():
        if target not in out.columns:
            for candidate in candidates:
                if candidate in out.columns:
                    out[target] = out[candidate]
                    break
        if target in out.columns:
            out[target] = pd.to_numeric(out[target], errors="coerce")
    if "transition" not in out.columns:
        out["transition"] = "Unlabelled transition"
    if "interpretation_warning" not in out.columns:
        out["interpretation_warning"] = (
            "Exploratory ranking only; elapsed gaps are not verified queue time "
            "and causal effects have not been established."
        )
    return out


def simulate_gap_reduction(
    frame: pd.DataFrame,
    reduction_percent: int,
    *,
    max_rows: int | None = None,
) -> pd.DataFrame:
    """Apply a hypothetical percentage reduction to each transition median.

    `illustrative_hours_across_occurrences` is provided only for auditability.
    It must not be summed or described as realised, unique-case, or end-to-end savings.
    """
    if not 0 <= reduction_percent <= 50:
        raise ValueError("reduction_percent must be between 0 and 50")

    out = validate_recommendations(frame)
    required = {"transition_count", "median_gap_hours"}
    missing = required - set(out.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))

    if "screening_score" in out.columns:
        out = out.sort_values("screening_score", ascending=False, na_position="last")
    if max_rows is not None:
        if max_rows < 1:
            raise ValueError("max_rows must be positive")
        out = out.head(max_rows).copy()

    factor = reduction_percent / 100.0
    out["assumed_reduction_percent"] = reduction_percent
    out["hypothetical_median_gap_hours"] = out["median_gap_hours"] * (1 - factor)
    out["illustrative_hours_across_occurrences"] = (
        out["transition_count"] * out["median_gap_hours"] * factor
    )
    out["savings_verified"] = False
    return out.reset_index(drop=True)
