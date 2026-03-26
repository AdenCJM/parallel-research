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


class PerplexityProvider(BaseProvider):
    """Perplexity API provider. Native deep research via sonar-deep-research."""

    name = "perplexity"

    def __init__(self) -> None:
        self.api_key = os.environ.get("PERPLEXITY_API_KEY", "")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _model_for_depth(self, depth: Depth) -> str:
        if depth == Depth.DEEP:
            return "sonar-deep-research"
        return "sonar-pro"

    async def research(self, topic: str, depth: Depth) -> ResearchResult:
        from perplexity import AsyncPerplexity

        start = time.monotonic()
        model = self._model_for_depth(depth)
        client = AsyncPerplexity(api_key=self.api_key)

        try:
            if depth == Depth.QUICK or depth == Depth.DEEP:
                # Single call — quick uses sonar-pro, deep uses sonar-deep-research
                response = await with_retries(
                    client.chat.completions.create,
                    model=model,
                    messages=[
                        {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Research the following topic comprehensively:\n\n{topic}"},
                    ],
                )
                content = response.choices[0].message.content

            else:
                # Standard: 3-call refinement chain
                messages = [
                    {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Research the following topic comprehensively:\n\n{topic}"},
                ]

                # Call 1: Initial research
                r1 = await with_retries(
                    client.chat.completions.create,
                    model=model,
                    messages=messages,
                )
                messages.append({"role": "assistant", "content": r1.choices[0].message.content})

                # Call 2: Identify gaps and go deeper
                messages.append({"role": "user", "content": REFINEMENT_PROMPT})
                r2 = await with_retries(
                    client.chat.completions.create,
                    model=model,
                    messages=messages,
                )
                messages.append({"role": "assistant", "content": r2.choices[0].message.content})

                # Call 3: Synthesise
                messages.append({"role": "user", "content": SYNTHESIS_PROMPT})
                r3 = await with_retries(
                    client.chat.completions.create,
                    model=model,
                    messages=messages,
                )
                content = r3.choices[0].message.content

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
