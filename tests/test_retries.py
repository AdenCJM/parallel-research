from __future__ import annotations

import unittest
from unittest.mock import patch

from parallel_research.providers.base import with_retries


class RetryableError(Exception):
    status_code = 503


class RetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_transient_failure_is_retried(self) -> None:
        attempts = 0

        async def operation() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise RetryableError("temporary")
            return "ok"

        with patch("parallel_research.providers.base.asyncio.sleep", return_value=None):
            self.assertEqual(await with_retries(operation), "ok")
        self.assertEqual(attempts, 3)

    async def test_non_retryable_failure_is_immediate(self) -> None:
        attempts = 0

        async def operation() -> str:
            nonlocal attempts
            attempts += 1
            raise ValueError("bad input")

        with self.assertRaises(ValueError):
            await with_retries(operation)
        self.assertEqual(attempts, 1)


if __name__ == "__main__":
    unittest.main()
