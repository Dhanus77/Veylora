"""Causal analysis utilities for controlled process interventions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CausalEstimate:
    treatment: str
    outcome: str
    estimand: str
    control_mean: float
    treatment_mean: float
    effect: float
    standard_error: float
    confidence_interval: tuple[float, float]
    p_value: float
    control_count: int
    treatment_count: int
    identification: str
    assumptions: tuple[str, ...]
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def estimate_randomized_effect(
    data: pd.DataFrame,
    treatment: str,
    outcome: str,
    confidence_level: float = 0.95,
) -> CausalEstimate:
    """Estimate an intention-to-treat effect from a randomized binary treatment.

    Effect is treatment mean minus control mean. A negative estimate is
    beneficial when the outcome is a delay or cost.
    """
    if treatment not in data.columns or outcome not in data.columns:
        raise ValueError("Treatment and outcome columns must exist.")

    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1.")

    frame = data[[treatment, outcome]].copy()
    frame[treatment] = pd.to_numeric(frame[treatment], errors="coerce")
    frame[outcome] = pd.to_numeric(frame[outcome], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna()

    if not frame[treatment].isin([0, 1]).all():
        raise ValueError("Treatment must contain only binary values 0 and 1.")

    control = frame.loc[frame[treatment] == 0, outcome].astype(float)
    treated = frame.loc[frame[treatment] == 1, outcome].astype(float)

    if len(control) < 2 or len(treated) < 2:
        raise ValueError("At least two valid observations per group are required.")

    control_mean = float(control.mean())
    treatment_mean = float(treated.mean())
    effect = treatment_mean - control_mean

    control_var = float(control.var(ddof=1))
    treatment_var = float(treated.var(ddof=1))
    standard_error = float(
        np.sqrt(control_var / len(control) + treatment_var / len(treated))
    )

    # Welch-Satterthwaite degrees of freedom.
    numerator = (control_var / len(control) + treatment_var / len(treated)) ** 2
    denominator = (
        (control_var / len(control)) ** 2 / (len(control) - 1)
        + (treatment_var / len(treated)) ** 2 / (len(treated) - 1)
    )
    degrees_freedom = numerator / denominator if denominator > 0 else float("inf")

    try:
        from scipy.stats import t

        alpha = 1 - confidence_level
        critical = float(t.ppf(1 - alpha / 2, degrees_freedom))
        statistic = effect / standard_error if standard_error > 0 else 0.0
        p_value = float(2 * t.sf(abs(statistic), degrees_freedom))
    except ImportError as exc:
        raise RuntimeError("SciPy is required for confidence intervals.") from exc

    interval = (
        float(effect - critical * standard_error),
        float(effect + critical * standard_error),
    )

    return CausalEstimate(
        treatment=treatment,
        outcome=outcome,
        estimand="Average treatment effect (intention-to-treat)",
        control_mean=control_mean,
        treatment_mean=treatment_mean,
        effect=float(effect),
        standard_error=standard_error,
        confidence_interval=interval,
        p_value=p_value,
        control_count=len(control),
        treatment_count=len(treated),
        identification="Randomized assignment; estimate applies to this experiment.",
        assumptions=(
            "Treatment assignment was randomized.",
            "Treatment and outcome are consistently defined.",
            "One unit's treatment does not affect another unit's outcome.",
            "Missing outcomes do not introduce differential selection bias.",
        ),
        interpretation=(
            "Treatment minus control. A negative effect indicates a reduction "
            "in the measured outcome; a positive effect indicates an increase."
        ),
    )


def historical_identification_assessment() -> dict[str, Any]:
    """Return the current evidence boundary for the historical BPI dataset."""
    return {
        "dataset": "BPI 2017 historical event log",
        "status": "not_identified",
        "reason": (
            "The available historical analysis does not establish randomized "
            "intervention assignment or sufficient control of time-varying and "
            "unobserved confounding."
        ),
        "causal_effect_established": False,
        "permitted_use": "Descriptive analysis and hypothesis generation.",
        "prohibited_interpretation": (
            "Do not report historical associations or hypothetical scenario "
            "reductions as established intervention effects."
        ),
    }
