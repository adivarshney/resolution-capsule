# Resolution Capsule

AI coding assistants fix bugs using Stack Overflow knowledge. This extension makes those fixes go back to Stack Overflow automatically.

## How it works

1. Your AI assistant applies a fix
2. Run **Resolution Capsule: Create from AI Fix**
3. The extension captures your git diff as the fix, you describe the problem in two prompts
4. A sanitized draft opens — one click posts it to Stack Overflow

No copy-pasting. No manual redaction. No tab-switching.

## Requirements

Python 3 on your `PATH` (or set `resolutionCapsule.pythonPath`). The sanitization engine ships bundled — no extra install.

## Commands

| Command | What it does |
|---|---|
| **Create from AI Fix** | Captures your current git diff as the fix — the main workflow |
| **Create From Selection** | Use selected text (logs, error, RCA notes) as the error field |
| **Create From Prompts** | Fill in all fields manually |
| **Connect Stack Overflow** | OAuth login — required once for auto-posting |
| **Disconnect Stack Overflow** | Revokes stored token |

## Stack Overflow Setup

Register a free app at [stackapps.com/apps/oauth/register](https://stackapps.com/apps/oauth/register) with OAuth domain `localhost`. Then add your credentials in VS Code settings:

- `resolutionCapsule.stackOverflow.clientId`
- `resolutionCapsule.stackOverflow.clientSecret`
- `resolutionCapsule.stackOverflow.apiKey` *(optional — raises quota from 300 to 10,000/day)*

Run **Connect Stack Overflow** once to authorise. After that, every capsule gets a "Post to Stack Overflow" button.

## Settings

| Setting | Default | Description |
|---|---|---|
| `resolutionCapsule.pythonPath` | `python3` | Python executable path |
| `resolutionCapsule.sanitizationMode` | `balanced` | `balanced` or `strict` |
| `resolutionCapsule.enginePath` | *(empty)* | Override path to `capsule_cli.py` |
| `resolutionCapsule.stackOverflow.clientId` | *(empty)* | From stackapps.com |
| `resolutionCapsule.stackOverflow.clientSecret` | *(empty)* | From stackapps.com |
| `resolutionCapsule.stackOverflow.apiKey` | *(empty)* | From stackapps.com |

## Source

[github.com/adivarshney/resolution-capsule](https://github.com/adivarshney/resolution-capsule)
