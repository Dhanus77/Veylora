# Veylora --- Experiment Log

This log records material analytical and optimization runs. Dates, input
fingerprints, software versions, and configurations should be completed
from the original run environment whenever available. Missing historical
metadata is explicitly marked as not recorded rather than inferred.

## 1. Experiment Recording Template

Use one entry for each material run.

-   Date/time (timezone):
-   Git commit:
-   Input artifact and SHA-256:
-   Script/command and version:
-   Question / hypothesis:
-   Population and exclusions:
-   Target and feature cutoff time:
-   Train/validation/test scheme:
-   Baseline:
-   Metrics and confidence intervals:
-   Results:
-   Known caveats / failure analysis:
-   Decision and next experiment:

------------------------------------------------------------------------

## 2. Historical Predictive Evaluation --- Duration

**Run metadata:** Exact execution date, input fingerprint, and Git
commit were not retained in the available project notes.

-   **Question:** Can the available case-level features predict elapsed
    application duration more accurately than a simple median baseline?
-   **Target:** `duration_hours`.
-   **Evaluation:** Existing model comparison on a held-out test set;
    the exact split configuration should be recovered from the original
    experiment scripts before publication.
-   **Baseline:** Median-duration baseline.
-   **Reported baseline MAE:** Approximately 276.37 hours.
-   **Reported Random Forest MAE:** Approximately 280.61 hours in the
    earlier recorded comparison.
-   **Reported R²:** Negative for the compared models.
-   **Finding:** The Random Forest did not outperform the median
    baseline in that recorded comparison. The predictive results were
    weak.
-   **Caveats:** Duration is elapsed time between recorded case events,
    not active handling time or verified queue time. The exact
    experiment should be rerun against a fingerprinted input before
    using these metrics in a formal report.
-   **Decision:** Do not present the duration model as a reliable
    operational predictor. Continue feature and evaluation research.

A later diagnostic run recorded a duration Random Forest MAE of
approximately 271.24 hours and R² of approximately -0.1262, compared
with a median baseline MAE of approximately 276.37 hours and R² of
approximately -0.1625. The available notes do not establish that this
later run used an identical split or configuration, so the two
comparisons must not be treated as directly interchangeable.

## 3. Historical Predictive Evaluation --- Acceptance

**Run metadata:** Exact execution date, input fingerprint, and Git
commit were not retained in the available project notes.

-   **Question:** Can intake-time features predict the case-level
    `Accepted` label?
-   **Evaluation:** Existing intake-only experiments included random
    cross-validation and a chronological holdout.
-   **Reported chronological evaluation:** Balanced accuracy
    approximately 0.502 and ROC AUC approximately 0.523.
-   **Finding:** The recorded chronological evaluation showed weak
    discrimination. Negative-class recall was also reported as poor.
-   **Caveats:** The meaning of `Accepted` and the prediction-time
    availability and semantics of `CreditScore` have not been fully
    validated. Zero values are common and must not be assumed to mean
    missing or genuine zero credit scores.
-   **Decision:** Do not use this model for applicant-level decisions.
    Revisit target definition, feature timing, and temporal validation.

## 4. Historical Process Analysis --- Opportunity Screening

**Run metadata:** Exact execution date, input fingerprint, and Git
commit were not retained in the available project notes.

-   **Question:** Which observed process patterns should be prioritised
    for further investigation?
-   **Population:** Working BPI Challenge 2017 analytical dataset,
    recorded as 1,592 applications and 71,397 events.
-   **Method:** Descriptive process analysis of activity transitions,
    elapsed gaps, frequencies, and application counts.
-   **Leading screening opportunity:** `W_Call after offers [suspend]`
    to `W_Call after offers [resume]`.
-   **Recorded evidence:** 1,428 transition occurrences across 1,242
    applications; median elapsed gap approximately 93.80 hours; 90th
    percentile approximately 118.33 hours; screening score approximately
    33.07.
-   **Additional observed pathways:** The transition from
    `W_Call after offers [suspend]` to `A_Cancelled [complete]` was
    recorded across 163 applications, with a median elapsed gap of
    approximately 643.43 hours.
-   **Finding:** These patterns are candidates for process-owner
    investigation.
-   **Caveats:** Elapsed gaps do not establish queue time, staff idle
    time, or causal impact. Screening scores are prioritisation
    heuristics, not verified financial or operational value.
-   **Decision:** Retain the findings as investigation hypotheses, not
    confirmed root causes or savings estimates.

## 5. Synthetic Experimentation --- Optimization Workflow

**Run metadata:** The exact execution date, random seed for each
candidate run, input fingerprint, and Git commit were not retained in
the available project notes.

-   **Question:** Can the optimization workflow compare candidate
    interventions using a controlled synthetic experiment and a
    statistical estimator?
-   **Historical input:** Working historical dataset with 1,592
    applications.
-   **Workflow:** The agent retrieved historical opportunities, selected
    a bottleneck-related analytical tool based on the leading
    suspension/follow-up finding, assessed historical causal
    identification, and evaluated three candidate investigations using
    synthetic randomized experiments.
-   **Historical causal assessment:** `not_identified`.
-   **Reported simulated candidate effects:** Approximately -18.19,
    -12.19, and -6.19 hours for the three evaluated candidates.
-   **Guardrail:** The acceptance-quality guardrail passed for the
    evaluated candidates in the recorded run.
-   **Execution evidence:** Seven tool executions and seven audit
    records were recorded.
-   **Finding:** The end-to-end local workflow completed and produced
    candidate comparisons, a recommendation, a tool trace, and a
    downloadable JSON audit report.
-   **Caveats:** The effect estimates are generated by the synthetic
    simulator under its configured assumptions. They are not measured
    reductions in the historical dataset and do not establish real-world
    intervention impact. The historical observational assessment did not
    identify a causal effect.
-   **Decision:** Treat the result as a demonstration of the
    experimental estimation and agent orchestration pipeline. Validate
    simulator assumptions and candidate definitions before any
    real-world interpretation.

## 6. Current Evidence Boundaries

1.  Historical event-log findings are descriptive unless a defensible
    causal identification strategy is established.
2.  `duration_hours` is elapsed case duration, not active processing or
    queue time.
3.  Predictive model performance is weak in the recorded evaluations and
    should be reported with its baseline and split design.
4.  Synthetic treatment effects demonstrate estimator behaviour under
    simulator assumptions, not real-world business impact.
5.  Opportunity screening scores are heuristics, not measured financial
    value.
6.  Agent execution traces establish which registered tools ran in a
    particular workflow; they do not establish that a recommended
    intervention is operationally effective.

## 7. Reproducibility Work Required

For future runs, record:

-   Exact local date and time with timezone.
-   Git commit or source snapshot.
-   SHA-256 hash of each input artifact.
-   Python and dependency versions.
-   Exact command and configuration.
-   Random seed for synthetic experiments.
-   Population, exclusions, target definition, and feature cutoff.
-   Evaluation split and baseline.
-   Metrics with uncertainty where applicable.
-   Full caveats and the decision made from the result.

Do not backfill missing metadata by guessing. Re-run an experiment when
exact reproducibility evidence is required.
