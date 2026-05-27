import re


SECRET_PATTERNS = [
    ("OpenAI/API key", re.compile(r"\b(sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9_]*api[_-]?key[A-Za-z0-9_]*\s*[:=]\s*['\"]?[^'\"\s]+)", re.I)),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("AWS secret key", re.compile(r"(?i)aws[_\-\s]?secret[_\-\s]?(?:access[_\-\s]?)?key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}\b")),
    ("GitHub token", re.compile(r"\b(ghp_|gho_|ghs_|ghr_|github_pat_)[A-Za-z0-9_]{16,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z\-]{10,}\b")),
    ("Bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.I)),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")),
    ("Password assignment", re.compile(r"\b(password|passwd|pwd)\s*[:=]\s*['\"]?[^'\"\s]+", re.I)),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")),
    ("Generic secret assignment", re.compile(r"\b(secret|token|auth|credential)[_A-Za-z0-9]*\s*[:=]\s*['\"]?[A-Za-z0-9+/=_\-]{16,}", re.I)),
]

IDENTITY_PATTERNS = [
    ("Email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("IPv4 address", re.compile(r"\b(?:(?:10|172|192)\.(?:\d{1,3}\.){2}\d{1,3}|127\.0\.0\.\d{1,3})\b")),
    ("Public IP address", re.compile(r"\b(?!10\.|172\.|192\.|127\.)(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("Internal URL", re.compile(r"\bhttps?://(?:localhost|127\.0\.0\.1|[\w.-]*\.(?:local|internal|corp|lan|intra))(?::\d+)?[^\s]*", re.I)),
    ("Filesystem user path", re.compile(r"(/Users/|/home/|C:\\Users\\)[^/\\\s]+")),
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

            def replace(match, _l=label):
                nonlocal count
                count += 1
                return f"[REDACTED: {_l}]"

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


_TAG_PATTERNS = [
    ("python", re.compile(r"\bpython\b", re.I)),
    ("node", re.compile(r"\bnode(?:\.js)?\b", re.I)),
    ("typescript", re.compile(r"\btypescript\b|\b\.tsx?\b", re.I)),
    ("react", re.compile(r"\breact\b", re.I)),
    ("next.js", re.compile(r"\bnext(?:\.js)?\b", re.I)),
    ("vite", re.compile(r"\bvite\b", re.I)),
    ("docker", re.compile(r"\bdocker\b", re.I)),
    ("kubernetes", re.compile(r"\bkubernetes\b|\bk8s\b", re.I)),
    ("postgres", re.compile(r"\bpostgres(?:ql)?\b", re.I)),
    ("mysql", re.compile(r"\bmysql\b", re.I)),
    ("redis", re.compile(r"\bredis\b", re.I)),
    ("aws", re.compile(r"\baws\b|\bamazon web services\b", re.I)),
    ("gcp", re.compile(r"\bgcp\b|\bgoogle cloud\b", re.I)),
    ("azure", re.compile(r"\bazure\b", re.I)),
    ("github-actions", re.compile(r"\bgithub[- ]actions?\b", re.I)),
    ("java", re.compile(r"\bjava\b", re.I)),
    ("spring", re.compile(r"\bspring\b", re.I)),
    ("go", re.compile(r"\bgolang\b|\bgo\s+\d+\.\d+\b", re.I)),
    ("rust", re.compile(r"\brust\b|\bcargo\b", re.I)),
    ("django", re.compile(r"\bdjango\b", re.I)),
    ("fastapi", re.compile(r"\bfastapi\b", re.I)),
    ("flask", re.compile(r"\bflask\b", re.I)),
    ("terraform", re.compile(r"\bterraform\b", re.I)),
    ("rails", re.compile(r"\brails\b|\bruby on rails\b", re.I)),
]


def infer_tags(environment, raw):
    source = f"{environment}\n{raw}"
    tags = [tag for tag, pattern in _TAG_PATTERNS if pattern.search(source)]
    return tags[:5] or ["debugging", "rca"]


def build_capsule(payload):
    mode = payload.get("mode", "balanced")
    problem, problem_redactions = redact(payload.get("problem", ""), mode)
    environment, environment_redactions = redact(payload.get("environment", ""), mode)
    error, error_redactions = redact(payload.get("error", ""), mode)
    attempts, attempts_redactions = redact(payload.get("attempts", ""), mode)
    root_cause, root_cause_redactions = redact(payload.get("rootCause", ""), mode)
    fix, fix_redactions = redact(payload.get("fix", ""), mode)

    title_seed = public_title_seed(problem, fix, root_cause, error)
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
    if any(item["type"] in {"OpenAI/API key", "AWS access key", "AWS secret key", "GitHub token", "Slack token", "Bearer token", "JWT", "Private key block"} for item in all_redactions):
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
