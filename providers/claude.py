from __future__ import annotations

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


class ClaudeProvider(BaseProvider):
    """Anthropic Claude provider. No native deep research — deep falls back to standard."""

    name = "claude"

    def __init__(self) -> None:
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def research(self, topic: str, depth: Depth) -> ResearchResult:
        from anthropic import AsyncAnthropic

        start = time.monotonic()
        model = "claude-sonnet-4-6"
        client = AsyncAnthropic(api_key=self.api_key)

        # Deep falls back to standard (no native deep research)
        effective_depth = Depth.STANDARD if depth == Depth.DEEP else depth

        try:
            if effective_depth == Depth.QUICK:
                response = await with_retries(
                    client.messages.create,
                    model=model,
                    max_tokens=4096,
                    system=RESEARCH_SYSTEM_PROMPT,
                    messages=[
                        {"role": "user", "content": f"Research the following topic comprehensively:\n\n{topic}"},
                    ],
                )
                content = response.content[0].text

            else:
                # Standard: 3-call refinement chain
                messages = [
                    {"role": "user", "content": f"Research the following topic comprehensively:\n\n{topic}"},
                ]

                # Call 1: Initial research
                r1 = await with_retries(
                    client.messages.create,
                    model=model,
                    max_tokens=4096,
                    system=RESEARCH_SYSTEM_PROMPT,
                    messages=messages,
                )
                messages.append({"role": "assistant", "content": r1.content[0].text})

                # Call 2: Identify gaps
                messages.append({"role": "user", "content": REFINEMENT_PROMPT})
                r2 = await with_retries(
                    client.messages.create,
                    model=model,
                    max_tokens=4096,
                    system=RESEARCH_SYSTEM_PROMPT,
                    messages=messages,
                )
                messages.append({"role": "assistant", "content": r2.content[0].text})

                # Call 3: Synthesise
                messages.append({"role": "user", "content": SYNTHESIS_PROMPT})
                r3 = await with_retries(
                    client.messages.create,
                    model=model,
                    max_tokens=8192,
                    system=RESEARCH_SYSTEM_PROMPT,
                    messages=messages,
                )
                content = r3.content[0].text

            return ResearchResult(
                provider=self.name,
                model=model,
                content=content,
                duration_seconds=time.monotonic() - start,
            )
        except Exception as exc:
            return ResearchResult(
                provider=self.name,
                model=model,
                content="",
                duration_seconds=time.monotonic() - start,
                error=f"{type(exc).__name__}: {exc}",
            )
