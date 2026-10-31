# Veylora — Test Strategy

## 1. Purpose

This document defines the testing approach for Veylora, a local-first business process intelligence and optimization application.

Testing focuses on analytical correctness, data handling, statistical estimation, agent tool execution, auditability, and application stability.

## 2. Testing Objectives

- Verify that analytical modules produce valid and consistent outputs.
- Validate input handling and error conditions.
- Test statistical estimation and confidence interval calculations.
- Verify synthetic experiment generation and treatment assignment.
- Confirm that agent tools execute and record their results.
- Validate the optimization workflow and candidate ranking.
- Ensure existing application functionality remains stable.

## 3. Testing Framework

| Area | Tool |
|---|---|
| Automated testing | Pytest |
| Data validation | Pandas assertions |
| Numerical validation | NumPy and SciPy |
| Application checks | Manual Streamlit testing |
| Output verification | JSON and CSV inspection |

## 4. Automated Test Coverage

The current automated suite contains 31 tests.

### 4.1 Analytics Tests

File: `tests/test_analytics.py`

Validates analytical functions and expected output behaviour.

### 4.2 Catalog Tests

File: `tests/test_catalog.py`

Validates analytical artifact registration, retrieval, and catalog behaviour.

### 4.3 AI Assistant Tests

File: `tests/test_ai_assistant.py`

Validates assistant functionality and evidence-oriented responses.

### 4.4 Causal Engine Tests

File: `tests/test_causal_engine.py`

Validates:
- Treatment and control group estimation.
- Treatment effect calculations.
- Confidence interval generation.
- Invalid treatment input handling.
- Historical causal identification assessment.

### 4.5 Process Simulator Tests

File: `tests/test_process_simulator.py`

Validates:
- Synthetic application generation.
- Randomized treatment assignment.
- Configurable intervention effects.
- Reproducibility using a fixed random seed.

### 4.6 Agent Tool Tests

File: `tests/test_agent_tools.py`

Validates:
- Tool registration.
- Tool execution.
- Tool result handling.
- Execution audit records.
- Error handling.

### 4.7 Optimization Agent Tests

File: `tests/test_optimization_agent.py`

Validates:
- Optimization workflow execution.
- Evidence retrieval.
- Adaptive tool selection.
- Candidate evaluation.
- Recommendation generation.
- Execution trace and audit information.

## 5. Running the Automated Test Suite

Run the following command from the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected latest verified result:

```text
31 passed
```

This is the latest recorded successful test result. Run the suite again after code changes before treating the result as current.

## 6. Manual Application Validation

The following checks should be performed through the Streamlit interface.

| Area | Validation |
|---|---|
| Application startup | Application opens without startup errors |
| Navigation | All eight workspaces are accessible |
| Overview | Historical application and event statistics render |
| Process Explorer | Process analysis views load |
| Predictive Evaluation | Model evaluation results display |
| Opportunity Register | Ranked opportunities are visible |
| Scenario Lab | Scenario assumptions and results render |
| Evidence & Governance | Evidence and limitation information is accessible |
| AI Assistant | Analytical queries return appropriate responses |
| Autonomous Optimization | Agent completes its workflow |
| Tool execution | Execution trace displays the tools used |
| Candidate evaluation | Candidate comparison and recommendation render |
| Audit report | JSON audit report can be downloaded and inspected |

## 7. Analytical Validation

### Historical Data

Confirm that the application loads the expected processed artifacts and reports the working dataset consistently.

Current reference dataset:
- 1,592 applications.
- 71,397 events.
- 23 configured analytical artifacts.

### Causal Estimation

Confirm that randomized synthetic treatment and control groups are used for the experiment estimator.

Check that:
- The treatment effect is calculated from group outcomes.
- Confidence intervals are returned.
- Invalid treatment inputs are rejected.
- Historical observational data are not presented as proof of causal impact.

### Synthetic Experimentation

Confirm that:
- The simulator generates reproducible data for a fixed seed.
- Treatment assignment is randomized.
- Configured effects are reflected in simulated outcomes.
- Results are labelled as synthetic.

### Optimization Agent

Confirm that:
- Historical opportunities are retrieved before candidate evaluation.
- Tool selection responds to the available opportunity evidence.
- Candidate evaluations are recorded.
- The acceptance-quality guardrail is applied.
- Recommendations retain the distinction between historical evidence and simulated results.
- Tool executions are auditable.

## 8. Release Acceptance Criteria

A development release should meet the following criteria:

- Automated tests pass.
- The application starts successfully.
- All eight workspaces render.
- The autonomous optimization workflow completes against the available dataset.
- Candidate evaluation results are displayed.
- Tool execution traces are available.
- Audit JSON can be downloaded.
- Synthetic results are clearly distinguished from historical findings.
- Known analytical limitations are documented.
- No unverified real-world impact or production-readiness claims are made.

## 9. Known Testing Limitations

- Automated unit tests do not establish production reliability.
- Manual UI checks do not replace browser-level automated testing.
- Synthetic experiments validate the estimator under simulator assumptions, not real-world intervention effects.
- Historical observational data cannot establish causal impact without an appropriate identification strategy.
- Predictive model performance remains subject to the limitations recorded in the model documentation.
- Performance and scalability under substantially larger datasets have not been comprehensively benchmarked.

## 10. Future Testing Improvements

Potential improvements include:

- Streamlit UI automation.
- Additional integration tests using malformed and incomplete event logs.
- Statistical coverage and estimator robustness tests.
- Sensitivity analysis for experiment assumptions.
- Performance tests for larger datasets.
- Reproducibility checks for generated audit reports.
- Additional agent failure-recovery and tool-permission tests.