from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from parallel_research.models import Depth, RunStatus
from parallel_research.providers.claude import ClaudeProvider
from parallel_research.providers.gemini import GeminiProvider
from parallel_research.providers.openai_provider import OpenAIProvider
from parallel_research.providers.perplexity import PerplexityProvider


class ProviderContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_openai_general_request_uses_responses_web_search(self) -> None:
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test"}, clear=False):
            provider = OpenAIProvider()
        response = SimpleNamespace(id="response-1")
        create = AsyncMock(return_value=response)
        client = SimpleNamespace(responses=SimpleNamespace(create=create))
        returned = await provider._grounded_call(client, "topic", 4096)
        self.assertIs(returned, response)
        call = create.await_args
        self.assertIsNotNone(call)
        assert call is not None
        kwargs = call.kwargs
        self.assertEqual(kwargs["tools"], [{"type": "web_search"}])
        self.assertEqual(kwargs["max_output_tokens"], 4096)

    async def test_openai_deep_persists_request_id_before_polling(self) -> None:
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test"}, clear=False):
            provider = OpenAIProvider()
        queued = SimpleNamespace(id="deep-1", status="queued")
        completed = SimpleNamespace(
            id="deep-1",
            status="completed",
            output_text="Grounded report",
            output=[],
            usage=None,
        )
        fake_client = SimpleNamespace(
            responses=SimpleNamespace(
                create=AsyncMock(return_value=queued),
                retrieve=AsyncMock(return_value=completed),
            )
        )
        updates: list[dict[str, object]] = []

        async def progress(update: dict[str, object]) -> None:
            updates.append(update)

        with (
            patch("openai.AsyncOpenAI", return_value=fake_client),
            patch("parallel_research.providers.openai_provider.asyncio.sleep", AsyncMock()),
        ):
            result = await provider.research("topic", Depth.DEEP, progress)
        self.assertEqual(result.status, RunStatus.SUCCEEDED)
        self.assertEqual(updates[0]["request_id"], "deep-1")
        call = fake_client.responses.create.await_args
        self.assertIsNotNone(call)
        assert call is not None
        self.assertEqual(call.kwargs["max_tool_calls"], 30)

    async def test_claude_request_enables_direct_grounded_search(self) -> None:
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}, clear=False):
            provider = ClaudeProvider()
        create = AsyncMock(return_value=SimpleNamespace())
        client = SimpleNamespace(messages=SimpleNamespace(create=create))
        await provider._call(client, [{"role": "user", "content": "topic"}], 4096)
        call = create.await_args
        self.assertIsNotNone(call)
        assert call is not None
        tool = call.kwargs["tools"][0]
        self.assertEqual(tool["type"], "web_search_20260318")
        self.assertEqual(tool["allowed_callers"], ["direct"])

    async def test_gemini_request_enables_grounding_and_output_limit(self) -> None:
        with patch.dict("os.environ", {"GOOGLE_AI_API_KEY": "test"}, clear=False):
            provider = GeminiProvider()
        generate = AsyncMock(return_value=SimpleNamespace())
        client = SimpleNamespace(
            aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate))
        )
        await provider._call(client, "topic", 4096)
        call = generate.await_args
        self.assertIsNotNone(call)
        assert call is not None
        config = call.kwargs["config"]
        self.assertEqual(config.max_output_tokens, 4096)
        self.assertIsNotNone(config.tools[0].google_search)

    async def test_perplexity_deep_persists_resumable_request_id(self) -> None:
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test"}, clear=False):
            provider = PerplexityProvider()
        content = SimpleNamespace(
            id="result-1",
            choices=[SimpleNamespace(message=SimpleNamespace(content="Deep report"))],
            citations=["https://example.com/deep"],
            search_results=[],
            usage=None,
        )
        completed = SimpleNamespace(
            id="pplx-deep-1",
            status="COMPLETED",
            response=content,
            error_message=None,
        )
        create = AsyncMock(return_value=completed)
        fake_client = SimpleNamespace(
            async_=SimpleNamespace(
                chat=SimpleNamespace(completions=SimpleNamespace(create=create, get=AsyncMock()))
            )
        )
        updates: list[dict[str, object]] = []

        async def progress(update: dict[str, object]) -> None:
            updates.append(update)

        with patch("perplexity.AsyncPerplexity", return_value=fake_client):
            result = await provider.research("topic", Depth.DEEP, progress)
        self.assertEqual(result.status, RunStatus.SUCCEEDED)
        self.assertEqual(result.request_id, "pplx-deep-1")
        self.assertEqual(updates[0]["request_id"], "pplx-deep-1")
        call = create.await_args
        self.assertIsNotNone(call)
        assert call is not None
        request = call.kwargs["request"]
        self.assertEqual(request["reasoning_effort"], "medium")


if __name__ == "__main__":
    unittest.main()
