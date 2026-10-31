from __future__ import annotations

import sys
import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flowlens.analytics import overview_metrics, simulate_gap_reduction, validate_recommendations
from flowlens.catalog import ARTIFACTS, load_catalog

DATA_DIR = Path(__import__("os").environ.get("FLOWLENS_DATA_DIR", ROOT / "data" / "processed"))

st.set_page_config(
    page_title="Veylora | Process Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Styling is intentionally restrained: strong hierarchy, readable tables, no emoji-heavy UI.
st.markdown(
    """
    <style>
      :root {
        --fl-bg:#090b0a; --fl-panel:#151816; --fl-panel-2:#1b201b;
        --fl-line:#2a322b; --fl-ink:#f1f5ef; --fl-muted:#9ba69b;
        --fl-accent:#a8e34b; --fl-accent-soft:#26351b;
      }
      .stApp {
        background:radial-gradient(ellipse at 78% 0%,rgba(113,153,47,.10),transparent 34%),var(--fl-bg);
        color:var(--fl-ink);
      }
      .block-container {max-width:1600px;padding:1.45rem 2.2rem 3rem;}
      [data-testid="stSidebar"] {
        background:linear-gradient(180deg,#151816 0%,#101310 100%);
        border-right:1px solid var(--fl-line);
      }
      [data-testid="stSidebar"] > div:first-child {padding-top:1.2rem;}
      [data-testid="stSidebar"] h1 {font-size:1.45rem;letter-spacing:-.04em;}
      [data-testid="stSidebar"] [data-testid="stRadio"] > label {
        color:var(--fl-muted);font-size:.70rem;font-weight:750;
        letter-spacing:.13em;text-transform:uppercase;margin:1rem 0 .45rem;
      }
      [data-testid="stSidebar"] [data-testid="stRadio"] > div {gap:.22rem;}
      [data-testid="stSidebar"] [data-testid="stRadio"] input {display:none;}
      [data-testid="stSidebar"] [data-testid="stRadio"] label {
        background:transparent;border:1px solid transparent;min-height:2.35rem;
        display:flex;align-items:center;padding:.35rem .65rem !important;
      }
      [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
        background:#26331d;border-color:#3c512b;box-shadow:inset 3px 0 0 #a8e34b;
      }
      [data-testid="stSidebar"] [data-testid="stRadio"] label p {color:#dce5d8;}
      [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p {
        color:#f4f8ed;font-weight:750;
      }
      [data-testid="stSidebar"] [data-testid="stRadio"] label {
        border-radius:.65rem;padding:.34rem .48rem;transition:background .15s ease;
      }
      [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {background:#222820;}
      [data-testid="stSidebar"] [data-testid="stRadio"] label p {font-size:.88rem;font-weight:550;}
      .fl-brand {display:flex;align-items:center;gap:.65rem;padding:.35rem 0 .25rem;}
      .fl-brand-mark {
        width:2rem;height:2rem;border-radius:.7rem;display:flex;align-items:center;
        justify-content:center;color:#10150a;background:var(--fl-accent);
        font-size:1.1rem;font-weight:900;box-shadow:0 0 24px rgba(168,227,75,.18);
      }
      .fl-brand-name {font-size:1.35rem;font-weight:800;letter-spacing:-.05em;color:var(--fl-ink);}
      .fl-brand-sub {font-size:.72rem;color:var(--fl-muted);margin-top:.12rem;}
      .fl-kicker {color:var(--fl-accent);font-size:.70rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase;}
      .fl-subtitle {color:var(--fl-muted);font-size:.96rem;max-width:920px;margin-top:-.15rem;}
      .fl-section-label {color:var(--fl-muted);font-size:.70rem;letter-spacing:.13em;text-transform:uppercase;font-weight:750;}
      .fl-note {
        background:linear-gradient(100deg,#172018,#131814);border:1px solid var(--fl-line);
        border-left:3px solid var(--fl-accent);padding:.85rem 1rem;border-radius:.75rem;color:var(--fl-ink);
      }
      .fl-footnote {color:var(--fl-muted);font-size:.80rem;}
      h1,h2,h3 {letter-spacing:-.035em;}
      h1 {font-weight:800 !important;} h2 {font-weight:750 !important;} h3 {font-weight:700 !important;}
      div[data-testid="stMetric"] {
        background:linear-gradient(145deg,#1c2419,#141815 78%);border:1px solid #34402d;
        border-radius:1rem;padding:1rem 1.05rem;min-height:112px;box-shadow:0 8px 28px rgba(0,0,0,.16);
      }
      div[data-testid="stMetricLabel"] {color:#aab5a4;font-size:.78rem;font-weight:650;}
      div[data-testid="stMetricValue"] {color:#f4f7ef;font-weight:800;letter-spacing:-.04em;}
      div[data-testid="stMetricDelta"] {font-size:.75rem;}
      [data-testid="stPlotlyChart"] {background:#121613;border:1px solid var(--fl-line);border-radius:1rem;padding:.55rem .55rem .15rem;}
      [data-testid="stDataFrame"] {border:1px solid var(--fl-line);border-radius:.75rem;overflow:hidden;}
      .stTabs [data-baseweb="tab-list"] {gap:.45rem;border-bottom:1px solid var(--fl-line);}
      .stTabs [data-baseweb="tab"] {border-radius:.55rem .55rem 0 0;padding:.55rem .9rem;}
      .stTabs [aria-selected="true"] {color:var(--fl-accent) !important;border-bottom-color:var(--fl-accent) !important;}
      [data-testid="stExpander"] {background:#111512;border:1px solid var(--fl-line);border-radius:.75rem;}
      [data-testid="stAlert"] {border-radius:.8rem;}
      hr {border-color:var(--fl-line) !important;}
      #MainMenu, footer {visibility:hidden;}

      /* Veylora visual system */
      :root {
        --fl-bg:#090b0a; --fl-panel:#151816; --fl-panel2:#1b201b;
        --fl-line:#2b332c; --fl-ink:#f1f5ef; --fl-muted:#9ba69b;
        --fl-accent:#a8e34b; --fl-accent2:#7fc62d;
      }
      .stApp {
        background:
          radial-gradient(ellipse at 72% 0%,rgba(130,180,48,.12),transparent 32%),
          radial-gradient(ellipse at 0% 70%,rgba(90,120,65,.06),transparent 35%),
          var(--fl-bg);
        color:var(--fl-ink);
      }
      .block-container {max-width:1680px;padding:1.25rem 2rem 3rem;}
      [data-testid="stHeader"] {background:rgba(8,10,9,.88);}
      [data-testid="stSidebar"] {
        background:linear-gradient(180deg,#171a18 0%,#101310 100%);
        border-right:1px solid #293129;
      }
      [data-testid="stSidebar"] > div:first-child {padding-top:1.1rem;}
      .fl-brand {padding:.55rem .25rem 1rem;}
      .fl-brand-mark {box-shadow:0 0 26px rgba(168,227,75,.24);}
      .fl-brand-name {font-size:1.42rem;}
      .fl-kicker {color:var(--fl-accent);font-size:.68rem;font-weight:850;letter-spacing:.18em;}
      .fl-subtitle {color:#aab5a8;font-size:.9rem;max-width:900px;}
      .fl-note {
        background:linear-gradient(100deg,rgba(30,43,27,.94),rgba(18,23,19,.96));
        border:1px solid #35432f;border-left:3px solid var(--fl-accent);
        border-radius:12px;padding:.8rem 1rem;color:#e8eee4;font-size:.82rem;
      }
      h1,h2,h3 {letter-spacing:-.04em;}
      h1 {font-weight:800 !important;}
      h2 {font-size:1.35rem !important;font-weight:760 !important;}
      h3 {font-size:1.04rem !important;font-weight:720 !important;}
      p, label, [data-testid="stMarkdownContainer"] {color:inherit;}
      div[data-testid="stMetric"] {
        background:
          radial-gradient(ellipse at 70% 0%,rgba(151,205,58,.12),transparent 58%),
          linear-gradient(145deg,#1c231b,#141815 76%);
        border:1px solid #34402f;border-radius:16px;padding:1rem 1.1rem;
        min-height:112px;box-shadow:0 10px 30px rgba(0,0,0,.20);
        transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;
      }
      div[data-testid="stMetric"]:hover {transform:translateY(-2px);border-color:#647c43;box-shadow:0 12px 34px rgba(0,0,0,.3);}
      div[data-testid="stMetricLabel"] {color:#aeb9a9;font-size:.76rem;font-weight:650;}
      div[data-testid="stMetricValue"] {color:#f5f8f1;font-weight:820;letter-spacing:-.045em;}
      div[data-testid="stMetricDelta"] {font-size:.75rem;}
      [data-testid="stPlotlyChart"] {
        background:linear-gradient(145deg,#151a16,#101411);
        border:1px solid #2b352c;border-radius:14px;padding:.45rem;
      }
      [data-testid="stDataFrame"], [data-testid="stTable"] {
        border:1px solid #303a31;border-radius:12px;overflow:hidden;
        background:#111612;
      }
      [data-testid="stDataFrame"] iframe {border-radius:12px;}
      .stTabs [data-baseweb="tab-list"] {gap:.35rem;border-bottom:1px solid #303a31;}
      .stTabs [data-baseweb="tab"] {
        background:transparent;border-radius:8px 8px 0 0;padding:.62rem .85rem;
        color:#aeb8aa;font-weight:650;
      }
      .stTabs [aria-selected="true"] {color:var(--fl-accent) !important;border-bottom:2px solid var(--fl-accent) !important;}
      [data-testid="stExpander"] {background:#121713;border:1px solid #303a31;border-radius:12px;}
      [data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,
      [data-testid="stSelectbox"] [data-baseweb="select"] > div,
      [data-testid="stNumberInput"] input {
        background:#171d18 !important;border:1px solid #354035 !important;
        border-radius:10px !important;color:#edf3e9 !important;
      }
      [data-testid="stSlider"] [role="slider"] {background:var(--fl-accent);}
      .stButton button,.stDownloadButton button {
        border-radius:10px;border:1px solid #526b38;background:#26351d;color:#f4f8ee;
        font-weight:700;transition:all .16s ease;
      }
      .stButton button:hover,.stDownloadButton button:hover {
        border-color:var(--fl-accent);background:#344a25;color:white;transform:translateY(-1px);
      }
      .stButton button[kind="primary"] {background:var(--fl-accent);color:#11170b;border:0;}
      .stButton button[kind="primary"]:hover {background:#baf265;color:#10160a;}
      [data-testid="stAlert"] {border-radius:12px;}
      hr {border-color:#2b352c !important;}
      #MainMenu, footer {visibility:hidden;}
      @media (max-width:900px) {.block-container {padding:.9rem .8rem 2rem;}}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading local analysis artifacts…")
def get_catalog(data_path: str):
    return load_catalog(data_path)


def friendly_column_name(name: str) -> str:
    """Convert technical artifact headers into readable UI labels only."""
    aliases = {
        "concept:name": "Activity",
        "transition": "Transition",
        "from_state": "From",
        "to_state": "To",
        "transition_count": "Occurrences",
        "applications_observed": "Applications observed",
        "event_count": "Recorded events",
        "median_gap_hours": "Median gap (hours)",
        "mean_gap_hours": "Average gap (hours)",
        "p90_gap_hours": "90th percentile gap (hours)",
        "max_gap_hours": "Maximum gap (hours)",
        "median_wait_hours": "Median elapsed gap (hours)",
        "mean_wait_hours": "Average elapsed gap (hours)",
        "duration_hours": "Case duration (hours)",
        "median_duration_hours": "Median duration (hours)",
        "mean_duration_hours": "Average duration (hours)",
        "p90_duration_hours": "90th percentile duration (hours)",
        "priority_rank": "Priority",
        "screening_score": "Screening score",
        "recommendation_type": "Investigation type",
        "recommended_investigation": "Suggested investigation",
        "evidence_quality": "Evidence quality",
        "assumed_reduction_percent": "Assumed reduction",
        "hypothetical_median_gap_hours": "Hypothetical median gap (hours)",
        "illustrative_hours_across_occurrences": "Illustrative hours across occurrences",
        "savings_verified": "Savings verified",
        "balanced_accuracy": "Balanced accuracy",
        "balanced_accuracy_mean": "Mean balanced accuracy",
        "roc_auc": "ROC-AUC",
        "roc_auc_mean": "Mean ROC-AUC",
        "precision_accepted": "Accepted precision",
        "recall_accepted": "Accepted recall",
        "f1_accepted": "Accepted F1 score",
        "MAE_hours": "Mean absolute error (hours)",
        "MedianAE_hours": "Median absolute error (hours)",
        "R2": "R²",
        "model": "Model",
        "variant_id": "Variant",
        "activity_path": "Observed activity path",
        "applications": "Applications",
        "applications_with_completed_events": "Applications with completed events",
        "unique_completed_event_variants": "Unique completed-event paths",
        "top_5_variant_coverage_pct": "Top 5 path coverage (%)",
        "top_15_variant_coverage_pct": "Top 15 path coverage (%)",
    }
    if name in aliases:
        return aliases[name]
    label = str(name).replace("case:", "").replace("activity:", "")
    label = re.sub(r"([a-z0-9])([A-Z])", r"\\1 \\2", label)
    label = label.replace("_", " ").replace(":", " ").strip()
    label = re.sub(r"\\s+", " ", label)
    return label[:1].upper() + label[1:]


def present_table(frame: pd.DataFrame, **kwargs):
    """Render friendly headers without changing the source DataFrame."""
    display = frame.copy()
    display.columns = [friendly_column_name(str(column)) for column in display.columns]
    st.dataframe(display, **kwargs)



def style_plotly(fig, *, height: int = 340, legend: bool = False):
    """Apply Veylora's shared dark/lime chart styling."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color="#dce6d7", size=11),
        height=height,
        margin=dict(l=12, r=14, t=18, b=12),
        showlegend=legend,
        hoverlabel=dict(bgcolor="#202820", bordercolor="#60754a", font_color="#f4f8ef"),
    )
    fig.update_xaxes(gridcolor="rgba(160,180,145,.10)", zeroline=False, linecolor="#394438")
    fig.update_yaxes(gridcolor="rgba(160,180,145,.10)", zeroline=False, linecolor="#394438")
    return fig


def table(catalog, key: str, *, height: int = 390):
    frame = catalog.tables.get(key)
    if frame is None:
        issue = next((i for i in catalog.issues if i.key == key), None)
        filename = ARTIFACTS.get(key, key)
        detail = issue.message if issue else "The artifact is not available."
        st.info(f"**{filename}** — {detail}")
        return None
    present_table(frame, width="stretch", height=height, hide_index=True)
    return frame



def exploratory_local_table(filename: str, *, height: int = 260):
    """Load and display a clearly labelled local exploratory CSV artifact."""
    path = DATA_DIR / filename
    if not path.is_file():
        st.info(f"**{filename}** — exploratory artifact not found in the processed-data directory.")
        return None
    try:
        frame = pd.read_csv(path, low_memory=False)
    except (OSError, pd.errors.ParserError, UnicodeError, ValueError) as exc:
        st.warning(f"Could not read exploratory artifact **{filename}** ({type(exc).__name__}).")
        return None
    present_table(frame, width="stretch", height=height, hide_index=True)
    return frame


def compact_acceptance_table(catalog, key: str, *, height: int = 190):
    """Show evaluation metrics without repeating long target/feature metadata."""
    frame = catalog.tables.get(key)
    if frame is None:
        table(catalog, key)
        return None
    display = frame.drop(columns=["target_definition", "features"], errors="ignore")
    present_table(display, width="stretch", height=height, hide_index=True)
    return frame


def show_acceptance_metadata(frame: pd.DataFrame | None = None):
    """Keep full target and feature definitions available without crowding tables."""
    target = (
        "Last recorded Accepted value on O_Create Offer [complete] for each application."
    )
    features = [
        "case:LoanGoal", "case:RequestedAmount", "case:ApplicationType",
        "start_month", "start_weekday",
    ]
    with st.expander("Target and feature definitions", expanded=False):
        st.markdown(f"**Prediction target:** {target}")
        st.markdown("**Primary input features:** " + ", ".join(f"`{item}`" for item in features))
        st.caption(
            "CreditScore and later financial/outcome fields are excluded from primary models. "
            "The target is an offer-acceptance indicator, not proof of final application completion."
        )


def show_holdout_metrics(frame: pd.DataFrame | None):
    """Highlight the intake-only Random Forest metrics and baseline reference."""
    if frame is None or frame.empty or "model" not in frame.columns:
        return
    rf = frame[frame["model"].astype(str).str.casefold().eq("random_forest")]
    baseline = frame[frame["model"].astype(str).str.casefold().eq("majority_baseline")]
    if rf.empty:
        return
    row = rf.iloc[0]
    cols = st.columns(4)
    for col, label, key, fmt in [
        (cols[0], "Balanced accuracy", "balanced_accuracy", "{:.1%}"),
        (cols[1], "ROC-AUC", "roc_auc", "{:.3f}"),
        (cols[2], "Accepted recall", "recall_accepted", "{:.1%}"),
        (cols[3], "Accepted precision", "precision_accepted", "{:.1%}"),
    ]:
        value = pd.to_numeric(pd.Series([row.get(key)]), errors="coerce").iloc[0]
        col.metric(label, fmt.format(value) if pd.notna(value) else "Not available")
    if not baseline.empty:
        b = baseline.iloc[0]
        b_ba = pd.to_numeric(pd.Series([b.get("balanced_accuracy")]), errors="coerce").iloc[0]
        b_auc = pd.to_numeric(pd.Series([b.get("roc_auc")]), errors="coerce").iloc[0]
        st.caption(
            "Majority baseline reference: balanced accuracy "
            f"{b_ba:.1%}, ROC-AUC {b_auc:.3f}."
            if pd.notna(b_ba) and pd.notna(b_auc) else "Majority baseline is shown in the table below."
        )

def audit_summary(catalog, key: str):
    """Display case-audit files as aggregate counts, not raw case-level rows."""
    frame = catalog.tables.get(key)
    if frame is None:
        issue = next((i for i in catalog.issues if i.key == key), None)
        message = issue.message if issue else "The artifact is not available."
        st.info(f"**{ARTIFACTS.get(key, key)}** — {message}")
        return

    id_cols = [
        c for c in frame.columns
        if c.lower() in {"case:concept:name", "case_id", "caseid", "application_id", "applicationid"}
        or c.lower().endswith(":concept:name")
    ]
    candidate_cols = [
        c for c in frame.columns if c not in id_cols
        and any(token in c.lower() for token in ("activity", "state", "lifecycle", "accepted", "status"))
        and frame[c].nunique(dropna=True) <= 60
    ]
    if candidate_cols and len(frame) > 30:
        summary = (
            frame.groupby(candidate_cols, dropna=False)
            .size().reset_index(name="case_or_record_count")
            .sort_values("case_or_record_count", ascending=False)
        )
        present_table(summary, width="stretch", height=360, hide_index=True)
        st.caption("Aggregated view; individual case identifiers are intentionally omitted.")
    else:
        safe = frame.drop(columns=id_cols, errors="ignore")
        present_table(safe, width="stretch", height=360, hide_index=True)
        st.caption("Case identifiers are intentionally omitted from this default view.")


def colname(frame: pd.DataFrame, options: list[str]) -> str | None:
    return next((name for name in options if name in frame.columns), None)


def as_hours(value) -> str:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "Not available"
    return f"{n:,.1f} h" if np.isfinite(n) else "Not available"


def as_int(value) -> str:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "Not available"
    return f"{n:,.0f}" if np.isfinite(n) else "Not available"


def page_header(title: str, subtitle: str):
    st.markdown(f'<div class="fl-kicker">VEYLORA  /  PROCESS INTELLIGENCE</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="fl-subtitle">{subtitle}</div>', unsafe_allow_html=True)
    st.write("")


def focus_evidence(question: str, evidence: dict) -> dict:
    """Select complete, question-relevant evidence without hiding source rows."""

    focused = dict(evidence)
    question_lower = question.casefold()

    waits = evidence.get("activity_wait_statistics", [])
    matching_rows = [
        row
        for row in waits
        if isinstance(row, dict)
        and str(row.get("concept:name", "")).casefold() in question_lower
    ]

    # A named activity gets its matching activity row and related transitions.
    # Broad questions retain the complete supplied evidence.
    if matching_rows:
        activity_names = {
            str(row["concept:name"]).casefold()
            for row in matching_rows
        }
        focused["activity_wait_statistics"] = matching_rows
        focused["transition_statistics"] = [
            row
            for row in evidence.get("transition_statistics", [])
            if any(
                name in str(row.get("transition", "")).casefold()
                for name in activity_names
            )
        ]
        focused["recommendations"] = [
            row
            for row in evidence.get("recommendations", [])
            if any(
                name in str(row.get("transition", "")).casefold()
                for name in activity_names
            )
        ]
        focused["question_scope"] = (
            "The question names a specific activity. Prioritize its incoming "
            "elapsed-gap statistics. Related transitions are secondary context. "
            "Do not describe the gap as time spent processing the activity."
        )
    else:
        focused["question_scope"] = (
            "Use the complete supplied evidence. For rankings, compare all "
            "available rows for the requested metric."
        )

    return focused


def main():
    catalog = get_catalog(str(DATA_DIR.resolve()))
    if not catalog.ready:
        st.error("The mandatory case-level dataset is missing or does not match the expected schema.")
        st.write(f"Expected directory: `{DATA_DIR.resolve()}`")
        cases_issue = next((issue for issue in catalog.issues if issue.key == "cases"), None)
        if cases_issue:
            st.write(f"**{cases_issue.filename}:** {cases_issue.message}")
        st.stop()

    cases = catalog.tables["cases"]
    metrics = overview_metrics(cases)

    with st.sidebar:
        st.markdown(
            '<div class="fl-brand"><div class="fl-brand-mark">V</div>'
            '<div><div class="fl-brand-name">Veylora</div>'
            '<div class="fl-brand-sub">Process Intelligence Platform</div></div></div>',
            unsafe_allow_html=True,
        )
        st.divider()
        nav_labels = {
            "Overview": "▦   Overview",
            "Process Explorer": "⌘   Process Explorer",
            "Predictive Evaluation": "⌁   Predictive Evaluation",
            "Opportunity Register": "▤   Opportunity Register",
            "Scenario Lab": "◉   Scenario Lab",
            "Evidence & Governance": "◇   Evidence & Governance",
            "Autonomous Optimization": "Autonomous Optimization",
            "AI Assistant": "✳   AI Assistant",
        }
        page = st.radio(
            "WORKSPACE",
            list(nav_labels),
            format_func=lambda item: nav_labels[item],
            label_visibility="visible",
        )
        st.divider()
        st.markdown('<div class="fl-section-label">SYSTEM STATUS</div>', unsafe_allow_html=True)
        st.metric("Artifacts loaded", f"{catalog.loaded_count} / {catalog.configured_count}")
        st.caption("LOCAL MODE  ·  No external service calls")
        st.caption("Historical dataset · Not a live operational feed")

    st.markdown(
        '<div class="fl-note"><strong>Evidence boundary.</strong> This workspace explores a historical event log. '
        'Elapsed event gaps are not confirmed queue or staff work time. Rankings are investigation aids; '
        'scenario reductions are assumptions, not measured impact.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    if page == "Overview":
        page_header(
            "Process performance at a glance",
            "A traceable view of case volume, elapsed duration, process variation, and the quality of current evidence.",
        )

        # KPI row — all values are derived from the existing case-level dataset.
        a, b, c, d = st.columns(4, gap="medium")
        a.metric("Applications", as_int(metrics["case_count"]))
        b.metric("Recorded event volume", as_int(metrics["event_count"]))
        acc = metrics["acceptance_rate"]
        c.metric("Accepted field = true", f"{acc:.1%}" if acc is not None else "Not available")
        d.metric("Median case duration", as_hours(metrics["median_duration_hours"]))

        durations = pd.to_numeric(cases["duration_hours"], errors="coerce")
        durations = durations[np.isfinite(durations) & (durations >= 0)]

        st.write("")
        left, right = st.columns([1.45, 1], gap="medium")

        with left:
            with st.container(border=True):
                st.subheader("Case duration distribution")
                if not durations.empty:
                    chart_frame = pd.DataFrame({"Duration (hours)": durations})
                    fig = px.histogram(
                        chart_frame,
                        x="Duration (hours)",
                        nbins=36,
                        color_discrete_sequence=["#a8e34b"],
                    )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=340,
                        margin=dict(l=8, r=8, t=8, b=8),
                        xaxis_title="First-to-last event duration (hours)",
                        yaxis_title="Applications",
                        showlegend=False,
                        font=dict(color="#cbd4c6", size=11),
                    )
                    fig.update_xaxes(showgrid=False, zeroline=False)
                    fig.update_yaxes(gridcolor="rgba(150,170,140,.13)", zeroline=False)
                    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
                else:
                    st.info("No valid non-negative duration values were found.")
                st.caption(
                    "Elapsed time from the first to the last recorded event in each application; "
                    "not active handling time."
                )

        with right:
            with st.container(border=True):
                st.subheader("Duration reference points")
                ref = pd.DataFrame({
                    "Measure": ["Mean", "Median", "90th percentile", "Invalid/missing rows"],
                    "Value": [
                        as_hours(metrics["mean_duration_hours"]),
                        as_hours(metrics["median_duration_hours"]),
                        as_hours(metrics["p90_duration_hours"]),
                        as_int(metrics["invalid_duration_count"]),
                    ],
                })
                present_table(ref, hide_index=True, width="stretch", height=210)
                st.divider()
                st.markdown("**Interpretation**")
                st.caption(
                    "These values describe case-level elapsed duration. They do not measure "
                    "staff workload, queue time, or service-level performance."
                )

        st.write("")
        activities = catalog.tables.get("activities")
        with st.container(border=True):
            st.subheader("Leading activity volumes")
            if activities is not None:
                name_col = colname(activities, ["concept:name", "activity", "activity_name"])
                n_col = colname(activities, ["event_count", "count", "frequency"])
                if name_col and n_col:
                    plot = activities[[name_col, n_col]].copy()
                    plot[n_col] = pd.to_numeric(plot[n_col], errors="coerce")
                    plot = plot.dropna().nlargest(10, n_col).sort_values(n_col)
                    fig = px.bar(
                        plot,
                        x=n_col,
                        y=name_col,
                        orientation="h",
                        color_discrete_sequence=["#a8e34b"],
                    )
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        height=390,
                        margin=dict(l=8, r=12, t=8, b=8),
                        xaxis_title="Recorded events",
                        yaxis_title="",
                        font=dict(color="#cbd4c6", size=11),
                        showlegend=False,
                    )
                    fig.update_xaxes(showgrid=False, zeroline=False)
                    fig.update_yaxes(showgrid=False, zeroline=False)
                    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
                else:
                    st.warning("The activity-count table does not contain recognised activity and count columns.")
            else:
                table(catalog, "activities")

        with st.expander("How to interpret the evidence"):
            st.markdown(
                "- **Observed:** timestamps, activity labels, recorded lifecycle states, and fields present in the exported tables.\n"
                "- **Estimated:** model outputs evaluated on the available sample.\n"
                "- **Hypothetical:** user-selected gap reductions in the Scenario Lab.\n"
                "- **Not established:** causal effects, recoverable staff hours, financial savings, or live production performance."
            )

    elif page == "Process Explorer":
        page_header("Process Explorer", "Inspect activity volumes, transition gaps, lifecycle events, and observed process paths.")
        t1, t2, t3, t4 = st.tabs(["Activity catalogue", "Transition analysis", "Path variants", "Lifecycle audits"])
        with t1:
            st.subheader("Activity frequency")
            activity_frame = catalog.tables.get("activities")
            if activity_frame is not None:
                activity_name = colname(activity_frame, ["concept:name", "activity", "activity_name"])
                activity_count = colname(activity_frame, ["event_count", "count", "frequency"])
                if activity_name and activity_count:
                    activity_plot = activity_frame[[activity_name, activity_count]].copy()
                    activity_plot[activity_count] = pd.to_numeric(activity_plot[activity_count], errors="coerce")
                    activity_plot = activity_plot.dropna().nlargest(12, activity_count).sort_values(activity_count)
                    activity_fig = px.bar(activity_plot, x=activity_count, y=activity_name, orientation="h",
                                          color_discrete_sequence=["#a8e34b"],
                                          hover_data={activity_count: ":,.0f"})
                    style_plotly(activity_fig, height=390)
                    activity_fig.update_layout(xaxis_title="Recorded events", yaxis_title="")
                    st.plotly_chart(activity_fig, width="stretch", config={"displayModeBar": False})
            table(catalog, "activities", height=300)
            st.subheader("Elapsed gap before each activity event")
            wait_frame = catalog.tables.get("waits")
            if wait_frame is not None:
                wait_name = colname(wait_frame, ["concept:name", "activity", "activity_name"])
                wait_median = colname(wait_frame, ["median_wait_hours", "median_gap_hours"])
                if wait_name and wait_median:
                    wait_plot = wait_frame[[wait_name, wait_median]].copy()
                    wait_plot[wait_median] = pd.to_numeric(wait_plot[wait_median], errors="coerce")
                    wait_plot = wait_plot.dropna().nlargest(12, wait_median).sort_values(wait_median)
                    wait_fig = px.bar(wait_plot, x=wait_median, y=wait_name, orientation="h",
                                      color_discrete_sequence=["#8bbf43"])
                    style_plotly(wait_fig, height=370)
                    wait_fig.update_layout(xaxis_title="Median incoming elapsed gap (hours)", yaxis_title="")
                    st.plotly_chart(wait_fig, width="stretch", config={"displayModeBar": False})
            table(catalog, "waits", height=300)
            st.caption(
                "Each value is the elapsed time from the previous recorded event "
                "to the current activity event. It is not processing time within "
                "the activity."
            )
        with t2:
            st.subheader("Transition evidence")
            df = catalog.tables.get("transition_summary")
            if df is not None and "transition" in df.columns:
                median_col = colname(df, ["median_gap_hours"])
                if median_col:
                    chart_data = df[["transition", median_col]].copy()
                    chart_data[median_col] = pd.to_numeric(chart_data[median_col], errors="coerce")
                    chart_data = chart_data.dropna().nlargest(12, median_col).sort_values(median_col)
                    gap_fig = px.bar(chart_data, x=median_col, y="transition", orientation="h",
                                     color_discrete_sequence=["#a8e34b"])
                    style_plotly(gap_fig, height=430)
                    gap_fig.update_layout(xaxis_title="Median elapsed transition gap (hours)", yaxis_title="")
                    st.plotly_chart(gap_fig, width="stretch", config={"displayModeBar": False})
                present_table(df, width="stretch", height=360, hide_index=True)
                selected = st.selectbox("Inspect one transition", df["transition"].dropna().astype(str).tolist())
                selected_df = df[df["transition"].astype(str) == selected]
                if not selected_df.empty:
                    r = selected_df.iloc[0]
                    ca, cb, cc = st.columns(3)
                    if "transition_count" in r.index:
                        ca.metric("Occurrences", as_int(r["transition_count"]))
                    if "median_gap_hours" in r.index:
                        cb.metric("Median elapsed gap", as_hours(r["median_gap_hours"]))
                    if "p90_gap_hours" in r.index:
                        cc.metric("90th percentile", as_hours(r["p90_gap_hours"]))
                    st.caption("Gap values describe time between adjacent event records in the sorted event trace.")
        with t3:
            st.subheader("Variant summary")
            table(catalog, "variant_summary")
            st.subheader("Variant outcomes and durations")
            table(catalog, "variant_outcomes", height=440)
            st.caption("Variants depend on the activity-sequence definition and lifecycle filtering used to create them.")
        with t4:
            st.subheader("Work-item lifecycle summary")
            table(catalog, "lifecycle")
            st.subheader("Final recorded case states")
            audit_summary(catalog, "final_states")
            st.subheader("Last completed activity audit")
            audit_summary(catalog, "last_completed")

    elif page == "Predictive Evaluation":
        page_header("Predictive Evaluation", "Compare experimental models with baselines and inspect generalisation limitations.")
        st.warning("These models are exploratory. Do not use them to approve or reject real loan applicants.")
        t1, t2, t3 = st.tabs(["Duration model", "Acceptance models", "Temporal variation"])
        with t1:
            table(catalog, "duration_metrics")
            st.markdown(
                "Model selection should use a baseline comparison, MAE, and R². The current results show weak predictive performance. "
                "The model should not be presented as reliable simply because a fitted estimator exists."
            )
        with t2:
            st.subheader("Primary evaluation — intake-only features")
            st.caption(
                "Primary results use only fields available at application intake. "
                "Long target and feature definitions are available below when needed."
            )
            show_acceptance_metadata()

            st.subheader("Random holdout")
            holdout = catalog.tables.get("acceptance_metrics")
            show_holdout_metrics(holdout)
            compact_acceptance_table(catalog, "acceptance_metrics", height=150)

            st.subheader("Five-fold cross-validation")
            cv = catalog.tables.get("acceptance_cv")
            if cv is not None and not cv.empty:
                lr = cv[cv["model"].astype(str).str.casefold().eq("logistic_regression")]
                if not lr.empty:
                    row = lr.iloc[0]
                    c1, c2 = st.columns(2)
                    ba = pd.to_numeric(pd.Series([row.get("balanced_accuracy_mean")]), errors="coerce").iloc[0]
                    auc = pd.to_numeric(pd.Series([row.get("roc_auc_mean")]), errors="coerce").iloc[0]
                    c1.metric("Logistic regression · balanced accuracy", f"{ba:.1%}" if pd.notna(ba) else "Not available")
                    c2.metric("Logistic regression · ROC-AUC", f"{auc:.3f}" if pd.notna(auc) else "Not available")
            compact_acceptance_table(catalog, "acceptance_cv", height=190)
            st.caption(
                "Five-fold stratified cross-validation. Logistic Regression has the strongest "
                "mean balanced accuracy and ROC-AUC among the tested intake-only models, "
                "but overall discrimination remains weak."
            )

            st.subheader("Chronological holdout — primary temporal result")
            temporal = catalog.tables.get("acceptance_temporal")
            if temporal is not None and not temporal.empty:
                row = temporal.iloc[0]
                c1, c2, c3, c4 = st.columns(4)
                for col, label, key, fmt in [
                    (c1, "Balanced accuracy", "balanced_accuracy", "{:.1%}"),
                    (c2, "ROC-AUC", "roc_auc", "{:.3f}"),
                    (c3, "Training cases", "train_cases", "{:,.0f}"),
                    (c4, "Testing cases", "test_cases", "{:,.0f}"),
                ]:
                    value = pd.to_numeric(pd.Series([row.get(key)]), errors="coerce").iloc[0]
                    col.metric(label, fmt.format(value) if pd.notna(value) else "Not available")
            compact_acceptance_table(catalog, "acceptance_temporal", height=150)
            if temporal is not None and not temporal.empty:
                row = temporal.iloc[0]
                with st.expander("Chronological split details", expanded=False):
                    st.write(f"Training period: {row.get('train_start', 'Not available')} to {row.get('train_end', 'Not available')}")
                    st.write(f"Testing period: {row.get('test_start', 'Not available')} to {row.get('test_end', 'Not available')}")
                    st.write(f"Training accepted rate: {row.get('train_accepted_rate', 'Not available')}")
                    st.write(f"Testing accepted rate: {row.get('test_accepted_rate', 'Not available')}")
            st.warning(
                "The intake-only chronological model has balanced accuracy close to 50% "
                "and ROC-AUC close to 0.5. It has not demonstrated useful discrimination "
                "between accepted and not-accepted applications. This is one chronological "
                "holdout, not a rolling backtest."
            )

            st.divider()
            st.subheader("Exploratory analysis — credit-score features")
            st.warning(
                "Do not interpret these results as valid pre-offer prediction performance. "
                "The event log shows non-zero CreditScore values first recorded on "
                "O_Create Offer [complete] events or later. Their availability before "
                "the first offer is therefore unverified."
            )
            with st.expander("Feature comparison (exploratory)", expanded=False):
                st.caption(
                    "This comparison includes an intake-plus-credit-score feature set. "
                    "It is retained for investigation only and must not be compared with "
                    "the primary results as if it were an equally valid prediction setup."
                )
                exploratory_local_table("acceptance_feature_comparison.csv")

            with st.expander("Chronological credit-score experiment (exploratory)", expanded=False):
                st.caption(
                    "Separate temporal experiment with credit-score features. Its improved "
                    "metrics do not establish that those features were available at prediction time."
                )
                exploratory_local_table("acceptance_temporal_credit_exploratory_metrics.csv")
        with t3:
            table(catalog, "temporal_drift")
            st.caption("Month sizes vary. Rate differences are descriptive and should be interpreted alongside sample sizes and temporal validation.")

    elif page == "Opportunity Register":
        page_header("Opportunity Register", "A review queue for high-priority transitions and the next evidence required.")
        rec = catalog.tables.get("recommendations")
        if rec is None:
            table(catalog, "recommendations")
        else:
            rec = validate_recommendations(rec)
            if "priority_rank" in rec.columns:
                rec = rec.sort_values("priority_rank", na_position="last")
            if "recommendation_type" in rec.columns:
                opts = ["All types"] + sorted(rec["recommendation_type"].dropna().astype(str).unique().tolist())
                choice = st.selectbox("Recommendation type", opts)
                if choice != "All types":
                    rec = rec[rec["recommendation_type"].astype(str) == choice]
            q = st.text_input("Search by transition or recommendation", placeholder="e.g. suspend, cancellation, follow-up")
            if q:
                fields = [c for c in ["transition", "recommendation_type", "recommended_investigation", "evidence_quality"] if c in rec.columns]
                mask = pd.Series(False, index=rec.index)
                for field in fields:
                    mask |= rec[field].astype(str).str.contains(q, case=False, na=False)
                rec = rec[mask]
            if not rec.empty and "transition" in rec.columns:
                score_col = colname(rec, ["screening_score", "priority_rank"])
                if score_col:
                    score_plot = rec[["transition", score_col]].copy()
                    score_plot[score_col] = pd.to_numeric(score_plot[score_col], errors="coerce")
                    score_plot = score_plot.dropna().head(12)
                    if not score_plot.empty:
                        score_fig = px.bar(score_plot.sort_values(score_col), x=score_col, y="transition",
                                           orientation="h", color_discrete_sequence=["#a8e34b"])
                        style_plotly(score_fig, height=390)
                        score_fig.update_layout(xaxis_title=friendly_column_name(score_col), yaxis_title="")
                        st.plotly_chart(score_fig, width="stretch", config={"displayModeBar": False})
            present_table(rec, width="stretch", height=460, hide_index=True)
            if not rec.empty and "transition" in rec.columns:
                picked = st.selectbox("Open an opportunity", rec["transition"].astype(str).tolist())
                r = rec[rec["transition"].astype(str) == picked].iloc[0]
                st.subheader("Investigation brief")
                st.markdown(f"**Type:** {r.get('recommendation_type', 'Not specified')}")
                st.markdown(f"**Evidence rating:** {r.get('evidence_quality', 'Not specified')}")
                st.write(r.get("recommended_investigation", "Review representative case timelines and validate with a process owner."))
                st.caption(r.get("interpretation_warning", "Treat as a screening hypothesis until validated."))
            st.download_button("Export current register", rec.to_csv(index=False).encode("utf-8"),
                               file_name="veylora_opportunity_register.csv", mime="text/csv")

    elif page == "Scenario Lab":
        page_header("Scenario Lab", "Test assumptions about elapsed-gap reductions without misrepresenting them as impact estimates.")
        st.warning("Scenario values are hypothetical assumptions. They are not measured effects, unique-case savings, or end-to-end duration reductions.")
        rec = catalog.tables.get("recommendations")
        if rec is None:
            table(catalog, "recommendations")
        else:
            rec = validate_recommendations(rec)
            percent = st.slider("Assumed reduction in median elapsed gap", 0, 50, 20, 5, format="%d%%")
            n_default = min(10, len(rec))
            n = st.slider("Candidates to compare", 1, max(1, len(rec)), n_default)
            try:
                scenario = simulate_gap_reduction(rec, percent, max_rows=n)
                columns = [c for c in ["transition", "transition_count", "median_gap_hours", "assumed_reduction_percent",
                                       "hypothetical_median_gap_hours", "illustrative_hours_across_occurrences", "savings_verified"] if c in scenario.columns]
                if {"transition", "median_gap_hours", "hypothetical_median_gap_hours"}.issubset(scenario.columns):
                    scenario_plot = scenario[["transition", "median_gap_hours", "hypothetical_median_gap_hours"]].copy()
                    scenario_plot["median_gap_hours"] = pd.to_numeric(scenario_plot["median_gap_hours"], errors="coerce")
                    scenario_plot["hypothetical_median_gap_hours"] = pd.to_numeric(scenario_plot["hypothetical_median_gap_hours"], errors="coerce")
                    scenario_plot = scenario_plot.dropna().head(12)
                    if not scenario_plot.empty:
                        scenario_long = scenario_plot.melt(id_vars="transition", var_name="Scenario", value_name="Hours")
                        scenario_fig = px.bar(scenario_long, x="Hours", y="transition", color="Scenario",
                                              barmode="group",
                                              color_discrete_map={"median_gap_hours":"#a8e34b",
                                                                  "hypothetical_median_gap_hours":"#6c8c52"})
                        style_plotly(scenario_fig, height=430, legend=True)
                        scenario_fig.update_layout(xaxis_title="Median elapsed gap (hours)", yaxis_title="")
                        st.plotly_chart(scenario_fig, width="stretch", config={"displayModeBar": False})
                present_table(scenario[columns], width="stretch", height=450, hide_index=True)
                st.download_button("Export scenario table", scenario.to_csv(index=False).encode("utf-8"),
                                   file_name="veylora_hypothetical_scenario.csv", mime="text/csv")
            except ValueError as exc:
                st.error(f"Scenario could not be calculated: {exc}")
            st.markdown(
                '<div class="fl-note"><strong>Interpretation rule.</strong> The occurrence-level arithmetic is shown for traceability only. '
                'Do not add it across transitions or report it as realised savings: events may overlap within a case, '
                'and observed gaps may include customer response time, business rules, or other elapsed intervals.</div>',
                unsafe_allow_html=True,
            )

    elif page == "Evidence & Governance":
        page_header("Evidence & Governance", "Data readiness, analytical assumptions, reproducibility, and responsible-use boundaries.")
        st.subheader("Artifact inventory")
        inventory = []
        for key, filename in ARTIFACTS.items():
            frame = catalog.tables.get(key)
            issue = next((x for x in catalog.issues if x.key == key), None)
            inventory.append({
                "Artifact": filename,
                "Status": "Loaded" if frame is not None else "Unavailable",
                "Rows": len(frame) if frame is not None else None,
                "Columns": len(frame.columns) if frame is not None else None,
                "Note": "" if issue is None else issue.message,
            })
        present_table(pd.DataFrame(inventory), width="stretch", hide_index=True)

        st.subheader("Known analytical caveats")
        st.markdown(
            "- **Dataset scope:** the installed working log is a historical research dataset/subset, not a connected production source.\n"
            "- **Data semantics:** zero-valued credit scores require domain clarification before modelling.\n"
            "- **Lifecycle records:** start, suspend, resume, complete, abort, and withdrawal events describe work-item states and are not interchangeable.\n"
            "- **Outcome overlap:** the Accepted field does not map cleanly to a single final event in the current analysis.\n"
            "- **Prediction:** recorded model results include weak and temporally unstable performance.\n"
            "- **Causal inference:** no intervention effect is claimed. A future analysis must specify treatment timing, confounders, assumptions, uncertainty, overlap, and sensitivity checks.\n"
            "- **Autonomy:** the current recommendation engine is deterministic ranking logic, not an autonomous AI agent.\n"
            "- **Live mode:** not connected. Any future event replay must be explicitly labelled simulated."
        )
        st.subheader("Risk management reference points")
        st.markdown(
            "This prototype uses the following as design references, not certifications: "
            "[NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework), "
            "[ISO/IEC 42001:2023](https://www.iso.org/standard/42001), and "
            "[OWASP Top 10:2025](https://top10.owasp.org/2025/). "
            "Applicable privacy obligations depend on jurisdiction, data, roles, and effective dates."
        )
        st.subheader("Current data issues")
        table(catalog, "correlations")
        table(catalog, "outcome_summary")
        table(catalog, "outcome_duration")
        table(catalog, "rework")

    elif page == "Autonomous Optimization":
        from flowlens.optimization_ui import render_optimization_workspace
        render_optimization_workspace(catalog)

    elif page == "AI Assistant":
        page_header(
            "AI Assistant",
            "Ask questions about your local process-analysis evidence using a locally running language model.",
        )

        st.markdown(
            "The assistant uses selected analytical summaries, not the full raw event log. "
            "Its explanations are AI-generated interpretations, not proof of root causes or business impact."
        )

        from flowlens.ai_assistant import LocalAIError, ask_local_ai

        with st.expander("About the local AI connection"):
            st.write(
                "Veylora sends prompts and selected evidence to Ollama on this computer. "
                "No paid AI API is used by this assistant."
            )
            st.caption(
                "If Ollama is not running, start it and make sure the model is available "
                "with `ollama list`."
            )

        rec = catalog.tables.get("recommendations")
        waits = catalog.tables.get("waits")

        evidence = {
            "data_scope": "Historical BPI 2017 process-log analysis; not a live operational feed.",
            "activity_gap_definition": (
                "For each activity event, the activity-level gap is the elapsed "
                "time from the immediately previous recorded event in the same "
                "application to this event. It is not time spent inside the activity."
            ),
            "transition_gap_definition": (
                "A lifecycle transition-level gap is the elapsed time between "
                "consecutive recorded lifecycle event records in the same application."
            ),
            "transition_dataset_definitions": {
                "activity_transitions": (
                    "Activity-to-activity transitions: consecutive activity names "
                    "in a case, counted in activity_transitions.csv. Each row has "
                    "source_activity, next_activity, and transition_count."
                ),
                "transition_statistics": (
                    "Lifecycle-specific transitions: event lifecycle state changes "
                    "such as suspend, resume, complete, and abort, with elapsed-gap "
                    "statistics. This is not the same as activity-to-activity transitions."
                ),
            },
            "interpretation_limits": [
                "Activity-level gaps measure elapsed time from the previous recorded event to the current activity event; they are not time spent processing that activity.",
                "Transition-level gaps measure elapsed time between consecutive event records in a case.",
                "Neither measure is confirmed queue time, staff work time, or processing time.",
                "Causal effects have not been established.",
                "Scenario reductions are assumptions, not measured savings.",
                "Recommendations are screening aids that require case review and process-owner validation.",
                "transition_count is a count of transition occurrences in the source table, not necessarily a count of unique applications.",
                "applications_observed is a separate metric. Never treat it as interchangeable with transition_count.",
                "If transition_count exceeds applications_observed, report both separately and flag their definitions for verification; do not assume the cause.",
                "Use only the supplied figures. Do not invent counts, root causes, or explanations for differences.",
            ],
            "recommendations": [],
            "transition_statistics": [],
            "activity_transitions": [],
            "activity_wait_statistics": [],
        }

        # Activity-to-activity transitions come from activity_transitions.csv.
        # Keep them separate from lifecycle-specific transition statistics.
        activity_transitions = catalog.tables.get("transitions")
        if activity_transitions is not None:
            required_activity_columns = ["concept:name", "next_activity", "transition_count"]
            if all(column in activity_transitions.columns for column in required_activity_columns):
                selected_activity_transitions = activity_transitions[required_activity_columns].copy()
                selected_activity_transitions = selected_activity_transitions.rename(
                    columns={"concept:name": "source_activity"}
                )
                selected_activity_transitions["transition"] = (
                    selected_activity_transitions["source_activity"].astype(str)
                    + " -> "
                    + selected_activity_transitions["next_activity"].astype(str)
                )
                selected_activity_transitions["transition_count"] = pd.to_numeric(
                    selected_activity_transitions["transition_count"], errors="coerce"
                )
                selected_activity_transitions = selected_activity_transitions.dropna(
                    subset=["transition_count"]
                )
                selected_activity_transitions = selected_activity_transitions.astype(object).where(
                    pd.notna(selected_activity_transitions), None
                )
                evidence["activity_transitions"] = selected_activity_transitions.to_dict("records")

        # Include a separate, traceable lifecycle transition summary so the AI can
        # distinguish transition occurrences from observed applications.
        transitions = catalog.tables.get("transition_summary")
        if transitions is not None:
            transition_columns = [
                "transition",
                "transition_count",
                "applications_observed",
                "median_gap_hours",
                "p90_gap_hours",
            ]
            transition_columns = [c for c in transition_columns if c in transitions.columns]
            if transition_columns:
                selected_transitions = transitions[transition_columns].copy()
                if "median_gap_hours" in selected_transitions.columns:
                    selected_transitions["median_gap_hours"] = pd.to_numeric(
                        selected_transitions["median_gap_hours"], errors="coerce"
                    )
                    selected_transitions = selected_transitions.sort_values(
                        "median_gap_hours", ascending=False, na_position="last"
                    )
                selected_transitions = selected_transitions.astype(object).where(
                    pd.notna(selected_transitions), None
                )
                evidence["transition_statistics"] = selected_transitions.to_dict("records")

        if rec is not None:
            recommendation_columns = [
                "priority_rank",
                "transition",
                "transition_count",
                "applications_observed",
                "median_gap_hours",
                "p90_gap_hours",
                "recommendation_type",
                "recommended_investigation",
                "evidence_quality",
                "causal_effect_established",
                "confirmed_queue_time",
                "scenario_reduction_is_assumption",
                "interpretation_warning",
            ]
            recommendation_columns = [c for c in recommendation_columns if c in rec.columns]
            selected_recommendations = rec[recommendation_columns].copy()
            selected_recommendations = selected_recommendations.astype(object).where(
                pd.notna(selected_recommendations), None
            )
            evidence["recommendations"] = selected_recommendations.to_dict("records")

        if waits is not None:
            wait_columns = [
                "concept:name",
                "event_count",
                "median_wait_hours",
                "mean_wait_hours",
            ]
            wait_columns = [c for c in wait_columns if c in waits.columns]
            selected_waits = waits[wait_columns].copy()
            selected_waits = selected_waits.astype(object).where(pd.notna(selected_waits), None)
            evidence["activity_wait_statistics"] = selected_waits.to_dict("records")

        st.subheader("Ask about your process evidence")
        question = st.text_area(
            "Your question",
            placeholder=(
                "Example: Which transition should we investigate first, and what are the limitations?"
            ),
            height=110,
        )

        col_ask, col_check = st.columns([2, 1])
        with col_ask:
            ask_clicked = st.button("Ask Veylora AI", type="primary", width="stretch")
        with col_check:
            check_clicked = st.button("Check connection", width="stretch")

        if check_clicked:
            try:
                with st.spinner("Checking the local model…"):
                    connection_answer = ask_local_ai(
                        "Reply with one short sentence confirming you can explain supplied process evidence.",
                        {"project": "Veylora", "mode": "local evidence-based explanation"},
                    )
                st.success("Local AI connection successful.")
                st.write(connection_answer)
            except (LocalAIError, ValueError) as exc:
                st.error(f"Local AI is not available: {exc}")
            except Exception as exc:
                st.error(f"Unexpected AI error ({type(exc).__name__}): {exc}")

        if ask_clicked:
            if not question.strip():
                st.warning("Enter a question first.")
            elif not evidence["recommendations"] and not evidence["transition_statistics"] and not evidence["activity_transitions"] and not evidence["activity_wait_statistics"]:
                st.error(
                    "No recommendation or activity-wait evidence is loaded. "
                    "Check the processed-data directory in the sidebar configuration."
                )
            else:
                try:
                    with st.spinner("Asking your local model… this may take a little while."):
                        focused_evidence = focus_evidence(question, evidence)
                        answer = ask_local_ai(question, focused_evidence)
                    st.subheader("AI explanation")
                    with st.container(border=True):
                        st.markdown(answer)
                    st.caption(
                        "AI-generated interpretation of the selected evidence. "
                        "Verify important figures against the source tables; this is not causal proof."
                    )
                    with st.expander("Inspect evidence supplied to the model"):
                        st.json(focused_evidence)
                except (LocalAIError, ValueError) as exc:
                    st.error(f"Could not get an answer from local AI: {exc}")
                except Exception as exc:
                    st.error(f"Unexpected AI error ({type(exc).__name__}): {exc}")

    st.divider()
    st.caption("Veylora 0.2.0 · Local research prototype · No production compliance or model-performance claim")


if __name__ == "__main__":
    main()
