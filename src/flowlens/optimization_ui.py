"""Streamlit interface for Veylora autonomous optimization."""

from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from flowlens.agent_tools import build_tool_registry
from flowlens.optimization_agent import OptimizationAgent


def render_optimization_workspace(catalog) -> None:
    st.markdown(
        '<div class="fl-kicker">VEYLORA / AUTONOMOUS INTELLIGENCE</div>',
        unsafe_allow_html=True,
    )
    st.title("Autonomous Business Process Optimization")
    st.markdown(
        '<div class="fl-subtitle">Investigate process evidence, evaluate '
        'interventions, compare outcomes, and generate an auditable '
        'optimization recommendation.</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "**Optimization objective:** Reduce loan application processing "
        "delays without reducing acceptance quality."
    )
    st.warning(
        "Historical process findings are observational. Intervention "
        "effects shown here come from synthetic randomized experiments, "
        "not proven real-world business impact. Human approval is required."
    )

    col1, col2 = st.columns(2)
    with col1:
        applications = st.number_input(
            "Synthetic applications per experiment",
            min_value=100,
            max_value=50000,
            value=5000,
            step=1000,
        )
    with col2:
        seed = st.number_input(
            "Experiment random seed",
            min_value=0,
            max_value=1000000,
            value=42,
            step=1,
        )

    if st.button(
        "Run Autonomous Investigation",
        type="primary",
        use_container_width=True,
    ):
        try:
            with st.spinner(
                "Investigating process evidence, running experiments, "
                "and ranking interventions..."
            ):
                registry = build_tool_registry(catalog)
                agent = OptimizationAgent(registry)
                result = agent.run(
                    applications=int(applications),
                    seed=int(seed),
                )
                st.session_state["veylora_optimization_result"] = result

            st.success("Investigation completed. Execution trace recorded.")

        except Exception as exc:
            st.error(f"Investigation failed ({type(exc).__name__}): {exc}")
            return

    result = st.session_state.get("veylora_optimization_result")

    if not result:
        st.subheader("Investigation workflow")
        st.markdown(
            """
            1. Retrieve historical process performance.
            2. Inspect historically prioritized opportunities.
            3. Select analytical tools based on historical findings.
            4. Assess whether historical causal identification is justified.
            5. Run synthetic randomized experiments for candidate investigations.
            6. Apply an acceptance-quality guardrail.
            7. Rank candidates and generate an audit record.
            """
        )
        st.caption(
            "Run the investigation to populate historical evidence, "
            "candidate experiments, and the recommendation."
        )
        return

    investigation = result.get("investigation", {})
    overview = investigation.get("historical_overview", {}).get("metrics", {})
    historical = investigation.get("historical_causal_assessment", {})
    candidates = pd.DataFrame(result.get("candidate_evaluations", []))
    recommendation = result.get("recommendation")

    st.divider()
    st.subheader("Investigation result")

    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Historical applications",
        f'{overview.get("case_count", 0):,}',
    )

    median_duration = overview.get("median_duration_hours")
    m2.metric(
        "Historical median duration",
        f"{median_duration:,.1f} h"
        if median_duration is not None
        else "Unavailable",
    )

    causal_status = historical.get("status", "unavailable")
    m3.metric(
        "Historical causal status",
        causal_status.replace("_", " ").title(),
    )

    st.caption(
        "Historical figures are descriptive. They are not estimates "
        "of intervention effects."
    )

    st.divider()
    st.subheader("Historical opportunity register")

    opportunities_result = investigation.get("prioritized_opportunities", {})
    opportunities = opportunities_result.get("opportunities", [])

    if opportunities:
        opportunity_df = pd.DataFrame(opportunities)
        preferred = [
            "priority_rank",
            "transition",
            "recommendation_type",
            "screening_score",
            "applications_observed",
            "median_gap_hours",
            "recommended_investigation",
        ]
        visible = [column for column in preferred if column in opportunity_df.columns]
        st.dataframe(
            opportunity_df[visible],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "No opportunity details were returned by the agent for this run."
        )

    selection_reason = investigation.get("tool_selection_reason")
    if selection_reason:
        st.markdown("**Agent tool-selection reasoning**")
        st.write(selection_reason)

    st.divider()
    st.subheader("Synthetic experiment comparison")

    if candidates.empty:
        st.warning("The agent did not return candidate experiment results.")
    else:
        preferred_columns = [
            "rank",
            "candidate",
            "historical_transition",
            "assumed_delay_reduction_hours",
            "estimated_delay_effect_hours",
            "acceptance_effect",
            "acceptance_quality_guardrail_passed",
            "delay_effect_recovered",
        ]
        display_columns = [
            column for column in preferred_columns
            if column in candidates.columns
        ]

        st.dataframe(
            candidates[display_columns],
            use_container_width=True,
            hide_index=True,
        )

        if "estimated_delay_effect_hours" in candidates.columns:
            chart = candidates.copy()
            chart["estimated_reduction"] = -pd.to_numeric(
                chart["estimated_delay_effect_hours"],
                errors="coerce",
            )
            chart = chart.sort_values("rank", ascending=False)

            if "acceptance_quality_guardrail_passed" in chart.columns:
                color_column = "acceptance_quality_guardrail_passed"
                color_map = {
                    True: "#a8e34b",
                    False: "#d66b6b",
                }
            else:
                color_column = None
                color_map = None

            fig = px.bar(
                chart,
                x="estimated_reduction",
                y="candidate",
                orientation="h",
                text="estimated_reduction",
                color=color_column,
                color_discrete_map=color_map,
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=350,
                xaxis_title=(
                    "Estimated reduction in simulated duration (hours)"
                ),
                yaxis_title="",
                showlegend=False,
            )
            fig.update_traces(
                texttemplate="%{text:.2f} h",
                textposition="outside",
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False},
            )

        st.caption(
            "Negative estimated delay effects indicate shorter simulated "
            "duration in the treatment group. These are not historical "
            "business savings."
        )

        top_candidate = candidates.sort_values("rank").iloc[0]
        st.subheader("Top candidate experiment")

        a, b, c = st.columns(3)
        a.metric(
            "Assumed reduction",
            f'{top_candidate.get("assumed_delay_reduction_hours", 0):.1f} h',
        )
        b.metric(
            "Estimated delay effect",
            f'{top_candidate.get("estimated_delay_effect_hours", 0):+.2f} h',
        )

        guardrail = top_candidate.get(
            "acceptance_quality_guardrail_passed"
        )
        c.metric(
            "Acceptance guardrail",
            "Unavailable" if pd.isna(guardrail) else (
                "Passed" if bool(guardrail) else "Not passed"
            ),
        )

        interval = top_candidate.get(
            "delay_confidence_interval",
            top_candidate.get("confidence_interval"),
        )
        if isinstance(interval, (list, tuple)) and len(interval) == 2:
            st.write(
                "Estimated delay-effect confidence interval: "
                f"**[{interval[0]:.2f}, {interval[1]:.2f}] hours**"
            )

    st.divider()
    st.subheader("Agent recommendation")

    if recommendation:
        st.markdown(f'### {recommendation.get("candidate", "Candidate")}')
        st.write(recommendation.get("assumption", ""))
        st.write(
            "Estimated simulated delay effect: "
            f'**{recommendation.get("estimated_delay_effect_hours", 0):+.2f} hours**'
        )
        st.write(
            "Acceptance effect: "
            f'**{recommendation.get("acceptance_effect", 0):+.3f}**'
        )

        passed = recommendation.get(
            "acceptance_quality_guardrail_passed"
        )
        st.write(
            "Acceptance quality guardrail: "
            f"**{'Passed' if passed else 'Not passed'}**"
        )
    else:
        st.info("No candidate passed the agent's recommendation criteria.")

    st.warning(result.get("approval_boundary", "Human approval is required."))
    st.caption(result.get("evidence_boundary", ""))

    st.divider()
    st.subheader("Agent execution trace")

    for step in result.get("execution_trace", []):
        with st.expander(
            f'Step {step.get("step", "?")}: '
            f'{step.get("tool", "Unknown tool")} — '
            f'{step.get("status", "unknown")}'
        ):
            st.json(step.get("result", {}))

    with st.expander("Historical causal identification assessment"):
        st.json(historical)

    with st.expander("Complete audit record"):
        st.json(result.get("audit_log", []))

    report = json.dumps(result, indent=2, default=str).encode("utf-8")
    st.download_button(
        "Download complete investigation report",
        data=report,
        file_name="veylora_optimization_audit.json",
        mime="application/json",
        use_container_width=True,
    )
