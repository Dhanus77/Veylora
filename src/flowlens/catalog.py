"""Explicit, testable loading of the project's existing analytical artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import pandas as pd

ARTIFACTS: Mapping[str, str] = {
    "cases": "case_level_dataset.csv",
    "activities": "activity_counts.csv",
    "transitions": "activity_transitions.csv",
    "waits": "activity_wait_statistics.csv",
    "recommendations": "improvement_recommendations.csv",
    "scenarios": "process_optimization_scenarios.csv",
    "variants": "case_variant_mapping.csv",
    "variant_summary": "process_variant_summary_v2.csv",
    "variant_outcomes": "variant_outcome_analysis.csv",
    "duration_metrics": "duration_model_metrics_v2.csv",
    "acceptance_metrics": "acceptance_model_metrics.csv",
    "acceptance_cv": "acceptance_cross_validation_metrics.csv",
    "acceptance_features": "acceptance_feature_comparison.csv",
    "acceptance_temporal": "acceptance_temporal_metrics.csv",
    "temporal_drift": "temporal_drift_analysis.csv",
    "outcome_summary": "case_outcome_summary.csv",
    "outcome_duration": "case_outcome_duration_comparison.csv",
    "correlations": "case_feature_correlations.csv",
    "lifecycle": "work_lifecycle_summary.csv",
    "transition_summary": "lifecycle_transition_summary.csv",
    "rework": "rework_summary_v2.csv",
    "final_states": "final_case_states.csv",
    "last_completed": "last_completed_activity_audit.csv",
}

REQUIRED_CASE_COLUMNS = {"case:concept:name", "duration_hours", "event_count", "Accepted"}


@dataclass(frozen=True)
class ArtifactIssue:
    """Describes a missing or invalid artifact without exposing file contents."""

    key: str
    filename: str
    message: str


@dataclass
class DataCatalog:
    """Loaded tables and diagnostics for a local processed-data directory."""

    data_dir: Path
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    issues: list[ArtifactIssue] = field(default_factory=list)

    @property
    def loaded_count(self) -> int:
        return len(self.tables)

    @property
    def configured_count(self) -> int:
        return len(ARTIFACTS)

    @property
    def cases(self) -> pd.DataFrame | None:
        return self.tables.get("cases")

    @property
    def ready(self) -> bool:
        return self.cases is not None and not any(
            issue.key == "cases" for issue in self.issues
        )


def _read_csv(path: Path) -> pd.DataFrame:
    """Read a CSV with stable parser settings; errors are handled by the catalog."""
    return pd.read_csv(path, low_memory=False)


def load_catalog(data_dir: str | Path) -> DataCatalog:
    """Load available artifacts and record each missing/invalid file explicitly.

    Only the case table is mandatory to run the overview. Other artifact tables
    are optional, so the interface can tell the user exactly which analysis
    views are unavailable without pretending the data exists.
    """
    root = Path(data_dir).expanduser().resolve()
    catalog = DataCatalog(data_dir=root)

    for key, filename in ARTIFACTS.items():
        path = root / filename
        if not path.is_file():
            catalog.issues.append(
                ArtifactIssue(key, filename, "File not found in processed-data directory.")
            )
            continue
        try:
            frame = _read_csv(path)
        except (OSError, pd.errors.ParserError, UnicodeError, ValueError) as exc:
            catalog.issues.append(
                ArtifactIssue(key, filename, f"Could not read CSV ({type(exc).__name__}).")
            )
            continue
        catalog.tables[key] = frame

    cases = catalog.tables.get("cases")
    if cases is not None:
        missing_columns = sorted(REQUIRED_CASE_COLUMNS - set(cases.columns))
        if missing_columns:
            catalog.tables.pop("cases", None)
            catalog.issues.append(
                ArtifactIssue(
                    "cases",
                    ARTIFACTS["cases"],
                    "Required columns are missing: " + ", ".join(missing_columns),
                )
            )

    return catalog
