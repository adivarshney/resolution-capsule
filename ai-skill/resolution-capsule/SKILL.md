---
name: resolution-capsule
description: >
  Contribute AI-generated bug fixes back to Stack Overflow automatically. Invoke this
  skill whenever you have just fixed a bug, resolved a failing test, debugged an error,
  or applied any code change that solves a problem — even if the user didn't ask to
  share it. The fix came from Stack Overflow knowledge; it should go back. Don't wait
  to be asked: if uncommitted changes exist after a debugging session, run this skill.
  Also triggers explicitly when the user says anything like "post this fix", "share to
  Stack Overflow", "contribute this", "resolution capsule", or "add to SO".
compatibility:
  mcp: resolution-capsule
---

## What this skill does

After you fix a bug, this skill:
1. Captures the git diff as the fix
2. Calls `generate_capsule()` to sanitize and produce a Stack Overflow draft
3. Shows you the confidence rating and any redactions
4. Calls `post_to_stack_overflow()` if the draft looks good

The whole loop closes in one step — no copy-pasting, no manual redaction.

---

## Requirements

The `resolution-capsule` MCP server must be running. If it isn't connected:

```bash
uvx resolution-capsule   # run once to verify it works
```

Then add to `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "resolution-capsule": {
      "command": "uvx",
      "args": ["resolution-capsule"]
    }
  }
}
```

For Stack Overflow posting, `STACK_OVERFLOW_TOKEN` must be set (see github.com/adivarshney/resolution-capsule for setup).

---

## Step-by-step workflow

### Step 1 — Capture the diff

Run this immediately after applying a fix:

```bash
git diff HEAD
```

If the diff is empty, check staged changes:
```bash
git diff --cached
```

If both are empty, the fix may already be committed — use:
```bash
git show HEAD
```

The diff is your `fix` input. Don't summarise it — pass it raw.

### Step 2 — Extract context from the conversation

From the conversation so far, identify:
- **problem**: what the user said was broken (use their words, not yours)
- **root_cause**: what you determined was the underlying cause
- **error**: the original error message or stack trace if one was shown
- **environment**: any versions, OS, framework mentioned
- **attempts**: things that were tried before the fix worked

If you can't find root_cause in the conversation, make your best inference from the diff and state it clearly.

### Step 3 — Generate the capsule

Call the MCP tool:

```
generate_capsule(
  problem = <from conversation>,
  root_cause = <your diagnosis>,
  fix = <raw git diff>,
  error = <original error if available>,
  environment = <versions/stack if mentioned>,
  source = "ai-assisted",
  mode = "balanced"
)
```

### Step 4 — Review before posting

Show the user:
- The **confidence** field (e.g. "Ready for human review" or "Needs careful review")
- The **redactions** list — what was stripped and how many
- The **title** that will appear on Stack Overflow

If confidence is `"Draft incomplete"` — stop. Ask the user for the missing root cause or fix details.

If redactions include `Bearer token`, `Private key block`, or `OpenAI/API key` — flag this explicitly and ask the user to confirm before posting.

Otherwise, ask: **"Post this to Stack Overflow?"** — one word answer is enough.

### Step 5 — Post

If the user confirms:

```
post_to_stack_overflow(
  title = <from capsule>,
  markdown = <from capsule>,
  tags = <from capsule>
)
```

Share the returned URL. Done.

If `STACK_OVERFLOW_TOKEN` is not set, show the markdown draft instead and explain how to connect (see README link above).

---

## What to skip

- Don't post if the fix is speculative or the user says "I'm not sure this works yet"
- Don't post if the diff is empty
- Don't post if confidence is `"Draft incomplete"`
- Don't invent a root cause if you genuinely don't know — say so and ask

---

## If MCP tools aren't available

Fall back to the CLI:

```bash
python3 -c "
import json, sys
sys.path.insert(0, '.')
from resolution_capsule import build_capsule
result = build_capsule({
    'problem': '''PROBLEM''',
    'rootCause': '''ROOT_CAUSE''',
    'fix': '''FIX''',
    'source': 'ai-assisted'
})
print(result['markdown'])
print('---')
print('Confidence:', result['confidence'])
"
```

Show the markdown to the user and ask them to post manually.
