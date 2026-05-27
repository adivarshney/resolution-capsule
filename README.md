# Resolution Capsule

AI coding assistants are trained on Stack Overflow. When they fix your bug, that fix should go back to Stack Overflow.

Resolution Capsule closes the loop: it captures an AI-generated fix, strips everything private (tokens, emails, internal paths, IPs, ticket IDs), and posts a clean, reviewable draft directly to Stack Overflow.

---

## The Problem

Every day, AI assistants help developers fix bugs using knowledge that was scraped from public forums. Those fixes stay in a chat window and never benefit the next person who hits the same error. The knowledge loop is broken.

## What It Does

1. You fix a bug — with an AI assistant or manually
2. Resolution Capsule captures the fix and its context
3. It redacts secrets, identity markers, and internal details automatically
4. It produces a Stack Overflow-ready draft and posts it via the API

The goal is zero friction between "fix applied" and "community helped."

---

## Surfaces

| Surface | Best for |
|---|---|
| **VS Code extension** | Capturing AI-generated fixes directly from your editor (git diff → post) |
| **CLI** | CI pipelines, scripts, batch processing of resolved incidents |
| **Web UI** | Quick one-off drafts and testing the sanitizer |
| **AI skill** | Embedding the workflow inside Cursor, Copilot, Claude Code, or any agent |

---

## VS Code Extension

Install from the [marketplace](https://marketplace.visualstudio.com/items?itemName=adivarshney.resolution-capsule) or from the `.vsix` in `vscode-extension/`.

**Key command — Create from AI Fix:**

1. Use your AI assistant to apply a fix
2. `Cmd+Shift+P` → **Resolution Capsule: Create from AI Fix**
3. Describe the problem and root cause
4. A sanitized draft opens — one click posts it to Stack Overflow

The command captures your current git diff as the fix automatically. No copy-pasting.

Other commands: `Create From Selection`, `Create From Prompts`, `Connect Stack Overflow`, `Disconnect Stack Overflow`.

---

## CLI

```bash
python3 capsule_cli.py \
  --problem "Build fails after dependency upgrade" \
  --rootCause "Lockfile drift" \
  --fix "Regenerated package-lock.json" \
  --source "ai-assisted"
```

JSON input:

```bash
python3 capsule_cli.py --format json --json '{"problem":"...","rootCause":"...","fix":"...","source":"ai-assisted","mode":"balanced"}'
```

Write to file:

```bash
python3 capsule_cli.py --output capsule.md --problem "..." --rootCause "..." --fix "..."
```

---

## Web UI

```bash
python3 app.py
```

Open `http://127.0.0.1:8000`.

---

## Sanitization

**Balanced mode** (default): API keys, bearer tokens, JWTs, GitHub tokens, Slack tokens, AWS keys, emails, IPs, internal URLs, filesystem user paths, private key blocks.

**Strict mode**: everything above plus ticket IDs and long numeric identifiers.

---

## What's Missing (and Where to Help)

This is a work in progress. The pieces that matter most and aren't built yet:

- **Cursor / Copilot / Claude Code hooks** — trigger a capsule automatically when an AI fix is accepted, without the developer doing anything manually
- **Entropy-based secret detection** — catch high-entropy strings that don't match known patterns
- **Duplicate detection** — check if the question already exists on Stack Overflow before posting
- **Team policy packs** — org-level redaction rules layered on top of the defaults
- **JetBrains plugin** — same workflow as the VS Code extension

If any of these interest you, the codebase is small and the engine is pure Python with no dependencies.

---

## Stack Overflow Setup

To enable auto-posting, register a free app at [stackapps.com/apps/oauth/register](https://stackapps.com/apps/oauth/register) with OAuth domain `localhost`, then add your credentials to VS Code settings:

```
resolutionCapsule.stackOverflow.clientId
resolutionCapsule.stackOverflow.clientSecret
resolutionCapsule.stackOverflow.apiKey
```

Run **Resolution Capsule: Connect Stack Overflow** once to authorise.

---

## Contributing

The repo is at [github.com/adivarshney/resolution-capsule](https://github.com/adivarshney/resolution-capsule). Issues, PRs, and ideas are all welcome. If you're unsure where to start, the AI tool integrations section above is the frontier.

---

## Run the Tests

```bash
python3 -m unittest test_app -v
```
