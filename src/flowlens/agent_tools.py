"""Executable analytical tool registry for the Veylora agent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

import pandas as pd

from flowlens.analytics import overview_metrics
from flowlens.causal_engine import (
    estimate_randomized_effect,
    historical_identification_assessment,
)
from flowlens.process_simulator import simulate_loan_process


@dataclass
class Tool:
    name: str
    description: str
    function: Callable[..., dict[str, Any]]


class ToolRegistry:
    """Register, execute, and audit analytical tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self.audit_log: list[dict[str, Any]] = []

    def register(
        self,
        name: str,
        description: str,
        function: Callable[..., dict[str, Any]],
    ) -> None:
        if not name or name in self._tools:
            raise ValueError(f"Invalid or duplicate tool name: {name}")
        self._tools[name] = Tool(name, description, function)

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = arguments or {}

        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")

        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be a dictionary.")

        tool = self._tools[name]
        started = datetime.now(timezone.utc).isoformat()

        try:
            result = tool.function(**arguments)
            record = {
                "tool": name,
                "status": "success",
                "started_at": started,
                "result": result,
            }
        except Exception as exc:
            record = {
                "tool": name,
                "status": "error",
                "started_at": started,
                "error": f"{type(exc).__name__}: {exc}",
            }
            self.audit_log.append(record)
            raise

        self.audit_log.append(record)
        return result


def _records(frame: pd.DataFrame | None, limit: int = 10) -> list[dict[str, Any]]:
    if frame is None or frame.empty:
        return []

    safe = frame.head(limit).copy()
    safe = safe.astype(object).where(pd.notna(safe), None)
    return safe.to_dict("records")


def build_tool_registry(catalog) -> ToolRegistry:
    """Build tools from the application's currently loaded local catalog."""

    registry = ToolRegistry()
    tables = catalog.tables

    def process_overview() -> dict[str, Any]:
        cases = tables.get("cases")
        if cases is None:
            raise ValueError("The case-level dataset is unavailable.")

        return {
            "metrics": overview_metrics(cases),
            "dataset": "Historical BPI 2017",
            "case_count": len(cases),
            "evidence_type": "historical_observation",
        }

    def get_bottlenecks(limit: int = 10) -> dict[str, Any]:
        if not 1 <= limit <= 50:
            raise ValueError("limit must be between 1 and 50.")

        waits = tables.get("waits")
        transitions = tables.get("transition_summary")

        return {
            "activity_waits": _records(waits, limit),
            "lifecycle_transitions": _records(transitions, limit),
            "interpretation": (
                "These are observed elapsed gaps, not confirmed queue time "
                "or active processing time."
            ),
            "evidence_type": "historical_observation",
        }

    def get_rework_evidence(limit: int = 20) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100.")

        frame = tables.get("rework")
        return {
            "records": _records(frame, limit),
            "interpretation": (
                "Descriptive rework evidence. It does not establish that "
                "rework caused longer processing duration."
            ),
            "evidence_type": "historical_observation",
        }

    def get_activity_transitions(limit: int = 20) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100.")

        frame = tables.get("transitions")
        return {
            "records": _records(frame, limit),
            "interpretation": (
                "Activity-to-activity transition frequencies from the "
                "historical event log."
            ),
            "evidence_type": "historical_observation",
        }

    def assess_historical_causality() -> dict[str, Any]:
        return historical_identification_assessment()

    def run_simulated_experiment(
        applications: int = 3000,
        reduction_hours: float = 12.0,
        seed: int = 42,
    ) -> dict[str, Any]:
        data, metadata = simulate_loan_process(
            n_applications=applications,
            true_delay_reduction_hours=reduction_hours,
            seed=seed,
        )

        delay_result = estimate_randomized_effect(
            data,
            treatment="treatment",
            outcome="processing_duration_hours",
        )

        acceptance_result = estimate_randomized_effect(
            data,
            treatment="treatment",
            outcome="accepted",
        )

        return {
            "metadata": metadata,
            "delay_effect": delay_result.to_dict(),
            "acceptance_effect": acceptance_result.to_dict(),
            "validation": {
                "known_delay_effect": metadata["true_effect_hours"],
                "estimated_delay_effect": delay_result.effect,
                "delay_effect_recovered": (
                    abs(delay_result.effect - metadata["true_effect_hours"]) < 2.0
                ),
                "acceptance_effect_is_small": (
                    abs(acceptance_result.effect) < 0.05
                ),
            },
            "evidence_type": "controlled_synthetic_experiment",
        }

    def get_prioritized_opportunities(limit: int = 10) -> dict[str, Any]:
        if not 1 <= limit <= 27:
            raise ValueError("limit must be between 1 and 27.")

        frame = tables.get("recommendations")
        if frame is None or frame.empty:
            return {
                "opportunities": [],
                "evidence_type": "historical_observation",
                "message": "No historical recommendations are available.",
            }

        columns = [
            "priority_rank",
            "transition",
            "transition_count",
            "applications_observed",
            "median_gap_hours",
            "p90_gap_hours",
            "screening_score",
            "recommendation_type",
            "recommended_investigation",
            "evidence_quality",
            "causal_effect_established",
            "confirmed_queue_time",
            "scenario_reduction_is_assumption",
            "interpretation_warning",
        ]
        available = [column for column in columns if column in frame.columns]
        selected = frame[available].copy()

        if "screening_score" in selected.columns:
            selected["screening_score"] = pd.to_numeric(
                selected["screening_score"], errors="coerce"
            )
            selected = selected.sort_values(
                "screening_score", ascending=False, na_position="last"
            )

        return {
            "opportunities": _records(selected, limit),
            "evidence_type": "historical_observation",
            "interpretation": (
                "Screening priorities only. Elapsed gaps are not confirmed "
                "queue time, and no causal intervention effect is established."
            ),
        }

    registry.register(
        "get_prioritized_opportunities",
        "Retrieve ranked historical process-improvement investigation opportunities.",
        get_prioritized_opportunities,
    )
    registry.register(
        "get_process_overview",
        "Retrieve historical case volume, acceptance, and duration metrics.",
        process_overview,
    )
    registry.register(
        "get_bottlenecks",
        "Inspect the largest observed activity and lifecycle elapsed gaps.",
        get_bottlenecks,
    )
    registry.register(
        "get_rework_evidence",
        "Retrieve descriptive historical rework evidence.",
        get_rework_evidence,
    )
    registry.register(
        "get_activity_transitions",
        "Inspect historical activity-to-activity transition frequencies.",
        get_activity_transitions,
    )
    registry.register(
        "assess_historical_causality",
        "Check whether the historical evidence supports causal identification.",
        assess_historical_causality,
    )
    registry.register(
        "run_simulated_experiment",
        "Run a controlled synthetic intervention experiment and estimate its effects.",
        run_simulated_experiment,
    )

    return registry
