# Veylora — System Architecture

## 1. Architecture Overview

Veylora is a local-first business process intelligence and optimization platform. It combines historical process mining, analytical evaluation, causal estimation, synthetic experimentation, and an adaptive tool-using agent in an interactive Streamlit application.

The system separates the presentation layer, data catalog, analytical modules, causal engine, process simulator, agent orchestration, and audit functionality.

The application operates on preprocessed historical event-log artifacts. Synthetic randomized experiments are used to evaluate hypothetical interventions separately from historical observations.

## 2. High-Level Architecture

```text
             BPI Challenge 2017 Event Log
                         |
                         v
                Offline Analysis Scripts
                         |
                         v
                 Processed CSV Artifacts
                         |
                         v
                     Data Catalog
                         |
             +-----------+-----------+
             |                       |
             v                       v
       Process Analytics       Predictive Evaluation
             |                       |
             +-----------+-----------+
                         |
                         v
                Opportunity Register
                         |
                         v
                 Optimization Agent
                         |
              +----------+----------+
              |          |          |
              v          v          v
          Agent Tools  Causal     Process
                       Engine    Simulator
              |          |          |
              +----------+----------+
                         |
                         v
                Candidate Evaluation
                         |
                         v
                Recommendation
                         |
                         v
                  Audit Record
                         |
                         v
                 Streamlit Interface
```

## 3. Application Workspaces

The Streamlit application provides eight workspaces:

1. Overview
2. Process Explorer
3. Predictive Evaluation
4. Opportunity Register
5. Scenario Lab
6. Evidence & Governance
7. AI Assistant
8. Autonomous Optimization

## 4. Technology Stack

| Layer | Technology | Responsibility |
|---|---|---|
| Programming | Python 3.10 | Application and analytical logic |
| Presentation | Streamlit | Interactive application |
| Data processing | Pandas, NumPy | Data loading and processing |
| Visualization | Plotly | Interactive charts |
| Offline process mining | PM4Py and Python analysis scripts | Event-log analysis and artifact generation |
| Predictive evaluation | Scikit-learn | Model training and evaluation |
| Statistical estimation | SciPy | Statistical estimation and inference |
| Local AI integration | Ollama, optional | Local language-model assistance |
| Testing | Pytest | Automated validation |

The Streamlit application consumes preprocessed CSV artifacts. PM4Py is used in the offline analysis workflow rather than as a required runtime dependency of the optimization workspace.

## 5. Repository Structure

```text
Veylora/
├── app.py
├── start_veylora.bat
├── requirements.txt
├── pyproject.toml
├── analysis/
│   └── Offline analysis and evaluation scripts
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   └── Technical and governance documentation
├── exports/
├── models/
├── scripts/
├── src/
│   └── flowlens/
│       ├── agent_tools.py
│       ├── ai_assistant.py
│       ├── analytics.py
│       ├── catalog.py
│       ├── causal_engine.py
│       ├── optimization_agent.py
│       ├── optimization_ui.py
│       ├── process_simulator.py
│       └── provenance.py
└── tests/
    ├── test_agent_tools.py
    ├── test_ai_assistant.py
    ├── test_analytics.py
    ├── test_catalog.py
    ├── test_causal_engine.py
    ├── test_optimization_agent.py
    └── test_process_simulator.py
```

The internal Python package retains the `flowlens` module name for compatibility with the existing implementation.

## 6. Core Application Modules

### Application Entry Point — app.py

Manages Streamlit configuration, navigation, workspace rendering, and integration with the analytical modules.

### Data Catalog — catalog.py

Loads configured processed CSV artifacts and exposes the data required by the application. It also supports artifact availability checks.

### Analytics — analytics.py

Provides reusable analytical calculations, process metrics, and scenario-related calculations.

### Provenance — provenance.py

Provides input fingerprinting and supporting provenance functionality.

### AI Assistant — ai_assistant.py

Supports analytical queries and evidence-based responses, with optional local language-model integration.

### Agent Tools — agent_tools.py

Defines the tool registry used by the optimization agent. The tools expose process overview, bottleneck evidence, rework evidence, activity transitions, historical causal assessment, synthetic experiments, and prioritized opportunities.

