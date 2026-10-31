import pytest

from flowlens.causal_engine import estimate_randomized_effect
from flowlens.process_simulator import simulate_loan_process


def test_simulator_generates_expected_data():
    data, metadata = simulate_loan_process(n_applications=1000, seed=42)

    assert len(data) == 1000
    assert data["application_id"].is_unique
    assert set(data["treatment"].unique()) == {0, 1}
    assert set(data["accepted"].unique()).issubset({0, 1})
    assert metadata["simulation"] is True


def test_causal_engine_recovers_simulated_delay_effect():
    data, metadata = simulate_loan_process(
        n_applications=10000,
        true_delay_reduction_hours=12,
        seed=42,
    )

    result = estimate_randomized_effect(
        data,
        treatment="treatment",
        outcome="processing_duration_hours",
    )

    assert result.effect == pytest.approx(
        metadata["true_effect_hours"],
        abs=1.5,
    )
    assert result.confidence_interval[0] < 0
    assert result.confidence_interval[1] < 0


def test_intervention_does_not_materially_change_acceptance():
    data, _ = simulate_loan_process(n_applications=20000, seed=42)

    result = estimate_randomized_effect(
        data,
        treatment="treatment",
        outcome="accepted",
    )

    # The simulated intervention has no direct acceptance effect.
    assert abs(result.effect) < 0.03


def test_simulator_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        simulate_loan_process(n_applications=2)

    with pytest.raises(ValueError):
        simulate_loan_process(true_delay_reduction_hours=-1)
