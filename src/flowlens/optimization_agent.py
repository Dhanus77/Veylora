"""Adaptive, auditable optimization investigation agent."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flowlens.agent_tools import ToolRegistry


class OptimizationAgent:
    """Use observed evidence to choose investigation and scenario candidates."""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def run(self, applications: int = 5000, seed: int = 42) -> dict[str, Any]:
        if applications < 100:
            raise ValueError("At least 100 simulated applications are required.")

        trace: list[dict[str, Any]] = []

        def execute_step(name: str, arguments: dict | None = None):
            result = self.registry.execute(name, arguments or {})
            trace.append({
                "step": len(trace) + 1,
                "tool": name,
                "status": "completed",
                "result": result,
            })
            return result

        overview = execute_step("get_process_overview")
        opportunities_result = execute_step(
            "get_prioritized_opportunities", {"limit": 10}
        )

        opportunities = opportunities_result.get("opportunities", [])

        if not opportunities:
            raise ValueError(
                "The historical dataset contains no usable investigation opportunities."
            )

        # Select the next analytical tool from the observed opportunity type.
        top_opportunity = opportunities[0]
        recommendation_type = str(
            top_opportunity.get("recommendation_type", "")
        ).casefold()

        if "suspension" in recommendation_type or "follow-up" in recommendation_type:
            selected_investigation = execute_step(
                "get_bottlenecks", {"limit": 10}
            )
            selected_tool_reason = (
                "The leading historical finding concerns a suspension/follow-up "
                "path, so elapsed lifecycle gaps were inspected."
            )
        elif "outcome" in recommendation_type or "cancellation" in recommendation_type:
            selected_investigation = execute_step(
                "get_activity_transitions", {"limit": 20}
            )
            selected_tool_reason = (
                "The leading finding concerns an outcome pathway, so activity "
                "transition frequencies were inspected."
            )
        else:
            selected_investigation = execute_step(
                "get_rework_evidence", {"limit": 20}
            )
            selected_tool_reason = (
                "The leading finding is not a recognized suspension or outcome "
                "pathway, so descriptive rework evidence was inspected."
            )

        historical_causality = execute_step("assess_historical_causality")

        # Candidate investigations come from the actual historical register.
        # The numerical scenario levels below are explicit assumptions only.
        scenario_levels = [6.0, 12.0, 18.0]
        candidates = []

        for index, opportunity in enumerate(opportunities[:3]):
            candidates.append({
                "candidate": (
                    f"Investigate: {opportunity.get('transition', 'Unlabelled transition')}"
                ),
                "historical_transition": opportunity.get("transition"),
                "recommendation_type": opportunity.get("recommendation_type"),
                "historical_screening_score": opportunity.get("screening_score"),
                "historical_median_gap_hours": opportunity.get("median_gap_hours"),
                "applications_observed": opportunity.get("applications_observed"),
                "recommended_investigation": opportunity.get(
                    "recommended_investigation"
                ),
                "assumed_delay_reduction_hours": scenario_levels[index],
                "assumption": (
                    f"Illustrative scenario only: assume a {scenario_levels[index]:.0f}-hour "
                    "reduction. This value is not estimated from historical data."
                ),
            })

        evaluations = []

        for candidate in candidates:
            experiment = execute_step(
                "run_simulated_experiment",
                {
                    "applications": applications,
                    "reduction_hours": candidate["assumed_delay_reduction_hours"],
                    "seed": seed,
                },
            )

            delay = experiment["delay_effect"]
            quality = experiment["acceptance_effect"]

            evaluations.append({
                **candidate,
                "estimated_delay_effect_hours": delay["effect"],
                "delay_confidence_interval": delay["confidence_interval"],
                "acceptance_effect": quality["effect"],
                "acceptance_quality_guardrail_passed": (
                    abs(quality["effect"]) < 0.05
                ),
                "delay_effect_recovered": (
                    experiment["validation"]["delay_effect_recovered"]
                ),
                "evaluation_type": "controlled_synthetic_scenario",
            })

        ranked = sorted(
            evaluations,
            key=lambda item: (
                item["acceptance_quality_guardrail_passed"],
                abs(item["estimated_delay_effect_hours"]),
            ),
            reverse=True,
        )

        for rank, item in enumerate(ranked, start=1):
            item["rank"] = rank

        recommendation = ranked[0] if ranked else None

        return {
            "agent": "Veylora Optimization Agent",
            "status": "completed",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "objective": (
                "Reduce loan application processing delay without "
                "reducing acceptance quality."
            ),
            "investigation": {
                "historical_overview": overview,
                "prioritized_opportunities": opportunities_result,
                "selected_investigation": selected_investigation,
                "tool_selection_reason": selected_tool_reason,
                "historical_causal_assessment": historical_causality,
            },
            "candidate_evaluations": ranked,
            "recommendation": recommendation,
            "approval_boundary": (
                "Research recommendation only. Validate the proposed "
                "intervention with process owners and a real controlled "
                "operational pilot before implementation."
            ),
            "evidence_boundary": (
                "Candidate investigations are derived from historical "
                "recommendations. Numerical delay reductions are illustrative "
                "assumptions evaluated in synthetic experiments. They do not "
                "establish real-world intervention impact."
            ),
            "execution_trace": trace,
            "audit_log": list(self.registry.audit_log),
        }
