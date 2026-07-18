from __future__ import annotations

import unittest

from parallel_research.safety import redact_secrets


class SafetyTests(unittest.TestCase):
    def test_redacts_common_credentials(self) -> None:
        source = "Authorization: Bearer token-123 API_KEY=secret-456 sk-ant-abcdefghijklmnop"
        redacted = redact_secrets(source)
        self.assertNotIn("token-123", redacted)
        self.assertNotIn("secret-456", redacted)
        self.assertNotIn("sk-ant-abcdefghijklmnop", redacted)
        self.assertIn("[REDACTED]", redacted)


if __name__ == "__main__":
    unittest.main()
