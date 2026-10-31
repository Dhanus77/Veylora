# Veylora — AI Governance and Responsible-Use Plan

## 1. Status and Scope

This document defines the current AI governance principles, controls, risks, and outstanding responsibilities for Veylora.

It is a project-level control plan informed by public frameworks. It is not an ISO certification, legal opinion, formal conformity assessment, or claim of regulatory compliance.

Veylora is intended for historical business process analysis, investigation, experimentation, and portfolio demonstration.

It is not intended to make real applicant approval or rejection decisions or autonomously control business operations.

## 2. Reference Frameworks

- **NIST AI Risk Management Framework (AI RMF):** Organise governance activities around Govern, Map, Measure, and Manage.
- **ISO/IEC 42001:2023:** Use as a reference for documented AI management practices, accountability, and continual improvement. Do not claim certification without formal assessment.
- **OWASP Top 10:2025:** Use as a security awareness reference for application design and risk review.
- **India DPDP Act and Rules:** Assess applicability, processing purposes, responsibilities, and effective dates with qualified advice before any deployment involving covered digital personal data.

These frameworks are references for project governance, not evidence that Veylora has been independently assessed against them.

## 3. Intended and Prohibited Uses

### Intended Uses

- Historical business process exploration.
- Identification of operational patterns and potential bottlenecks.
- Predictive model evaluation and comparison.
- Investigation-oriented opportunity prioritisation.
- Synthetic experimentation under explicit assumptions.
- Statistical estimation and demonstration of an experimental workflow.
- Human-reviewed analytical decision support.

### Prohibited Uses

- Autonomous approval or rejection of real loan applications.
- Automated consequential decisions about individual applicants.
- Presenting synthetic experiment results as measured business outcomes.
- Presenting historical associations as proven causal effects.
- Executing operational business changes without authorised human approval.

## 4. Governance Register

| Area | Current control or implementation | Status |
|---|---|---|
| Intended use | Historical process analysis and hypothesis generation | Documented |
| Prohibited use | No real applicant approval/rejection or autonomous operational decisions | Documented |
| Data provenance | Dataset source and local analytical artifacts identified | Partially implemented |
| Data quality | Catalog artifact availability and data checks | Implemented in scaffold |
| Predictive evaluation | Baselines and evaluation limitations documented | Existing experiments; weak results noted |
| Causal estimation | Randomized synthetic treatment-effect estimation and historical identification assessment | Implemented with limited scope |
| Human oversight | Recommendations are subject to human review; no operational action is executed | Documented boundary |
| Explainability | Historical evidence, candidate comparisons, tool traces, and audit records | Implemented in optimization workflow |
| Privacy | Local-first handling and restrictions on unreviewed company data | Foundation; further review required |
| Security | Restricted registered tools and no arbitrary shell/code execution in the agent workflow | Foundation |
| Monitoring | Per-run execution traces and audit records | Partially implemented |
| Incident handling | Recovery and release considerations documented | Further work required |

## 5. Causal Reasoning Controls

Veylora separates historical observational analysis from synthetic randomized experimentation.

### Historical Data

Historical event logs are used to identify process patterns, elapsed event gaps, repeated activities, and candidate opportunities.

These observations do not independently establish causal effects.

The historical causal identification assessment explicitly reports when the available observational evidence is insufficient to identify a causal effect.

### Synthetic Experiments

The process simulator generates synthetic application data with randomized treatment assignment and configurable intervention effects.

The causal engine estimates treatment-control differences, standard errors, confidence intervals, and statistical significance.

These results validate the estimation workflow under simulator assumptions. They do not prove that an intervention will produce the same effect in a real business process.

### Required Controls

- State the estimand and outcome clearly.
- Record treatment and control definitions.
- Preserve uncertainty estimates.
- Identify simulator assumptions.
- Separate historical observations from synthetic results.
- Avoid causal claims without a defensible identification strategy.

## 6. Agent Governance

The Autonomous Optimization workspace uses an adaptive, rule-based tool-using agent.

The current implementation:
- Uses registered analytical tools.
- Retrieves historical process evidence.
- Selects tools based on observed opportunity findings.
- Evaluates candidate investigations using synthetic experiments.
- Applies an acceptance-quality guardrail.
- Records tool execution results and audit information.
- Produces recommendations for human review.

The agent does not have unrestricted shell or arbitrary code execution capabilities in its registered tool workflow.

It does not autonomously change business processes or execute operational interventions.

The current implementation is not an unrestricted autonomous language-model planner.

## 7. Risk Register

| Risk | Why it matters | Mitigation |
|---|---|---|
| Event gap interpreted as staff idle time | May produce misleading operational conclusions | Label as elapsed time between recorded events |
| Ambiguous outcome labels | Can distort predictive evaluation | Document target definitions and prediction-time assumptions |
| CreditScore zero misinterpreted | May introduce misleading features or estimates | Treat semantics and availability as unresolved |
| Overlapping event occurrences | May inflate illustrative aggregate calculations | Do not present occurrence-level scenario hours as case savings |
| Agent invents evidence | Reduces analytical reliability | Use registered tools and structured evidence outputs |
| Sensitive data exposure | May create privacy and publication risks | Keep raw and processed data out of public releases by default |
| Synthetic results presented as historical | Misleads reviewers | Clearly label simulator-generated data and outputs |
| Unsupported causal claims | Creates false confidence in recommendations | Separate observational evidence from randomized synthetic experiments |
| Unauthorised operational action | Could affect real business outcomes | Maintain human approval boundary and no automatic execution |
| Dependency vulnerabilities | May affect application security | Review dependencies and use appropriate version constraints |

## 8. Human Oversight

Veylora provides recommendations as investigation candidates, not automatically approved business interventions.

A process owner or authorised analyst should:
- Validate the historical evidence.
- Confirm the operational meaning of identified delays.
- Review experiment assumptions.
- Assess possible effects on customers and business operations.
- Approve any real-world intervention outside the application.

The current application does not implement a complete organisational approval workflow.

## 9. Privacy and Data Handling

- Do not ingest production or directly identifying data without authorisation.
- Minimise the data used for analysis.
- Review dataset terms before redistribution.
- Avoid exposing application or case identifiers in public screenshots.
- Keep raw event logs and sensitive derived data out of public repositories.
- Define retention, deletion, and access controls before using company data.

The local prototype does not have an organisational data-protection officer, legal review, or certified information-security management system.

## 10. Auditability and Monitoring

The optimization workflow records tool execution results and audit information for individual runs.

The downloadable JSON report supports inspection of the executed workflow.

Current limitations:
- No continuous production monitoring.
- No centralised multi-user audit service.
- No operational alerting or incident-management system.
- No complete organisation-wide retention policy.

These capabilities must be assessed separately before deployment beyond the local prototype.

## 11. Release Gates

Do not describe Veylora as production-ready until the following have been reviewed for the actual deployment context:

- Dataset rights and permitted use.
- Data protection and retention requirements.
- Threat modelling and access controls.
- Dependency security.
- Reproducible tests and evaluation.
- Audit retention and monitoring.
- Backup and rollback procedures.
- Domain validation of process findings.
- Human approval and operational accountability.

## 12. Continual Improvement

Future governance improvements include:
- Stronger provenance and reproducibility manifests.
- Additional causal sensitivity and robustness checks.
- More comprehensive input validation.
- Dependency vulnerability scanning.
- Export-field and identifier reviews.
- Expanded agent failure-recovery tests.
- Formal review of deployment-specific privacy and security requirements.