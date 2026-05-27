import gzip
import json
import os
import urllib.parse
import urllib.request

from mcp.server.fastmcp import FastMCP

from .engine import build_capsule

mcp = FastMCP("resolution-capsule")


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

    Returns title, tags, confidence, redactions, markdown, and source.
    Always call this before post_to_stack_overflow.
    """
    return build_capsule({
        "problem": problem,
        "rootCause": root_cause,
        "fix": fix,
        "environment": environment,
        "error": error,
        "attempts": attempts,
        "source": source,
        "mode": mode,
    })


@mcp.tool()
def post_to_stack_overflow(
    title: str,
    markdown: str,
    tags: list[str],
    access_token: str = "",
    api_key: str = "",
) -> dict:
    """
    Post a generated capsule to Stack Overflow as a new question.

    Requires a Stack Exchange access token — pass it directly or set the
    STACK_OVERFLOW_TOKEN environment variable. Get a token by registering
    a free app at stackapps.com/apps/oauth/register.
    """
    token = access_token or os.environ.get("STACK_OVERFLOW_TOKEN", "")
    key = api_key or os.environ.get("STACK_EXCHANGE_API_KEY", "")

    if not token:
        return {
            "error": (
                "No access token. Pass access_token or set the "
                "STACK_OVERFLOW_TOKEN environment variable."
            )
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
