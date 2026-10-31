# Veylora --- Product Roadmap

## 1. Purpose

This roadmap records the current implementation baseline and separates
completed development from further validation and future research.

The roadmap is focused on a local-first business process intelligence
and optimization application. Completion of a development phase does not
imply production readiness or verified operational impact.

## 2. Phase 0 --- Project Foundation

**Status: Completed**

-   Consolidated application code, tests, documentation, and analytical
    artifacts.
-   Established a reproducible Windows development environment.
-   Configured the application entry point and local startup script.
-   Organised source code, analysis scripts, data, and documentation.
-   Established automated tests and project documentation.

**Recorded acceptance evidence:** The application launches locally,
Python compilation succeeded, and the latest recorded automated test run
passed 31 tests.

## 3. Phase 1 --- Interactive Application

**Status: Implemented**

-   Built a Streamlit application with eight interactive workspaces.
-   Implemented a data catalog for configured analytical artifacts.
-   Added process overview and exploration capabilities.
-   Added predictive evaluation views.
-   Added an opportunity register and scenario exploration.
-   Added evidence and governance information.
-   Implemented deterministic analytical query and ranking capabilities
    in the AI Assistant.
-   Integrated the Autonomous Optimization workspace.

**Recorded acceptance evidence:** Eight workspaces are integrated and
the current catalog contains 23 configured analytical artifacts.

## 4. Phase 2 --- Historical Process Analysis

**Status: Implemented, with further validation required**

-   Analysed activity frequencies and observed event transitions.
-   Examined lifecycle behaviour and process variants.
-   Inspected case outcomes, repeated activities, and elapsed intervals.
-   Compared duration and acceptance models against baselines.
-   Preserved distinctions between observed measurements and
    hypothetical calculations.
-   Identified candidate process improvement opportunities from
    historical evidence.

**Further work:**

-   Expand timestamp and event-identity validation.
-   Validate event and lifecycle counting semantics.
-   Improve reproducibility metadata and run manifests.
-   Review data-quality rules against additional datasets.
-   Validate candidate opportunities with process-domain experts.

## 5. Phase 3 --- Predictive Model Evaluation

**Status: Implemented; model performance requires improvement**

-   Implemented duration and acceptance model evaluation workflows.
-   Compared model results with baseline approaches.
-   Examined temporal evaluation results and predictive limitations.
-   Documented weak predictive performance and unresolved target/feature
    semantics.

**Further work:**

-   Re-run experiments against a fingerprinted dataset version.
-   Improve feature quality and prediction-time definitions.
-   Investigate the causes of weak predictive performance.
-   Compare alternative model families and suitable baselines.
-   Add rolling temporal backtests where appropriate.
-   Evaluate calibration and subgroup performance.

**Acceptance gate:** Any claimed improvement must be demonstrated
through reproducible evaluation against suitable baselines. Model
performance must not be overstated.

## 6. Phase 4 --- Causal Estimation and Synthetic Experimentation

**Status: Initial implementation completed; validation and research
remain**

-   Implemented a statistical estimator for randomized treatment and
    control data.
-   Added treatment-effect, standard-error, confidence-interval, and
    significance calculations.
-   Added a historical causal identification assessment that reports
    when causal effects are not identified.
-   Implemented a synthetic process simulator with randomized treatment
    assignment and configurable intervention effects.
-   Added tests for the estimator and simulator.

**Further work:**

-   Document simulator assumptions and experiment configurations more
    completely.
-   Add statistical coverage and robustness tests.
-   Conduct sensitivity analysis.
-   Define intervention-specific estimands and outcomes.
-   Validate candidate intervention definitions with domain experts.
-   Investigate appropriate causal study designs for any future
    real-world data.

**Acceptance gate:** Synthetic estimates must remain labelled as
simulated. No causal conclusion about historical or real business
outcomes should be made without a defensible identification strategy and
supporting diagnostics.

## 7. Phase 5 --- Tool-Using Autonomous Optimization

**Status: Initial implementation completed**

-   Implemented a registry of allow-listed analytical tools.
-   Added structured tool execution results and audit records.
-   Implemented adaptive, rule-based tool selection based on historical
    opportunity findings.
-   Integrated historical process evidence and causal identification
    assessment.
-   Evaluated candidate investigations using synthetic randomized
    experiments.
-   Applied an acceptance-quality guardrail.
-   Ranked candidates and generated a recommendation.
-   Added execution traces and downloadable JSON audit reports.
-   Integrated the workflow into the Autonomous Optimization workspace.

**Recorded acceptance evidence:** The workflow completed against the
working historical dataset, produced candidate comparisons and a
recommendation, and recorded seven tool executions and seven audit
records in the documented run.

**Further work:**

-   Expand agent failure-recovery tests.
-   Improve tool input validation and permission boundaries.
-   Strengthen traceability from each candidate to its supporting
    evidence.
-   Improve reproducibility of agent runs and exported reports.
-   Validate candidate definitions and guardrails with domain experts.
-   Evaluate broader planning capabilities only with explicit controls
    and measurable acceptance criteria.

**Boundary:** The current agent uses adaptive rule-based tool selection.
It is not an unrestricted autonomous language-model planner and does not
execute operational business changes.

## 8. Phase 6 --- Documentation, Governance, and Reproducibility

**Status: In progress**

-   Documented system architecture and product capabilities.
-   Documented data governance and intended-use boundaries.
-   Added model and analytics limitations.
-   Documented experiment findings and missing historical run metadata.
-   Updated local operations and release guidance.
-   Recorded known security and governance limitations.

**Further work:**

-   Generate provenance manifests automatically.
-   Record SHA-256 fingerprints, software versions, and analysis
    configurations.
-   Review dependency security and vulnerability scanning.
-   Add input size and row-count limits.
-   Define export column allow-lists.
-   Expand malformed-input and failure-path testing.
-   Review privacy and data rights before using additional datasets.

## 9. Phase 7 --- Deployment Readiness

**Status: Future work**

-   Establish deployment-specific authentication and authorisation if
    the application becomes shared or hosted.
-   Define data retention and deletion procedures.
-   Add appropriate operational monitoring and alerting.
-   Establish backup, recovery, and rollback procedures.
-   Conduct security and privacy reviews for the actual deployment
    context.
-   Validate process findings with domain experts.
-   Establish operational support and incident-handling processes.

**Acceptance gate:** Deployment readiness requires separate technical,
security, operational, privacy, data-rights, and domain-validation
reviews. Local demonstration success is not sufficient evidence of
production readiness.

## 10. Guiding Principles

1.  Preserve the distinction between implemented and planned
    functionality.
2.  Prefer reproducible analytical evidence over unsupported claims.
3.  Keep observed historical data separate from synthetic experiments.
4.  Report predictive limitations transparently.
5.  Avoid claiming causal impact without suitable evidence.
6.  Keep local operation independent of paid cloud services.
7.  Require human review before real-world operational intervention.
8.  Validate changes through automated tests and manual application
    checks.
9.  Do not describe the project as production-ready without the required
    reviews.
