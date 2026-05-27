import argparse
import json
import sys

from resolution_capsule import build_capsule


FIELDS = ["problem", "environment", "error", "attempts", "rootCause", "fix"]


def read_payload(args):
    if args.json:
        return json.loads(args.json)
    if args.file:
        with open(args.file, "r", encoding="utf-8") as handle:
            return json.load(handle)
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            return json.loads(raw)
    return {field: getattr(args, field) for field in FIELDS}


def main():
    parser = argparse.ArgumentParser(description="Generate a sanitized Resolution Capsule draft.")
    parser.add_argument("--json", help="Inline JSON payload.")
    parser.add_argument("--file", help="Path to a JSON payload.")
    parser.add_argument("--mode", choices=["balanced", "strict"], default="balanced")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    for field in FIELDS:
        parser.add_argument(f"--{field}", default="")

    args = parser.parse_args()
    payload = read_payload(args)
    payload["mode"] = payload.get("mode") or args.mode
    result = build_capsule(payload)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(result["markdown"])


if __name__ == "__main__":
    main()
