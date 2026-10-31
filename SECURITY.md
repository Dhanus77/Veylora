# Security policy

## Current scope

FlowLens 0.1.0 is intended for local portfolio/research use. It is not a hardened multi-user web service. Do not place it on a public network or connect it to production data without completing the release gates in `docs/RELEASE_CHECKLIST.md`.

## Reporting a concern

For this portfolio repository, report a suspected vulnerability privately to the repository owner before publishing technical details. Do not publish event-log rows, credentials, internal file paths containing sensitive information, or access tokens in a report.

## Security expectations

- Keep `.env`, Streamlit secrets, personal data, raw logs and derived case-level files out of Git.
- Use least privilege for file and process permissions.
- Do not add a natural-language feature that executes arbitrary Python, SQL, PowerShell, or shell commands.
- Keep analytical tools allow-listed and validate all user-supplied tool parameters.
- Pin or constrain package versions and review dependency advisories before each release.
- Avoid logging raw case data. Log only run identifiers, event counts, tool names, status, and non-sensitive error categories unless a reviewed retention policy says otherwise.
- Recheck `.gitignore` and `git status` before every commit.
