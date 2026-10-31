import pandas as pd

from flowlens.catalog import load_catalog


def test_catalog_reports_missing_optional_artifacts_and_loads_cases(tmp_path):
    pd.DataFrame({
        "case:concept:name": ["A"],
        "duration_hours": [12.0],
        "event_count": [3],
        "Accepted": [True],
    }).to_csv(tmp_path / "case_level_dataset.csv", index=False)

    catalog = load_catalog(tmp_path)
    assert catalog.ready
    assert catalog.loaded_count == 1
    assert any(issue.key == "activities" for issue in catalog.issues)


def test_catalog_marks_bad_case_schema_as_not_ready(tmp_path):
    pd.DataFrame({"wrong": [1]}).to_csv(tmp_path / "case_level_dataset.csv", index=False)
    catalog = load_catalog(tmp_path)
    assert not catalog.ready
    issue = next(issue for issue in catalog.issues if issue.key == "cases")
    assert "Required columns are missing" in issue.message
