import numpy as np
import pandas as pd
import pytest

from flowlens.causal_engine import (
    estimate_randomized_effect,
    historical_identification_assessment,
)


def test_randomized_estimator_recovers_known_effect():
    rng = np.random.default_rng(42)
    n = 5000
    treatment = rng.integers(0, 2, size=n)
    noise = rng.normal(0, 10, size=n)

    frame = pd.DataFrame({
        "treatment": treatment,
        "delay": 100 - 12 * treatment + noise,
    })

    result = estimate_randomized_effect(frame, "treatment", "delay")

    assert result.effect == pytest.approx(-12, abs=1.0)
    assert result.confidence_interval[0] < result.effect
    assert result.confidence_interval[1] > result.effect
    assert result.p_value < 0.05
    assert result.identification.startswith("Randomized assignment")


def test_estimator_rejects_non_binary_treatment():
    frame = pd.DataFrame({
        "treatment": [0, 1, 2, 0],
        "delay": [10, 8, 9, 11],
    })

    with pytest.raises(ValueError, match="binary"):
        estimate_randomized_effect(frame, "treatment", "delay")


def test_estimator_rejects_small_groups():
    frame = pd.DataFrame({
        "treatment": [0, 1, 1],
        "delay": [10, 8, 9],
    })

    with pytest.raises(ValueError, match="two valid observations"):
        estimate_randomized_effect(frame, "treatment", "delay")


def test_historical_data_is_not_misrepresented_as_causal():
    result = historical_identification_assessment()

    assert result["status"] == "not_identified"
    assert result["causal_effect_established"] is False
