import pandas as pd
import pytest

from flowlens.agent_tools import build_tool_registry
from flowlens.optimization_agent import OptimizationAgent


class FakeCatalog:
    def __init__(self):
        self.tables = {
            "cases": pd.DataFrame({
                "case:concept:name": ["A", "B", "C", "D"],
                "duration_hours": [10.0, 20.0, 30.0, 40.0],
                "event_count": [3, 5, 4, 6],
                "Accepted": [True, False, True, True],
            }),
            "waits": pd.DataFrame({
                "concept:name": ["Review"],
                "median_wait_hours": [20.0],
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
                "priority_rank": [1, 2, 3],
                "transition": [
                    "Review [suspend] -> Review [resume]",
                    "Offer -> cancellation",
                    "Validation -> rework",
                ],
                "transition_count": [10, 8, 5],
                "applications_observed": [8, 6, 4],
                "median_gap_hours": [20.0, 40.0, 15.0],
                "p90_gap_hours": [30.0, 60.0, 25.0],
                "screening_score": [9.0, 7.0, 5.0],
                "recommendation_type": [
                    "Suspension and follow-up investigation",
                    "Outcome pathway investigation",
                    "Rework investigation",
                ],
                "recommended_investigation": [
                    "Inspect follow-up cases.",
                    "Inspect cancellation timelines.",
                    "Inspect repeated validation.",
                ],
                "causal_effect_established": [False, False, False],
                "confirmed_queue_time": [False, False, False],
                "scenario_reduction_is_assumption": [True, True, True],
            }),
        }


def test_agent_completes_multi_step_workflow():
    registry = build_tool_registry(FakeCatalog())
    agent = OptimizationAgent(registry)

    result = agent.run(applications=1000, seed=42)

    assert result["status"] == "completed"
    assert len(result["execution_trace"]) == 7
    assert len(result["candidate_evaluations"]) == 3
    assert result["recommendation"] is not None
    assert result["recommendation"]["acceptance_quality_guardrail_passed"]


def test_agent_records_historical_causal_boundary():
    agent = OptimizationAgent(build_tool_registry(FakeCatalog()))

    result = agent.run(applications=1000)

    assert (
        result["investigation"]["historical_causal_assessment"]["status"]
        == "not_identified"
    )
    assert "synthetic" in result["evidence_boundary"].lower()


def test_agent_selects_tool_from_historical_finding():
    agent = OptimizationAgent(build_tool_registry(FakeCatalog()))

    result = agent.run(applications=1000)

    assert (
        result["execution_trace"][2]["tool"]
        == "get_bottlenecks"
    )
    assert "suspension" in result["investigation"]["tool_selection_reason"].lower()


def test_agent_rejects_too_small_experiment():
    agent = OptimizationAgent(build_tool_registry(FakeCatalog()))

    with pytest.raises(ValueError):
        agent.run(applications=10)
