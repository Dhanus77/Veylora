# Veylora --- Local Operations Runbook

## 1. Scope

This runbook describes how to start, test, stop, and troubleshoot the
local Veylora development application on Windows.

The current project is intended for local research, development, and
demonstration. It does not provide enterprise authentication,
authorisation, production monitoring, or production data governance.

## 2. Environment

Current documented development environment:

-   Operating system: Windows
-   Python: 3.10.6
-   Virtual environment: `.venv`
-   Project root: `D:\intern\Veylora`
-   Application: Streamlit
-   Data directory: `data\processed`

Use the project's virtual environment rather than a global Python
installation.

## 3. Start the Application

Open PowerShell and move to the project root:

``` powershell
cd D:\intern\Veylora
```

Activate the virtual environment:

``` powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell policy prevents activation, invoke the environment's
Python executable directly instead.

Start the application using the project startup script:

``` powershell
.\start_veylora.bat
```

Alternatively, start Streamlit directly:

``` powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Keep the terminal running while using the application.

## 4. Run Automated Tests

Use a second PowerShell terminal so the Streamlit application can remain
running.

``` powershell
cd D:\intern\Veylora
.\.venv\Scripts\python.exe -m pytest -q
```

The latest recorded successful result was 31 passing tests. Re-run the
test suite after code changes; do not assume an earlier result still
applies.

## 5. Dependencies

If dependencies need to be installed or restored, activate the project's
virtual environment and run:

``` powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Do not install packages globally unless there is a specific
environment-management reason.

## 6. Data Location

The default processed-data directory is:

``` text
data\processed
```

The application can be configured to use another local processed-data
directory through `FLOWLENS_DATA_DIR`.

Example:

``` powershell
$env:FLOWLENS_DATA_DIR = 'D:\path\to\processed'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Only point the application at data that has been reviewed and authorised
for the intended use. Do not use an unreviewed company data directory.

## 7. Stop the Application

In the terminal running Streamlit, press:

``` text
Ctrl+C
```

Do not close or terminate unrelated Python processes as a routine
shutdown method.

## 8. Troubleshooting

### Application does not start

-   Confirm the current directory is `D:\intern\Veylora`.
-   Confirm `.venv` exists.
-   Run the application using `.\.venv\Scripts\python.exe`.
-   Read the first traceback or error message before changing
    dependencies.

### Missing case-level file

Verify that the expected file exists:

``` text
data\processed\case_level_dataset.csv
```

The case-level dataset is expected to contain the fields used by the
catalog, including:

-   `case:concept:name`
-   `duration_hours`
-   `event_count`
-   `Accepted`

If the file is missing or its schema differs, identify the relevant
offline analysis script and verify its inputs and output path before
regenerating it.

### Optional analytical view unavailable

Check the message shown by the application and confirm that the
corresponding configured artifact exists in the processed-data
directory.

Do not create placeholder data merely to hide a missing-artifact
warning.

### Dependency error

Run the dependency installation command inside the project's virtual
environment. If installation fails, preserve the error output and
inspect the package conflict before changing versions.

### Application changes are not visible

-   Save the modified source file.
-   Use Streamlit's rerun control.
-   If required, stop the app with `Ctrl+C` and restart it.

### Tests fail

-   Read the first failing assertion and traceback.
-   Identify whether the failure is caused by code, test data, or
    environment changes.
-   Do not delete or suppress a failing test merely to obtain a passing
    result.

## 9. Local Reports and Audit Outputs

The Autonomous Optimization workspace provides a downloadable JSON audit
report for an optimization run.

Inspect downloaded reports before sharing them. Check for case
identifiers, sensitive fields, local file paths, and other information
that should not be published.

Tool execution records support inspection of a particular run. They do
not constitute continuous production monitoring or a centralised audit
service.

## 10. Backup and Recovery

Before structural changes:

-   Keep a backup of important source files.
-   Preserve original raw event-log data.
-   Avoid destructive cleanup commands during troubleshooting.
-   Verify generated outputs before replacing existing artifacts.
-   Re-run the automated tests after restoring or changing source files.

Do not delete the raw dataset or processed analytical artifacts as a
routine troubleshooting step.

## 11. Operational Boundaries

-   The application is designed for local single-user development and
    demonstration.
-   No production authentication or authorisation boundary is supplied.
-   No continuous monitoring or operational alerting service is
    supplied.
-   Historical event gaps are not confirmed queue or staff-processing
    times.
-   Synthetic experiment results are not measured historical business
    outcomes.
-   Recommendations require domain review and human approval before any
    real-world action.
-   Production use requires separate security, privacy, data-rights,
    operational, and domain validation.
