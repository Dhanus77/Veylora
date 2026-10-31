# Contributing and engineering conventions

## Workflow

1. Create a focused branch for a discrete change.
2. Keep source changes separate from generated data outputs.
3. Add or update a unit test for each new metric or scenario rule.
4. Run `python -m pytest -q` and `python -m py_compile app.py src/flowlens/*.py`.
5. Run the app locally and inspect the changed page.
6. Update the relevant documentation and experiment log.
7. Review the diff and verify no raw data, credentials, generated model files, or personal data are staged.

## Coding conventions

- Prefer small functions with explicit inputs/outputs and descriptive names.
- Parse and validate data at the boundary; don't bury data cleaning inside UI code.
- Document the denominator, unit, and interpretation of each metric.
- Avoid hidden fallback behavior for mandatory data.
- Keep assumptions and warnings next to the result they qualify.
- Do not call rule-based rankings “AI reasoning” or “causal inference” unless those capabilities are actually implemented and evaluated.
- Use plain, specific writing. Avoid inflated claims such as “revolutionary,” “fully autonomous,” “real-time,” or “production-grade” without testable evidence.
