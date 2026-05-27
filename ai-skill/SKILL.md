# Resolution Capsule Skill

Use this skill when a developer wants to turn a solved engineering issue, bug, incident, test failure, or RCA into a sanitized public knowledge draft.

## Goal

Create a publishable "Resolution Capsule" that preserves reusable technical value while removing workplace-specific, private, regulated, or proprietary details.

## Inputs

- Problem: what failed and why it matters.
- Environment: versions, runtime, OS, framework, cloud, CI/CD, database, or deployment context.
- Error or logs: stack trace, command output, failing test, alert, or symptom.
- Attempts: fixes tried before the root cause was known.
- Root cause: the actual cause after investigation.
- Fix: the final resolution or workaround.
- Sanitization mode: `balanced` or `strict`.

## Workflow

1. Capture only the minimum context needed to explain the issue.
2. Redact secrets, tokens, credentials, emails, internal URLs, IPs, user paths, ticket IDs, customer names, proprietary repo names, and business-specific architecture.
3. Convert specific internal details into generic public equivalents.
4. Preserve versions, error class names, public package names, public APIs, and reproducible steps when safe.
5. Produce Markdown with these sections:
   - Problem
   - Environment
   - Error or Symptom
   - What I Tried
   - Root Cause
   - Resolution
   - Suggested Tags
   - Compliance Review Notes
6. Require human review before publishing.

## Output Rules

- Never claim the capsule is safe to publish without review.
- Prefer concise, reproducible explanations over narrative incident reports.
- Do not include full proprietary code. Use small pseudocode or generalized snippets only when needed.
- Include failed attempts when they clarify the diagnosis.
- If the root cause or fix is missing, mark the draft incomplete.

## Local Engine

When this skill is used inside this repository, the local deterministic engine can be called with:

```bash
python3 capsule_cli.py --format markdown --json '{"problem":"...","rootCause":"...","fix":"...","mode":"balanced"}'
```
