import re


SECRET_PATTERNS = [
    ("OpenAI/API key", re.compile(r"\b(sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9_]*api[_-]?key[A-Za-z0-9_]*\s*[:=]\s*['\"]?[^'\"\s]+)", re.I)),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.I)),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")),
    ("Password assignment", re.compile(r"\b(password|passwd|pwd)\s*[:=]\s*['\"]?[^'\"\s]+", re.I)),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")),
]

IDENTITY_PATTERNS = [
    ("Email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("IPv4 address", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("Internal URL", re.compile(r"\bhttps?://(?:localhost|127\.0\.0\.1|[\w.-]*\.(?:local|internal|corp|lan|intra))(?::\d+)?[^\s]*", re.I)),
    ("Filesystem user path", re.compile(r"(/Users/|/home/)[^/\s]+")),
]

BUSINESS_PATTERNS = [
    ("Likely ticket ID", re.compile(r"\b[A-Z]{2,10}-\d{2,8}\b")),
    ("Long numeric identifier", re.compile(r"\b\d{12,}\b")),
]


def redact(text, mode):
    redactions = []
    sanitized = text or ""
    pattern_sets = [SECRET_PATTERNS, IDENTITY_PATTERNS]
    if mode == "strict":
        pattern_sets.append(BUSINESS_PATTERNS)

    for patterns in pattern_sets:
        for label, pattern in patterns:
            count = 0

            def replace(match):
                nonlocal count
                count += 1
                return f"[REDACTED: {label}]"

            sanitized = pattern.sub(replace, sanitized)
            if count:
                redactions.append({"type": label, "count": count})

    return sanitized.strip(), redactions


def public_title_seed(*blocks):
    for block in blocks:
        for line in (block or "").splitlines():
            clean = line.strip()
            if clean and "[REDACTED:" not in clean:
                return clean[:140]
    return "Resolved development issue"


def infer_tags(environment, raw):
    source = f"{environment}\n{raw}".lower()
    known = [
        "python",
        "node",
        "typescript",
        "react",
        "next.js",
        "vite",
        "docker",
        "kubernetes",
        "postgres",
        "mysql",
        "redis",
        "aws",
        "gcp",
        "azure",
        "github-actions",
        "java",
        "spring",
        "go",
        "rust",
    ]
    tags = [tag for tag in known if tag in source]
    return tags[:5] or ["debugging", "rca"]


def build_capsule(payload):
    mode = payload.get("mode", "balanced")
    problem, problem_redactions = redact(payload.get("problem", ""), mode)
    environment, environment_redactions = redact(payload.get("environment", ""), mode)
    error, error_redactions = redact(payload.get("error", ""), mode)
    attempts, attempts_redactions = redact(payload.get("attempts", ""), mode)
    root_cause, root_cause_redactions = redact(payload.get("rootCause", ""), mode)
    fix, fix_redactions = redact(payload.get("fix", ""), mode)

    title_seed = public_title_seed(error, problem, root_cause, fix)
    title = f"How to fix: {title_seed}"
    tags = infer_tags(environment, "\n".join([problem, error, fix]))
    all_redactions = (
        problem_redactions
        + environment_redactions
        + error_redactions
        + attempts_redactions
        + root_cause_redactions
        + fix_redactions
    )

    confidence = "Ready for human review"
    if any(item["type"] in {"OpenAI/API key", "AWS access key", "Bearer token", "JWT", "Private key block"} for item in all_redactions):
        confidence = "Needs careful review before publishing"
    if not fix or not root_cause:
        confidence = "Draft incomplete: add root cause and fix"

    markdown = f"""# {title}

## Problem
{problem or "_Add the observed problem._"}

## Environment
{environment or "_Add versions, OS, framework, runtime, and deployment context._"}

## Error or Symptom
```text
{error or "Add the sanitized error, stack trace, or failing command output."}
```

## What I Tried
{attempts or "_Add failed approaches and why they did not work._"}

## Root Cause
{root_cause or "_Add the underlying cause._"}

## Resolution
{fix or "_Add the final fix with enough detail to reproduce safely._"}

## Suggested Tags
{", ".join(tags)}

## Compliance Review Notes
- Sanitization mode: {mode}
- Redactions applied: {sum(item["count"] for item in all_redactions)}
- Review status: {confidence}
"""

    return {
        "title": title,
        "tags": tags,
        "confidence": confidence,
        "redactions": summarize_redactions(all_redactions),
        "markdown": markdown,
    }


def summarize_redactions(redactions):
    summary = {}
    for item in redactions:
        summary[item["type"]] = summary.get(item["type"], 0) + item["count"]
    return [{"type": key, "count": value} for key, value in sorted(summary.items())]
