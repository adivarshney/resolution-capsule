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

## The flow (keep it to one prompt)

After fixing a bug, do this in one shot:

1. Capture the diff
2. Generate the capsule silently
3. Show a **single line** to the user and wait for yes/no
4. Post if yes, show draft if no

The user should never see intermediate steps, tool calls, or redaction details unless they ask.

---

## Step 1 — Get the diff

```bash
git diff HEAD
```

If empty, try staged:
```bash
git diff --cached
```

If both empty, the fix may be committed already:
```bash
git show HEAD
```

Pass the raw diff as `fix`. Do not summarise it.

---

## Step 2 — Generate silently

Call `generate_capsule()` without narrating what you're doing:

```
generate_capsule(
  problem    = <what the user said was broken, in their words>,
  root_cause = <your diagnosis from the fix>,
  fix        = <raw git diff>,
  error      = <original error message if one was shown>,
  environment = <versions/framework if mentioned>,
  source     = "ai-assisted"
)
```

---

## Step 3 — One prompt

Once you have the result, show **exactly this** (one line, fill in the blanks):

```
"[title]" — [N] things redacted. Post to Stack Overflow? yes/no
```

Example:
```
"How to fix: Cannot find module '@vitejs/plugin-react'" — 3 things redacted. Post to Stack Overflow? yes/no
```

Nothing else. No markdown, no redaction breakdown, no explanation. Just that line.

---

## Step 4 — Act on the answer

**If yes:**
Call `post_to_stack_overflow(title=..., markdown=..., tags=...)` and reply with just the URL:

```
Posted: https://stackoverflow.com/questions/...
```

**If no:**
Show the full markdown draft so the user can copy it manually. One sentence: "Here's the draft if you want to post it yourself."

**If credentials aren't set up yet** (post returns an error about missing credentials):
Say: "You need to connect Stack Overflow once. Run `setup_credentials(access_token='...')` — get your token at stackapps.com/apps/oauth/register"
Then stop. Don't retry posting.

---

## First-time setup (only needed once)

If `credentials_status()` returns `configured: false`, pause before generating the capsule and say:

```
"To post to Stack Overflow automatically, run setup_credentials(access_token='YOUR_TOKEN') once.
Get a free token at: stackapps.com/apps/oauth/register"
```

After setup, continue with the normal flow. This only happens once — credentials are saved permanently.

---

## What not to do

- Don't narrate each tool call ("Now I'll call generate_capsule...")
- Don't show the redaction list unless asked
- Don't post if the diff is empty
- Don't post if confidence is "Draft incomplete"
- Don't ask more than one question
