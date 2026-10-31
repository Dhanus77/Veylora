# Veylora --- Model and Analytics Card

## 1. Intended Use

Veylora supports exploratory analysis of a historical loan-application
event log, including process-duration and outcome-related patterns,
predictive model evaluation, opportunity screening, and controlled
synthetic experimentation.

It is intended for research, development, and portfolio demonstration.

It is **not** intended for real applicant-level approval or rejection
decisions, credit decisions, or autonomous operational control.

## 2. System Components Covered

This card describes the predictive and statistical components used by
Veylora. It does not describe every analytical feature as a trained
machine-learning model.

  -----------------------------------------------------------------------
  Component               Purpose                 Data basis
  ----------------------- ----------------------- -----------------------
  Duration prediction     Estimate case elapsed   Historical case-level
                          duration                features

  Acceptance prediction   Explore prediction of   Historical case-level
                          the case-level          features
                          `Accepted` label        

  Causal estimator        Estimate                Randomized synthetic
                          treatment-control       experiment data
                          differences             

  Process simulator       Generate controlled     Configurable simulation
                          synthetic intervention  assumptions
                          data                    

  Opportunity screening   Rank candidate          Historical process
                          investigations          statistics and
                                                  heuristic scores

  Optimization agent      Coordinate tools and    Registered tools,
                          candidate evaluation    historical evidence,
                                                  and synthetic
                                                  experiment outputs
  -----------------------------------------------------------------------

## 3. Data

The working source is the BPI Challenge 2017 historical loan-application
event log.

The current project notes report: - 1,592 historical applications. -
71,397 event records. - 23 configured analytical artifacts.

These counts must be revalidated against the exact dataset version and
input files before publication.

The data are historical and observational. They do not contain a
validated randomized intervention assignment for estimating the causal
impact of the candidate process changes considered by the optimization
workflow.

## 4. Duration Prediction

### Intended target

`duration_hours`, representing the elapsed interval between the first
and last recorded event for a case.

This is not active processing time, staff working time, or verified
queue time.

### Models and baseline

The recorded experiments compared a median-duration baseline with Random
Forest regression variants.

### Reported results

An earlier recorded comparison reported:

  Model                                      MAE
  ----------------- ----------------------------
  Median baseline     Approximately 276.37 hours
  Random Forest       Approximately 280.61 hours

The compared models had negative R² values in that recorded evaluation.

A later diagnostic record reported:

  Model                                      MAE                      R²
  ----------------- ---------------------------- -----------------------
  Median baseline     Approximately 276.37 hours   Approximately -0.1625
  Random Forest       Approximately 271.24 hours   Approximately -0.1262

The available notes do not establish that these two comparisons used
identical splits and configurations. They should not be treated as
directly interchangeable results.

### Interpretation

The recorded predictive performance is weak. The later Random Forest
result shows only a small MAE improvement over the baseline, while the
negative R² indicates performance below the test-set mean predictor
under that evaluation.

Do not present this model as a reliable operational duration predictor.

## 5. Acceptance Prediction

### Intended target

The case-level dataset field `Accepted`.

Its precise business meaning and relationship to final process
activities have not been fully validated.

### Reported evaluation

Existing intake-only experiments were reported as weak. A chronological
holdout produced approximately:

-   Balanced accuracy: 0.502.
-   ROC AUC: 0.523.

Poor recall for the negative class was also reported.

Random cross-validation results were reported to improve when a
zero-flagged credit-score feature was included. However, the semantics
of `CreditScore` zero values and their availability at the intended
prediction time are unresolved.

### Interpretation

These results do not support real applicant-level decisions. The target
definition, feature timing, data semantics, temporal evaluation,
calibration, subgroup performance, and fairness considerations require
further validation.

## 6. Causal Estimation

### Intended use

The causal engine estimates treatment-control differences on randomized
data generated by the process simulator.

The estimator calculates: - Difference in group means. - Standard
error. - Confidence interval. - Statistical significance.

### Historical observational data

The current historical analysis does not establish a defensible
identification strategy for the proposed interventions. The historical
causal assessment therefore reports `not_identified` rather than
presenting an observational association as a causal effect.

### Interpretation

The estimator's operation on randomized synthetic data demonstrates the
statistical workflow under the simulator's assumptions. It does not
establish causal effects in the historical BPI dataset or in a real
business process.

## 7. Process Simulator

The simulator generates synthetic loan-application process data with
randomized treatment assignment and a configurable intervention effect
on duration.

Its purpose is to test the experiment and estimation pipeline under
controlled assumptions.

Synthetic outputs must be labelled as simulated and must not be
described as observed historical results or verified business savings.

## 8. Opportunity Screening and Optimization Agent

The opportunity register uses historical process evidence, including
activity transitions, frequencies, elapsed gaps, and application counts,
to identify candidates for investigation.

The optimization agent: - Retrieves historical process information. -
Reads prioritized opportunities. - Selects analytical tools based on
observed findings. - Assesses historical causal identification. -
Evaluates candidate investigations using synthetic experiments. -
Applies an acceptance-quality guardrail. - Ranks candidates and produces
a recommendation. - Records tool execution traces and audit information.

The current agent uses adaptive rule-based tool selection. It is not an
unrestricted autonomous language-model planner and does not execute
operational changes.

Opportunity screening scores are prioritisation heuristics, not verified
financial or operational value.

## 9. Known Limitations and Risks

-   Historical data are observational and may reflect changing process
    policies.
-   Event gaps are elapsed intervals between recorded events, not
    necessarily queue or active processing time.
-   Outcome semantics are not fully validated.
-   `CreditScore` zero values are common and are not domain-validated.
-   A single chronological holdout is not a rolling backtest.
-   Calibration, subgroup performance, cost-sensitive decision analysis,
    and formal fairness review have not been completed.
-   Synthetic experiment results depend on simulator assumptions.
-   Predictive performance is weak and should be interpreted against
    baselines.
-   Candidate recommendations require domain review and human approval.

## 10. Deployment Decision

The predictive models and analytical components are **not suitable for
production decisions**.

Use the current implementation only for process-analysis research,
controlled synthetic experimentation, software demonstration, and
portfolio evaluation until data semantics, evaluation methodology,
domain validation, governance, and intended-use controls are
substantially strengthened.

## 11. Further Evaluation Required

-   Re-run all predictive experiments against a fingerprinted dataset
    version.
-   Record exact splits, feature sets, configurations, and software
    versions.
-   Validate target semantics and prediction-time feature availability.
-   Compare against appropriate baselines using temporal evaluation.
-   Add rolling temporal backtests where appropriate.
-   Evaluate calibration and subgroup performance.
-   Investigate the meaning of zero-valued credit-score records.
-   Conduct causal sensitivity and robustness analysis for any future
    observational study.
-   Validate simulator assumptions with domain expertise before
    interpreting candidate scenarios.
