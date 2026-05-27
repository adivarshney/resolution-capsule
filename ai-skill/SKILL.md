# Resolution Capsule — AI Assistant Integration Skill

## Purpose

This skill tells an AI coding assistant (Cursor, GitHub Copilot, Claude Code, or any agent) how to automatically contribute a just-applied fix to Stack Overflow with zero extra steps from the developer.

The trigger is simple: when an AI assistant has just fixed a bug, it should invoke this skill so the fix reaches the community that indirectly made it possible.

---

## When to Invoke

Invoke this skill after any of the following:

- An AI-generated code fix has been applied and the problem is confirmed resolved
- A developer runs a command like "share this fix" or "post to Stack Overflow"
- An incident post-mortem or RCA is complete and the resolution is known
- A test failure has been diagnosed and fixed

Do **not** invoke if the fix is speculative, unverified, or still in progress.

---

## Inputs

| Field | Required | Description |
|---|---|---|
| `problem` | yes | What failed and why it mattered |
| `rootCause` | yes | The actual underlying cause |
| `fix` | yes | The applied fix — code diff, config change, or command |
| `environment` | no | Runtime, versions, OS, framework, cloud context |
| `error` | no | The error message, stack trace, or failing output |
| `attempts` | no | Things tried before the root cause was found |
| `mode` | no | `balanced` (default) or `strict` |
| `source` | no | `ai-assisted`, `manual`, or `pair-programming` |

---

## Workflow

1. **Capture** the minimum context needed to reproduce and understand the fix.
2. **Redact** automatically: secrets, tokens, emails, IPs, internal URLs, user paths, ticket IDs, proprietary names.
3. **Preserve** what is safe and useful: versions, public package names, error class names, reproducible steps.
4. **Generate** a Markdown draft with these sections:
   - Problem
   - Environment
   - Error or Symptom
   - What I Tried
   - Root Cause
   - Resolution
   - Suggested Tags
   - Compliance Review Notes
5. **Post** via the Stack Exchange API if authenticated, or surface the draft for human review.
6. **Never** claim the capsule is safe to publish without review. Always include confidence status.

---

## Output Rules

- If root cause or fix is missing, mark the draft incomplete. Do not post.
- Do not include full proprietary code. Use minimal diffs or pseudocode.
- Prefer a reproducible explanation over a narrative incident report.
- Include failed attempts when they help explain the diagnosis.
- If the fix was AI-generated, note the source in the Compliance Review Notes section.

---

## Calling the Local Engine

When running inside this repository:

```bash
python3 capsule_cli.py \
  --format json \
  --source "ai-assisted" \
  --json '{"problem":"...","rootCause":"...","fix":"...","mode":"balanced"}'
```

Or pipe from a script:

```bash
echo '{"problem":"...","rootCause":"...","fix":"...","source":"ai-assisted"}' \
  | python3 capsule_cli.py --format json
```

---

## Integrating into an Agent Loop

If you are an agent deciding whether to invoke this skill, use this heuristic:

```
if fix_was_applied and problem_is_resolved and context_has_root_cause:
    invoke resolution_capsule(source="ai-assisted", ...)
```

The skill is cheap to invoke and the worst outcome is a draft that doesn't get posted. The best outcome is a contribution that helps hundreds of developers who hit the same bug.
