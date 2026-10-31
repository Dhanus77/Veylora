import pandas as pd
import pytest

from flowlens.analytics import overview_metrics, parse_boolean_series, simulate_gap_reduction, validate_recommendations


def test_overview_metrics_handles_string_booleans_and_invalid_duration():
    frame = pd.DataFrame({
        "case:concept:name": ["A", "B", "C"],
        "duration_hours": [10.0, 20.0, "invalid"],
        "event_count": [3, 5, 1],
        "Accepted": ["True", "False", None],
    })
    result = overview_metrics(frame)
    assert result["case_count"] == 3
    assert result["event_count"] == 9
    assert result["acceptance_rate"] == 0.5
    assert result["median_duration_hours"] == 15.0
    assert result["invalid_duration_count"] == 1


def test_boolean_parser_leaves_unknown_as_missing():
    parsed = parse_boolean_series(pd.Series(["TRUE", "no", "pending", None]))
    assert parsed.iloc[0] is True or bool(parsed.iloc[0]) is True
    assert bool(parsed.iloc[1]) is False
    assert pd.isna(parsed.iloc[2])
    assert pd.isna(parsed.iloc[3])


def test_simulation_is_hypothetical_and_does_not_silently_sum():
    frame = pd.DataFrame({
        "transition": ["A -> B", "C -> D"],
        "transition_count": [10, 20],
        "median_gap_hours": [100.0, 50.0],
        "screening_score": [2.0, 1.0],
    })
    result = simulate_gap_reduction(frame, 20, max_rows=1)
    assert len(result) == 1
    assert result.iloc[0]["hypothetical_median_gap_hours"] == 80.0
    assert result.iloc[0]["illustrative_hours_across_occurrences"] == 200.0
    assert bool(result.iloc[0]["savings_verified"]) is False


@pytest.mark.parametrize("pct", [-1, 51])
def test_simulation_rejects_invalid_reduction(pct):
    frame = pd.DataFrame({"transition_count": [1], "median_gap_hours": [5]})
    with pytest.raises(ValueError):
        simulate_gap_reduction(frame, pct)


def test_recommendation_validation_preserves_source_and_adds_warning():
    frame = pd.DataFrame({"transition": ["A -> B"], "transition_count": [4], "median_gap_hours": [12]})
    result = validate_recommendations(frame)
    assert result.loc[0, "transition"] == "A -> B"
    assert "causal effects" in result.loc[0, "interpretation_warning"]
