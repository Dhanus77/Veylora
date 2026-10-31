import pandas as pd
import pytest

from flowlens.agent_tools import ToolRegistry, build_tool_registry


class FakeCatalog:
    def __init__(self):
        self.tables = {
            "cases": pd.DataFrame({
                "case:concept:name": ["A", "B", "C"],
                "duration_hours": [10.0, 20.0, 30.0],
                "event_count": [3, 5, 4],
                "Accepted": [True, False, True],
            }),
            "waits": pd.DataFrame({
                "concept:name": ["Review", "Approval"],
                "median_wait_hours": [20.0, 30.0],
            }),
            "transition_summary": pd.DataFrame({
                "transition": ["start -> suspend"],
                "median_gap_hours": [15.0],
            }),
            "rework": pd.DataFrame({
                "activity": ["Review"],
                "count": [5],
            }),
            "transitions": pd.DataFrame({
                "concept:name": ["Review"],
                "next_activity": ["Approval"],
                "transition_count": [10],
            }),
            "recommendations": pd.DataFrame({
                "priority_rank": [1, 2],
                "transition": ["Review -> suspend", "Offer -> cancellation"],
                "transition_count": [10, 5],
                "applications_observed": [8, 5],
                "median_gap_hours": [20.0, 40.0],
                "p90_gap_hours": [30.0, 60.0],
                "screening_score": [9.0, 7.0],
                "recommendation_type": [
                    "Suspension and follow-up investigation",
                    "Outcome pathway investigation",
                ],
                "recommended_investigation": [
                    "Inspect follow-up cases.",
                    "Inspect cancellation timelines.",
                ],
                "causal_effect_established": [False, False],
                "confirmed_queue_time": [False, False],
            }),
        }


def test_registry_exposes_seven_tools():
    registry = build_tool_registry(FakeCatalog())
    names = {item["name"] for item in registry.list_tools()}

    assert len(names) == 7
    assert "get_prioritized_opportunities" in names


def test_opportunity_tool_returns_ranked_source_evidence():
    registry = build_tool_registry(FakeCatalog())

    result = registry.execute(
        "get_prioritized_opportunities", {"limit": 2}
    )

    assert len(result["opportunities"]) == 2
    assert result["opportunities"][0]["screening_score"] == 9.0
    assert result["evidence_type"] == "historical_observation"


def test_process_overview_reads_catalog():
    registry = build_tool_registry(FakeCatalog())
    result = registry.execute("get_process_overview")

    assert result["case_count"] == 3


def test_bottleneck_tool_returns_observed_evidence():
    registry = build_tool_registry(FakeCatalog())
    result = registry.execute("get_bottlenecks", {"limit": 5})

    assert len(result["activity_waits"]) == 2


def test_simulation_tool_runs_causal_experiment():
    registry = build_tool_registry(FakeCatalog())
    result = registry.execute(
        "run_simulated_experiment",
        {"applications": 5000, "reduction_hours": 12, "seed": 42},
    )

    assert result["validation"]["delay_effect_recovered"] is True


def test_execution_is_audited():
    registry = build_tool_registry(FakeCatalog())
    registry.execute("assess_historical_causality")

    assert registry.audit_log[0]["status"] == "success"


def test_unknown_tool_is_rejected():
    registry = ToolRegistry()

    with pytest.raises(ValueError, match="Unknown tool"):
        registry.execute("delete_production_records")


def test_invalid_tool_arguments_are_rejected():
    registry = build_tool_registry(FakeCatalog())

    with pytest.raises(ValueError):
        registry.execute("get_bottlenecks", {"limit": 1000})
