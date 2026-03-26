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


class GeminiProvider(BaseProvider):
    """Google Gemini provider. No native deep research — deep falls back to standard."""

    name = "gemini"

    def __init__(self) -> None:
        self.api_key = os.environ.get("GOOGLE_AI_API_KEY", "")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def research(self, topic: str, depth: Depth) -> ResearchResult:
        from google import genai

        start = time.monotonic()
        model = "gemini-2.5-pro"
        client = genai.Client(api_key=self.api_key)

        # Deep falls back to standard (no native deep research)
        effective_depth = Depth.STANDARD if depth == Depth.DEEP else depth

        try:
            if effective_depth == Depth.QUICK:
                response = await with_retries(
                    client.aio.models.generate_content,
                    model=model,
                    contents=f"{RESEARCH_SYSTEM_PROMPT}\n\nResearch the following topic comprehensively:\n\n{topic}",
                )
                content = response.text

            else:
                # Standard: 3-call refinement chain
                # Gemini doesn't have a native multi-turn async API with history,
                # so we build the context manually in each call.
                prompt_1 = f"{RESEARCH_SYSTEM_PROMPT}\n\nResearch the following topic comprehensively:\n\n{topic}"
                r1 = await with_retries(
                    client.aio.models.generate_content,
                    model=model,
                    contents=prompt_1,
                )
                text_1 = r1.text

                prompt_2 = (
                    f"{RESEARCH_SYSTEM_PROMPT}\n\n"
                    f"Previous research:\n{text_1}\n\n"
                    f"{REFINEMENT_PROMPT}"
                )
                r2 = await with_retries(
                    client.aio.models.generate_content,
                    model=model,
                    contents=prompt_2,
                )
                text_2 = r2.text

                prompt_3 = (
                    f"{RESEARCH_SYSTEM_PROMPT}\n\n"
                    f"Previous research:\n{text_1}\n\n"
                    f"Gap analysis:\n{text_2}\n\n"
                    f"{SYNTHESIS_PROMPT}"
                )
                r3 = await with_retries(
                    client.aio.models.generate_content,
                    model=model,
                    contents=prompt_3,
                )
                content = r3.text

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
