# Veylora --- Release Checklist

## 1. Purpose

This checklist is used before packaging, publishing, or demonstrating a
Veylora development release.

A completed local demonstration checklist does not establish production
readiness, regulatory compliance, or verified business impact.

## 2. Development Demonstration Checks

The following items have been verified during the current development
work. Re-run them after material code or environment changes.

-   [x] Local Streamlit application launched successfully.
-   [x] Eight application workspaces are integrated.
-   [x] Autonomous Optimization workflow completed against the working
    historical dataset.
-   [x] Candidate comparison and recommendation rendered in the
    application.
-   [x] Tool execution trace and audit records were produced.
-   [x] Downloadable JSON audit report was verified.
-   [x] Automated test suite passed: 31 tests.
-   [x] Synthetic experiment outputs are distinguished from historical
    observations in the optimization workflow.
-   [x] Known analytical limitations are documented.

**Verification note:** These checks reflect the latest recorded
development verification. Re-run the test suite and manually inspect the
application before creating a new release.

## 3. Product and Reproducibility

-   [ ] Confirm the application launches from the documented Windows
    command on the target environment.
-   [ ] Review all eight workspaces using both available and missing
    optional artifacts.
-   [ ] Confirm every displayed metric has a definition, unit,
    denominator, and scope.
-   [ ] Confirm outputs can be regenerated from a cited and
    fingerprinted input version.
-   [ ] Review the README and product documentation for
    implemented-versus-planned accuracy.
-   [ ] Confirm the application does not present hypotheses as verified
    business impact.
-   [ ] Record the exact source revision and dependency versions for the
    release.

## 4. Data and Privacy

-   [ ] Review the dataset licence and terms from the official source.
-   [ ] Include the dataset citation and source details in release
    materials.
-   [ ] Confirm raw and private data are excluded from Git history and
    release artifacts.
-   [ ] Review sample and export views for case identifier exposure.
-   [ ] Revalidate dataset counts against the exact input version.
-   [ ] Define data retention and deletion expectations for the intended
    deployment.
-   [ ] Confirm that synthetic data and historical data are clearly
    distinguishable.

## 5. Models, Analytics, and Causal Reasoning

-   [ ] Re-run predictive experiments against a fingerprinted dataset
    version.
-   [ ] Record baseline results, split strategy, feature set, and
    evaluation metrics.
-   [ ] Review target semantics and feature availability at prediction
    time.
-   [ ] Check for leakage and inappropriate use of post-outcome
    features.
-   [ ] Include temporal evaluation where applicable.
-   [ ] Confirm scenario assumptions are visibly separated from observed
    metrics.
-   [ ] Review causal claims against identification assumptions and
    sensitivity checks.
-   [ ] Confirm synthetic experiment results are not represented as
    historical intervention effects.
-   [ ] Document the limitations of the duration and acceptance models.

## 6. Agent and Audit Controls

-   [ ] Confirm agent tools are allow-listed and use defined inputs.
-   [ ] Verify no arbitrary shell or code execution is exposed through
    agent tools.
-   [ ] Confirm tool execution failures are represented accurately in
    the trace.
-   [ ] Inspect audit exports for identifiers, sensitive fields, and
    local paths.
-   [ ] Confirm the agent does not execute operational business changes.
-   [ ] Confirm recommendations remain subject to human review and
    approval.
-   [ ] Test malformed inputs and tool failure paths.

## 7. Security and Operations

-   [ ] Review `.gitignore` and staged changes; ensure no secrets are
    committed.
-   [ ] Review dependency versions and known vulnerabilities.
-   [ ] Test malformed and incomplete input files.
-   [ ] Confirm logs and reports avoid unnecessary sensitive raw
    records.
-   [ ] Review backup and recovery instructions.
-   [ ] Define rollback and support/issue handling for the intended
    deployment.
-   [ ] Review Streamlit network exposure and settings before any shared
    or hosted use.
-   [ ] Establish authentication and authorisation if the deployment is
    no longer single-user and local.

## 8. Communication and Claims

-   [ ] README distinguishes implemented features from planned features.
-   [ ] No claim of ISO certification or legal compliance is made
    without formal evidence.
-   [ ] No claim of real-time processing is made unless an authorised
    live event source is connected.
-   [ ] No claim of verified causal impact or realised savings is made
    from synthetic experiments.
-   [ ] Resume and portfolio descriptions accurately describe code that
    exists and has been tested.
-   [ ] Model limitations and intended-use restrictions are visible in
    release materials.

## 9. Release Decision

**Current status: Local development and portfolio demonstration.**

The current project has a working local application, an integrated
autonomous optimization workflow, a downloadable audit report, and a
recorded passing automated test suite.

The unchecked items above remain release-review tasks. Do not describe
the project as production-ready until the applicable data, security,
operational, governance, and domain-validation gates have been completed
for the actual deployment context.