Tool executions produce structured results and execution records.

### Causal Engine — causal_engine.py

Implements statistical treatment-effect estimation for randomized data.

The estimator calculates treatment-control differences, standard errors, confidence intervals, and statistical significance.

For historical observational data, the module provides an identification assessment rather than claiming a causal effect where the required identification conditions are not established.

### Process Simulator — process_simulator.py

Generates synthetic loan-application process data with randomized intervention assignment and a configurable known intervention effect.

The simulator allows the experiment and estimation pipeline to be evaluated under controlled assumptions.

Its results are not measurements of actual historical business impact.

### Optimization Agent — optimization_agent.py

Coordinates the optimization workflow through registered tools.

The agent:
- Retrieves historical process information.
- Reads prioritized opportunities.
- Selects an analytical tool based on the leading historical finding.
- Assesses historical causal identification.
- Evaluates candidate investigations using synthetic experiments.
- Applies an acceptance-quality guardrail.
- Ranks candidate interventions.
- Produces an execution trace and audit record.

The current implementation is an adaptive, rule-based tool-using agent. It is not an unrestricted autonomous language-model planner.

### Optimization UI — optimization_ui.py

Provides the Autonomous Optimization workspace, including historical opportunity evidence, candidate comparisons, experiment results, recommendations, execution traces, and downloadable JSON audit reports.

## 7. Data Organisation

### Raw Data

`data/raw/` contains locally retained BPI Challenge 2017 event-log files.

### Processed Data

`data/processed/` contains CSV artifacts generated through offline analysis.

The current catalog loads 23 configured analytical artifacts.

The working dataset contains approximately:
- 1,592 historical applications.
- 71,397 recorded events.

### Models

`models/` stores supporting model artifacts generated during offline analysis.

The presence of a saved model does not imply a deployed real-time prediction service.

## 8. Autonomous Optimization Workflow

The optimization workflow follows these stages:

1. Load historical process data through the catalog.
2. Retrieve process overview and prioritized opportunities.
3. Select the next analytical tool based on historical findings.
4. Inspect relevant process evidence.
5. Assess whether historical causal identification is justified.
6. Generate synthetic randomized experiment data for candidate investigations.
7. Estimate treatment effects and uncertainty.
8. Apply an acceptance-quality guardrail.
9. Rank candidate investigations.
10. Generate a recommendation, execution trace, and audit record.

The workflow distinguishes historical observations from synthetic experimental evidence.

## 9. Evidence and Evaluation Boundaries

- Historical event gaps represent elapsed time between recorded events; they do not independently establish queue time or active processing time.
- Historical process associations do not establish causal effects.
- Synthetic experiment effects validate the estimation workflow under simulator assumptions, not real-world intervention impact.
- Candidate screening scores are prioritization heuristics, not verified business-value measurements.
- Predictive model performance must be interpreted alongside baseline results and evaluation limitations.
- Recommendations are investigation candidates requiring human review and approval.

## 10. Design Principles

1. Keep the application local-first.
2. Separate presentation logic from analytical calculations.
3. Use explicit data catalog definitions.
4. Distinguish historical evidence from synthetic experiments.
5. Make assumptions and limitations visible.
6. Maintain an auditable record of agent tool execution.
7. Apply quality guardrails before recommending candidates.
8. Require human approval before operational intervention.
9. Avoid unsupported causal, financial, or production-readiness claims.

## 11. Execution and Deployment

The target environment is a Windows laptop running Python 3.10 or later.

The application can be started through `start_veylora.bat` or through Streamlit from the project root.

The current implementation is intended for local research, demonstration, and portfolio evaluation.

A production deployment would require additional authentication, authorization, monitoring, security controls, operational testing, and data-governance review.

## 12. Current Limitations

- Historical processed data are used rather than a live event stream.
- Event gaps do not independently establish operational queue or processing time.
- Historical causal effects are not identified by the current observational analysis.
- Synthetic experiment results depend on simulator assumptions.
- Predictive model performance is limited and requires careful interpretation.
- Agent tool selection is adaptive but rule-based.
- Recommendations are analytical candidates, not automatically executed business changes.
- The system is not a certified or production-ready enterprise deployment.