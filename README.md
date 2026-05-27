# Resolution Capsule

Resolution Capsule is a privacy-first prototype for turning solved engineering issues into sanitized, reviewable public knowledge artifacts.

It now has four surfaces over the same local engine:

- Web MVP for a fast browser demo.
- CLI for scripts, CI, and automation.
- VS Code extension scaffold for in-editor capture.
- AI skill workflow for Codex/Cursor/agent-style tools.

## Run The Web App

```bash
python3 app.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Use The CLI

```bash
python3 capsule_cli.py --problem "Build fails after dependency upgrade" --rootCause "Lockfile drift" --fix "Regenerated package-lock.json"
```

Or pass JSON:

```bash
python3 capsule_cli.py --format json --json '{"problem":"Build failed for alex@example.com","error":"Bearer abcdefghijklmnopqrstuvwxyz","rootCause":"Token leaked","fix":"Rotated token","mode":"balanced"}'
```

## Try The VS Code Extension

This repo includes a scaffold in `vscode-extension/`.

1. Open the repository in VS Code.
2. Open `vscode-extension/extension.js`.
3. Press `F5` to launch the extension development host.
4. Run `Resolution Capsule: Create From Selection` or `Resolution Capsule: Create From Prompts`.

The extension calls the local `capsule_cli.py` engine and opens a Markdown draft.

## AI Skill

The reusable AI workflow lives in `ai-skill/SKILL.md`. It describes how an AI coding assistant should capture, sanitize, transform, and review a resolved issue before publishing.

## What It Does

- Captures problem, environment, error logs, attempts, root cause, and fix.
- Redacts common secrets, tokens, emails, internal URLs, IP addresses, user paths, ticket IDs, and long identifiers.
- Produces a reusable "Resolution Capsule" draft.
- Shows a redaction report and review confidence.
- Keeps everything local.

## Suggested Next Steps

- Add IDE integrations for VS Code and JetBrains.
- Add deterministic secret scanning with entropy checks.
- Add organization policy packs and approval workflows.
- Add duplicate detection against public Q&A portals.
- Add export targets for Stack Overflow drafts, GitHub Discussions, and vendor forums.
