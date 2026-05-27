import unittest

from resolution_capsule import build_capsule


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

    def test_title_avoids_fully_redacted_error(self):
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


if __name__ == "__main__":
    unittest.main()
