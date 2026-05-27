import io
import json
import sys
import unittest
from unittest.mock import patch

from resolution_capsule import build_capsule, redact


class RedactTests(unittest.TestCase):
    def test_email_redacted(self):
        out, items = redact("Contact alex@example.com for help.", "balanced")
        self.assertIn("[REDACTED: Email]", out)
        self.assertEqual(items[0]["count"], 1)

    def test_bearer_token_redacted(self):
        out, items = redact("Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456", "balanced")
        self.assertIn("[REDACTED: Bearer token]", out)

    def test_github_token_redacted(self):
        out, items = redact("token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij", "balanced")
        self.assertIn("[REDACTED: GitHub token]", out)

    def test_slack_token_redacted(self):
        token = "xoxb-" + "123456789012-abcdefghijklmnopqrst"
        out, items = redact(f"SLACK_TOKEN={token}", "balanced")
        self.assertIn("[REDACTED: Slack token]", out)

    def test_jwt_redacted(self):
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        out, items = redact(jwt, "balanced")
        self.assertIn("[REDACTED: JWT]", out)

    def test_private_key_redacted(self):
        key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA\n-----END RSA PRIVATE KEY-----"
        out, items = redact(key, "balanced")
        self.assertIn("[REDACTED: Private key block]", out)

    def test_ipv4_redacted(self):
        out, items = redact("Connected to 192.168.1.100 for DB.", "balanced")
        self.assertIn("[REDACTED: IPv4 address]", out)

    def test_filesystem_path_redacted(self):
        out, items = redact("Error at /Users/alex/work/app.py", "balanced")
        self.assertIn("[REDACTED: Filesystem user path]", out)

    def test_ticket_id_only_in_strict_mode(self):
        text = "See ticket JIRA-1234 for background."
        balanced_out, _ = redact(text, "balanced")
        strict_out, _ = redact(text, "strict")
        self.assertNotIn("[REDACTED:", balanced_out)
        self.assertIn("[REDACTED: Likely ticket ID]", strict_out)

    def test_empty_text_returns_empty(self):
        out, items = redact("", "balanced")
        self.assertEqual(out, "")
        self.assertEqual(items, [])


class CapsuleTests(unittest.TestCase):
    def test_balanced_mode_redacts_secrets_and_identity(self):
        result = build_capsule(
            {
                "problem": "Build failed for alex@example.com",
                "environment": "Node 22 and Vite",
                "error": "Authorization: Bearer abcdefghijklmnopqrstuvwxyz",
                "rootCause": "Lockfile drift",
                "fix": "Regenerated package-lock.json",
                "mode": "balanced",
            }
        )
        self.assertIn("[REDACTED: Email]", result["markdown"])
        self.assertIn("[REDACTED: Bearer token]", result["markdown"])
        self.assertEqual(result["confidence"], "Needs careful review before publishing")

    def test_strict_mode_redacts_ticket_ids(self):
        result = build_capsule(
            {
                "problem": "Tracked as PLATFORM-1234",
                "rootCause": "Missing dependency",
                "fix": "Added dependency",
                "mode": "strict",
            }
        )
        self.assertIn("[REDACTED: Likely ticket ID]", result["markdown"])

    def test_incomplete_draft_requires_more_detail(self):
        result = build_capsule({"problem": "Fails during build", "mode": "balanced"})
        self.assertEqual(result["confidence"], "Draft incomplete: add root cause and fix")

    def test_title_uses_problem_not_redacted_error(self):
        result = build_capsule(
            {
                "problem": "Build fails after dependency upgrade",
                "error": "Bearer abcdefghijklmnopqrstuvwxyz",
                "rootCause": "Lockfile drift",
                "fix": "Regenerated package-lock.json",
                "mode": "balanced",
            }
        )
        self.assertEqual(result["title"], "How to fix: Build fails after dependency upgrade")

    def test_title_falls_back_gracefully(self):
        result = build_capsule({"mode": "balanced"})
        self.assertIn("How to fix:", result["title"])

    def test_tags_inferred_from_environment(self):
        result = build_capsule(
            {
                "problem": "Deploy broke",
                "environment": "Docker on Kubernetes, postgres 15",
                "rootCause": "OOM kill",
                "fix": "Raised memory limit",
                "mode": "balanced",
            }
        )
        self.assertIn("docker", result["tags"])
        self.assertIn("kubernetes", result["tags"])
        self.assertIn("postgres", result["tags"])

    def test_tags_match_github_actions(self):
        result = build_capsule(
            {
                "problem": "CI broke",
                "environment": "GitHub Actions runner",
                "rootCause": "Missing env var",
                "fix": "Added secret",
                "mode": "balanced",
            }
        )
        self.assertIn("github-actions", result["tags"])

    def test_redaction_summary_aggregates_counts(self):
        result = build_capsule(
            {
                "problem": "user1@x.com and user2@x.com both affected",
                "rootCause": "Permission error",
                "fix": "Fixed ACL",
                "mode": "balanced",
            }
        )
        email_entry = next((r for r in result["redactions"] if r["type"] == "Email"), None)
        self.assertIsNotNone(email_entry)
        self.assertEqual(email_entry["count"], 2)

    def test_no_redactions_when_input_is_clean(self):
        result = build_capsule(
            {
                "problem": "TypeError when calling sort on None",
                "environment": "Python 3.12, Ubuntu 22.04",
                "rootCause": "Variable was never initialized",
                "fix": "Added a None check before calling sort",
                "mode": "balanced",
            }
        )
        self.assertEqual(result["redactions"], [])
        self.assertEqual(result["confidence"], "Ready for human review")


class CLITests(unittest.TestCase):
    def _run_cli(self, args):
        from capsule_cli import main
        with patch("sys.argv", ["capsule_cli"] + args):
            captured = io.StringIO()
            with patch("sys.stdout", captured):
                main()
        return captured.getvalue()

    def test_cli_markdown_output(self):
        out = self._run_cli([
            "--problem", "DB connection refused",
            "--rootCause", "Wrong port in config",
            "--fix", "Updated PORT env var",
        ])
        self.assertIn("# How to fix:", out)
        self.assertIn("Resolution", out)

    def test_cli_json_output(self):
        out = self._run_cli([
            "--format", "json",
            "--problem", "DB connection refused",
            "--rootCause", "Wrong port",
            "--fix", "Fixed port",
        ])
        data = json.loads(out)
        self.assertIn("markdown", data)
        self.assertIn("tags", data)

    def test_cli_inline_json_payload(self):
        payload = json.dumps({
            "problem": "Build failed",
            "rootCause": "Missing dep",
            "fix": "Added dep",
            "mode": "balanced",
        })
        out = self._run_cli(["--json", payload])
        self.assertIn("# How to fix:", out)

    def test_cli_output_file(self, tmp_path=None):
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tf:
            path = tf.name
        try:
            from capsule_cli import main
            with patch("sys.argv", [
                "capsule_cli", "--output", path,
                "--problem", "Crash on start",
                "--rootCause", "Null pointer",
                "--fix", "Added nil check",
            ]):
                captured_err = io.StringIO()
                with patch("sys.stderr", captured_err):
                    main()
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            self.assertIn("# How to fix:", content)
            self.assertIn("Capsule written to", captured_err.getvalue())
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
