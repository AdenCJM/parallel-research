from __future__ import annotations

import os
import time
from typing import Any

from ..models import Citation, Depth, ResearchResult, RunStatus
from ..safety import redact_secrets
from ._utils import dedupe_citations, usage_from, value
from .base import (
    REFINEMENT_PROMPT,
    RESEARCH_SYSTEM_PROMPT,
    SYNTHESIS_PROMPT,
    BaseProvider,
    ProgressCallback,
    with_retries,
)


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self) -> None:
        super().__init__()
        self.api_key = os.environ.get("GOOGLE_AI_API_KEY", "") or os.environ.get(
            "GEMINI_API_KEY", ""
        )
        self.model = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def research(
        self,
        topic: str,
        depth: Depth,
        progress: ProgressCallback | None = None,
    ) -> ResearchResult:
        from google import genai

        start = time.monotonic()
        client = genai.Client(api_key=self.api_key)
        effective_depth = Depth.STANDARD if depth == Depth.DEEP else depth
        try:
            first = await self._call(
                client,
                f"{RESEARCH_SYSTEM_PROMPT}\n\nResearch this topic comprehensively:\n\n{topic}",
                effective_depth.max_output_tokens,
            )
            response = first
            if effective_depth == Depth.STANDARD:
                second = await self._call(
                    client,
                    f"Previous research:\n{first.text}\n\n{REFINEMENT_PROMPT}",
                    effective_depth.max_output_tokens,
                )
                response = await self._call(
                    client,
                    (
                        f"Previous research:\n{first.text}\n\n"
                        f"Evidence-gap research:\n{second.text}\n\n{SYNTHESIS_PROMPT}"
                    ),
                    effective_depth.max_output_tokens,
                )
            return self._result(response, start)
        except Exception as exc:
            return ResearchResult(
                provider=self.name,
                model=self.model,
                content="",
                duration_seconds=time.monotonic() - start,
                status=RunStatus.FAILED,
                error=f"{type(exc).__name__}: {redact_secrets(exc)}",
            )

    async def _call(self, client: Any, prompt: str, max_output_tokens: int) -> Any:
        from google.genai import types

        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            max_output_tokens=max_output_tokens,
        )
        return await with_retries(
            client.aio.models.generate_content,
            model=self.model,
            contents=prompt,
            config=config,
        )

    def _result(self, response: Any, start: float) -> ResearchResult:
        citations: list[Citation] = []
        for candidate in value(response, "candidates", []) or []:
            metadata = value(candidate, "grounding_metadata") or value(
                candidate, "groundingMetadata"
            )
            for chunk in value(metadata, "grounding_chunks", []) or value(
                metadata, "groundingChunks", []
            ):
                web = value(chunk, "web")
                url = value(web, "uri")
                if url:
                    citations.append(
                        Citation(url=url, title=value(web, "title"), provider=self.name)
                    )
        return ResearchResult(
            provider=self.name,
            model=self.model,
            content=value(response, "text", "") or "",
            duration_seconds=time.monotonic() - start,
            citations=dedupe_citations(citations),
            usage=usage_from(value(response, "usage_metadata")),
            request_id=value(response, "response_id"),
        )
