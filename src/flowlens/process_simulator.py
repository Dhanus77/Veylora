"""Controlled synthetic loan-process simulator for causal validation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_loan_process(
    n_applications: int = 3000,
    true_delay_reduction_hours: float = 12.0,
    seed: int = 42,
) -> tuple[pd.DataFrame, dict]:
    """Generate a randomized loan-process experiment with known effects.

    Treatment represents an operational intervention that reduces a simulated
    waiting interval. Assignment is randomized at application level.

    The intervention has no direct effect on acceptance probability in this
    data-generating process. These are synthetic assumptions, not historical
    BPI 2017 findings.
    """
    if n_applications < 4:
        raise ValueError("At least four applications are required.")

    if not np.isfinite(true_delay_reduction_hours):
        raise ValueError("The intervention effect must be finite.")

    if true_delay_reduction_hours < 0:
        raise ValueError("The delay reduction cannot be negative.")

    rng = np.random.default_rng(seed)

    application_id = np.arange(1, n_applications + 1)

    complexity = rng.choice(
        ["low", "medium", "high"],
        size=n_applications,
        p=[0.35, 0.45, 0.20],
    )

    complexity_hours = pd.Series(complexity).map({
        "low": 0.0,
        "medium": 30.0,
        "high": 75.0,
    }).to_numpy()

    requested_amount = rng.lognormal(
        mean=np.log(15000),
        sigma=0.55,
        size=n_applications,
    )

    # Randomized assignment at application level.
    treatment = rng.integers(0, 2, size=n_applications)

    baseline_duration = (
        100.0
        + complexity_hours
        + 0.0008 * requested_amount
        + rng.normal(0, 18, size=n_applications)
    )

    treatment_effect = -true_delay_reduction_hours * treatment
    processing_duration = np.maximum(
        1.0,
        baseline_duration + treatment_effect,
    )

    # Acceptance depends on application characteristics, not treatment.
    complexity_penalty = pd.Series(complexity).map({
        "low": 0.0,
        "medium": 0.25,
        "high": 0.60,
    }).to_numpy()

    amount_penalty = np.log1p(requested_amount / 15000) * 0.15

    acceptance_probability = 1 / (
        1 + np.exp(-(
            1.1 - complexity_penalty - amount_penalty
        ))
    )

    accepted = rng.binomial(1, acceptance_probability)

    data = pd.DataFrame({
        "application_id": application_id,
        "complexity": complexity,
        "requested_amount": requested_amount.round(2),
        "treatment": treatment,
        "processing_duration_hours": processing_duration.round(4),
        "accepted": accepted,
        "acceptance_probability": acceptance_probability.round(6),
    })

    metadata = {
        "simulation": True,
        "seed": seed,
        "applications": n_applications,
        "treatment_name": "Process-delay intervention",
        "outcome_name": "processing_duration_hours",
        "true_effect_hours": -float(true_delay_reduction_hours),
        "acceptance_effect": 0.0,
        "assignment": "Randomized at application level",
        "data_generating_assumption": (
            "The intervention reduces simulated processing duration by a fixed "
            "amount and does not directly change acceptance probability."
        ),
        "warning": (
            "Synthetic experiment. Its known effects validate the analysis "
            "pipeline; they are not evidence of real-world business impact."
        ),
    }

    return data, metadata
