# Veylora — Product Brief

## 1. Product Overview

**Veylora** is a local-first business process intelligence and optimization platform that analyses historical business event logs to identify process patterns, investigate operational opportunities, evaluate predictive models, and compare hypothetical interventions.

It combines process mining, statistical causal estimation, synthetic experimentation, and an adaptive tool-using agent in a unified interactive application.

**Project Title:** Autonomous Business Process Optimization using Process Mining, Causal Inference, and Tool-Using AI Agents

**Tagline:** See the process. Understand the delay. Improve the outcome.

## 2. Problem Statement

Business processes generate event logs containing records of activities, timestamps, and application outcomes. Extracting useful insights from these records often requires separate tools for process analysis, predictive evaluation, and improvement investigation.

Historical patterns alone cannot establish whether a proposed intervention will cause an improvement.

Veylora addresses this challenge by combining historical process analysis with controlled synthetic experimentation, while making assumptions, evidence boundaries, and limitations visible.

## 3. Intended Users

- Process analysts exploring historical event logs.
- Operations professionals investigating process behaviour.
- Data scientists evaluating predictive models and analytical results.
- Researchers studying process performance and improvement hypotheses.

## 4. Core Product Capabilities

### 4.1 Overview

Presents key case-level and event-level statistics, including application counts, event volumes, outcomes, and elapsed case duration.

### 4.2 Process Explorer

Supports activity frequency analysis, activity transitions, process variants, and lifecycle exploration.

### 4.3 Predictive Evaluation

Presents duration and acceptance model evaluations, baseline comparisons, and temporal evaluation results.

### 4.4 Opportunity Register

Displays candidate process improvement opportunities with supporting analytical evidence and investigation-oriented recommendations.

### 4.5 Scenario Lab

Allows users to explore hypothetical reductions in recorded process gaps using configurable assumptions.

### 4.6 Evidence & Governance

Provides visibility into analytical artifacts, data quality, evidence definitions, model limitations, and governance considerations.

### 4.7 AI Assistant

Supports deterministic evidence-based analytical queries and rankings. Optional local language-model integration is available through Ollama.

### 4.8 Autonomous Optimization

Coordinates an adaptive, tool-using optimization workflow.

The agent:
- Retrieves historical process information.
- Identifies prioritized historical opportunities.
- Selects analytical tools based on observed findings.
- Assesses historical causal identification.
- Evaluates candidate investigations through synthetic randomized experiments.
- Estimates treatment effects and confidence intervals.
- Applies an acceptance-quality guardrail.
- Ranks candidates and generates a recommendation.
- Records tool execution and audit information.

The current agent uses adaptive rule-based tool selection. It does not independently execute operational changes.

## 5. Technology Stack

| Category | Technology |
|---|---|
| Programming | Python |
| Interactive application | Streamlit |
| Data processing | Pandas, NumPy |
| Visualization | Plotly |
| Offline process mining | PM4Py and Python analysis scripts |
| Predictive evaluation | Scikit-learn |
| Statistical estimation | SciPy |
| Optional local AI | Ollama |
| Automated testing | Pytest |

## 6. Dataset and Research Scope

The project uses the BPI Challenge 2017 event log, which records a historical loan application process.

The current working analytical dataset contains:

- 1,592 historical applications.
- 71,397 recorded events.
- 23 configured analytical artifacts.

The application uses preprocessed CSV artifacts generated through offline analysis.

## 7. Evaluation Approach

Veylora separates historical observational analysis from synthetic experimental evaluation.

### Historical Analysis

Historical event-log data are used to identify process patterns, elapsed lifecycle gaps, repeated activities, and candidate improvement opportunities.

These observations are descriptive and do not independently establish causal effects.

### Synthetic Experimentation

The process simulator generates synthetic application data with randomized treatment assignment and configurable intervention effects.

The causal engine estimates treatment-control differences and associated statistical uncertainty.

This validates the estimation workflow under simulator assumptions. It does not demonstrate that the same effect will occur in real business operations.

### Candidate Evaluation

Candidate investigations are compared using simulated delay effects and an acceptance-quality guardrail.

The resulting ranking is a decision-support recommendation requiring human validation.

## 8. Analytical Boundaries

- Event gaps represent elapsed time between recorded events and do not independently establish queue time or staff processing time.
- Case duration represents the elapsed interval between the first and last recorded event.
- Recommendations are evidence-based screening candidates, not verified root causes.
- Scenario results are hypothetical, not measured intervention outcomes.
- Synthetic experiments do not establish real-world business impact.
- Observational event-log analysis does not establish causal impact.
- Predictive results must be interpreted alongside baseline performance and evaluation limitations.
- Human approval is required before operational intervention.

## 9. Deployment Scope

The current implementation is designed for local execution on Windows using Python and Streamlit.

It does not require a cloud deployment or paid API. Optional language-model assistance can use a locally hosted Ollama model.

The application is designed for research, experimentation, and demonstration rather than direct production control of business processes.

## 10. Current Project Status

The current implementation includes:

- Eight interactive workspaces.
- 23 configured analytical artifacts.
- An adaptive rule-based tool-using optimization agent.
- A statistical causal estimation module.
- A synthetic process experiment simulator.
- Candidate ranking and acceptance-quality guardrails.
- Structured tool execution traces and audit records.
- A downloadable JSON investigation report.
- An automated test suite with 31 passing tests.

The optimization workflow has been executed against the working historical dataset containing 1,592 applications.

These results establish a local development and demonstration milestone, not production readiness or verified operational impact.

## 11. Future Development

Potential future work includes:

- Stronger predictive model performance.
- Additional causal sensitivity and robustness analysis.
- Expanded process simulation and scenario evaluation.
- Improved experiment reproducibility.
- More comprehensive data-quality validation.
- Broader agent planning capabilities with controlled tool permissions.
- Additional operational monitoring and governance controls.