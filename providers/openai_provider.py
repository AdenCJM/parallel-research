from __future__ import annotations

import asyncio
import os
import time

from .base import (
    BaseProvider,
    Depth,
    ResearchResult,
    RESEARCH_SYSTEM_PROMPT,
    REFINEMENT_PROMPT,
    SYNTHESIS_PROMPT,
    with_retries,
)


class OpenAIProvider(BaseProvider):
    """OpenAI API provider. Native deep research via o3-deep-research."""

    name = "openai"

    def __init__(self) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY", "")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def research(self, topic: str, depth: Depth) -> ResearchResult:
        from openai import AsyncOpenAI

        start = time.monotonic()
        client = AsyncOpenAI(api_key=self.api_key)

        try:
            if depth == Depth.DEEP:
                return await self._deep_research(client, topic, start)
            elif depth == Depth.QUICK:
                return await self._quick_research(client, topic, start)
            else:
                return await self._standard_research(client, topic, start)
        except Exception as exc:
            return ResearchResult(
                provider=self.name,
                model="unknown",
                content="",
                duration_seconds=time.monotonic() - start,
                error=f"{type(exc).__name__}: {exc}",
            )

    async def _quick_research(
        self, client, topic: str, start: float
    ) -> ResearchResult:
        model = "gpt-4o"
        response = await with_retries(
            client.chat.completions.create,
            model=model,
            messages=[
                {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": f"Research the following topic comprehensively:\n\n{topic}"},
            ],
            max_tokens=4096,
        )
        return ResearchResult(
            provider=self.name,
            model=model,
            content=response.choices[0].message.content,
            duration_seconds=time.monotonic() - start,
        )

    async def _standard_research(
        self, client, topic: str, start: float
    ) -> ResearchResult:
        model = "gpt-4o"
        messages = [
            {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
            {"role": "user", "content": f"Research the following topic comprehensively:\n\n{topic}"},
        ]

        # Call 1: Initial research
        r1 = await with_retries(
            client.chat.completions.create,
            model=model,
            messages=messages,
            max_tokens=4096,
        )
        messages.append({"role": "assistant", "content": r1.choices[0].message.content})

        # Call 2: Identify gaps
        messages.append({"role": "user", "content": REFINEMENT_PROMPT})
        r2 = await with_retries(
            client.chat.completions.create,
            model=model,
            messages=messages,
            max_tokens=4096,
        )
        messages.append({"role": "assistant", "content": r2.choices[0].message.content})

        # Call 3: Synthesise
        messages.append({"role": "user", "content": SYNTHESIS_PROMPT})
        r3 = await with_retries(
            client.chat.completions.create,
            model=model,
            messages=messages,
            max_tokens=8192,
        )
        return ResearchResult(
            provider=self.name,
            model=model,
            content=r3.choices[0].message.content,
            duration_seconds=time.monotonic() - start,
        )

    async def _deep_research(
        self, client, topic: str, start: float
    ) -> ResearchResult:
        """Use o3-deep-research via the Responses API with background polling."""
        model = "o3-deep-research"

        # Create background deep research task
        response = await with_retries(
            client.responses.create,
            model=model,
            input=[
                {"role": "user", "content": f"Research the following topic comprehensively:\n\n{topic}"},
            ],
            tools=[{"type": "web_search_preview"}],
            background=True,
        )

        # Poll until complete
        while response.status in ("queued", "in_progress"):
            await asyncio.sleep(5)
            response = await client.responses.retrieve(response.id)

        if response.status != "completed":
            return ResearchResult(
                provider=self.name,
                model=model,
                content="",
                duration_seconds=time.monotonic() - start,
                error=f"Deep research ended with status: {response.status}",
            )

        # Extract text from response output
        content_parts = []
        for item in response.output:
            if hasattr(item, "text"):
                content_parts.append(item.text)
            elif hasattr(item, "content"):
                for block in item.content:
                    if hasattr(block, "text"):
                        content_parts.append(block.text)

        return ResearchResult(
            provider=self.name,
            model=model,
            content="\n\n".join(content_parts),
            duration_seconds=time.monotonic() - start,
        )
