# Resolution Capsule

Turn a solved debugging session into a privacy-safe, publishable knowledge draft — without leaving VS Code.

## What it does

When you fix a bug or close an incident, the context lives in your head and your editor. Resolution Capsule captures that context, automatically redacts secrets, emails, internal URLs, tokens, and private paths, and produces a Markdown draft you can post to Stack Overflow, GitHub Discussions, or your team wiki.

**Redacted automatically:**
- API keys, bearer tokens, JWTs, GitHub tokens, Slack tokens
- Emails, internal IPs, filesystem user paths, internal URLs
- Private key blocks, generic credential assignments
- Ticket IDs and long numeric identifiers *(strict mode)*

## Requirements

Python 3 must be available on your `PATH` (or configured via `resolutionCapsule.pythonPath`). The engine ships bundled with the extension — no extra install needed.

## Usage

### Create from a selection
1. Select logs, an error message, or stack trace text in any editor.
2. Open the Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`).
3. Run **Resolution Capsule: Create From Selection**.
4. Enter the root cause and fix when prompted.
5. A sanitized Markdown draft opens in a new editor tab.

### Create from prompts
1. Open the Command Palette and run **Resolution Capsule: Create From Prompts**.
2. Fill in each field (problem, environment, error, attempts, root cause, fix).
3. Review the sanitized draft that opens.

## Settings

| Setting | Default | Description |
|---|---|---|
| `resolutionCapsule.pythonPath` | `python3` | Python executable path |
| `resolutionCapsule.sanitizationMode` | `balanced` | `balanced` or `strict` |
| `resolutionCapsule.enginePath` | *(empty)* | Override path to `capsule_cli.py` |

## Source

[github.com/adivarshney/resolution-capsule](https://github.com/adivarshney/resolution-capsule)
