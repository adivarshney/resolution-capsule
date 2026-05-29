import gzip
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .engine import build_capsule

mcp = FastMCP("resolution-capsule")

# Credentials are stored once in ~/.config/resolution-capsule/credentials.json
_CREDS_PATH = Path.home() / ".config" / "resolution-capsule" / "credentials.json"


def _load_creds() -> dict:
    try:
        return json.loads(_CREDS_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_creds(data: dict):
    _CREDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CREDS_PATH.write_text(json.dumps(data, indent=2))


# ── Tools ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def setup_credentials(access_token: str, api_key: str = "") -> dict:
    """
    Save Stack Overflow credentials once. After this, post_to_stack_overflow
    works without any extra arguments — credentials are loaded automatically.

    Get your access_token and api_key by registering a free app at:
    https://stackapps.com/apps/oauth/register
    (OAuth domain: localhost, then run: Resolution Capsule: Connect Stack Overflow in VS Code)
    """
    _save_creds({"access_token": access_token, "api_key": api_key})
    return {"status": "ok", "message": "Credentials saved. You won't need to enter them again."}


@mcp.tool()
def credentials_status() -> dict:
    """Check whether Stack Overflow credentials are saved."""
    creds = _load_creds()
    if creds.get("access_token"):
        return {"configured": True, "has_api_key": bool(creds.get("api_key"))}
    return {"configured": False, "message": "Run setup_credentials() to connect Stack Overflow."}


@mcp.tool()
def generate_capsule(
    problem: str,
    root_cause: str,
    fix: str,
    environment: str = "",
    error: str = "",
    attempts: str = "",
    source: str = "ai-assisted",
    mode: str = "balanced",
) -> dict:
    """
    Sanitize a resolved bug and produce a Stack Overflow-ready draft.

    Returns title, tags, confidence, redaction_count, markdown, and source.
    Call this first, then post_to_stack_overflow if the user confirms.
    """
    result = build_capsule({
        "problem": problem,
        "rootCause": root_cause,
        "fix": fix,
        "environment": environment,
        "error": error,
        "attempts": attempts,
        "source": source,
        "mode": mode,
    })
    # Add a flat redaction_count for easy display
    result["redaction_count"] = sum(r["count"] for r in result.get("redactions", []))
    return result


@mcp.tool()
def post_to_stack_overflow(
    title: str,
    markdown: str,
    tags: list[str],
) -> dict:
    """
    Post a capsule to Stack Overflow. Credentials are loaded automatically
    from ~/.config/resolution-capsule/credentials.json — no token needed here.

    If credentials aren't saved yet, call setup_credentials() first.
    """
    creds = _load_creds()

    # Fall back to env vars for CI/scripting use cases
    token = creds.get("access_token") or os.environ.get("STACK_OVERFLOW_TOKEN", "")
    key = creds.get("api_key") or os.environ.get("STACK_EXCHANGE_API_KEY", "")

    if not token:
        return {
            "error": "No credentials found. Call setup_credentials(access_token=...) once to connect.",
            "setup_url": "https://stackapps.com/apps/oauth/register"
        }

    params: dict = {
        "site": "stackoverflow",
        "access_token": token,
        "title": title[:150],
        "body": markdown,
        "tags": ";".join(t[:25] for t in tags[:5]),
    }
    if key:
        params["key"] = key

    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        "https://api.stackexchange.com/2.3/questions/add",
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip",
        },
    )

    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        result = json.loads(raw)

    if result.get("error_id"):
        return {
            "error": f"Stack Exchange error {result['error_id']}: {result.get('error_message')}"
        }

    question = result.get("items", [{}])[0]
    return {
        "url": question.get("link", ""),
        "question_id": question.get("question_id"),
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
