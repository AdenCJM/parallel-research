from __future__ import annotations

import os
import time
from typing import Any

from ..models import Citation, Depth, ResearchResult, RunStatus, Usage
from ..safety import redact_secrets
from ._utils import dedupe_citations, value
from .base import (
    REFINEMENT_PROMPT,
    RESEARCH_SYSTEM_PROMPT,
    SYNTHESIS_PROMPT,
    BaseProvider,
    ProgressCallback,
    with_retries,
)


class ClaudeProvider(BaseProvider):
    name = "claude"

    def __init__(self) -> None:
        super().__init__()
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def research(
        self,
        topic: str,
        depth: Depth,
        progress: ProgressCallback | None = None,
    ) -> ResearchResult:
        from anthropic import AsyncAnthropic

        start = time.monotonic()
        client = AsyncAnthropic(api_key=self.api_key)
        effective_depth = Depth.STANDARD if depth == Depth.DEEP else depth
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": f"Research this topic comprehensively:\n\n{topic}"}
        ]
        try:
            response = await self._call(client, messages, effective_depth.max_output_tokens)
            if effective_depth == Depth.STANDARD:
                messages.extend(
                    [
                        {"role": "assistant", "content": self._text(response)},
                        {"role": "user", "content": REFINEMENT_PROMPT},
                    ]
                )
                response = await self._call(client, messages, effective_depth.max_output_tokens)
                messages.extend(
                    [
                        {"role": "assistant", "content": self._text(response)},
                        {"role": "user", "content": SYNTHESIS_PROMPT},
                    ]
                )
                response = await self._call(client, messages, effective_depth.max_output_tokens)
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

    async def _call(self, client: Any, messages: list[dict[str, Any]], max_tokens: int) -> Any:
        return await with_retries(
            client.messages.create,
            model=self.model,
            max_tokens=max_tokens,
            system=RESEARCH_SYSTEM_PROMPT,
            messages=messages,
            tools=[
                {
                    "type": "web_search_20260318",
                    "name": "web_search",
                    "allowed_callers": ["direct"],
                    "max_uses": int(os.environ.get("ANTHROPIC_MAX_SEARCHES", "8")),
                }
            ],
        )

    def _result(self, response: Any, start: float) -> ResearchResult:
        text_parts: list[str] = []
        citations: list[Citation] = []
        for block in value(response, "content", []) or []:
            text = value(block, "text")
            if text:
                text_parts.append(text)
            for citation in value(block, "citations", []) or []:
                url = value(citation, "url")
                if url:
                    citations.append(
                        Citation(
                            url=url,
                            title=value(citation, "title"),
                            provider=self.name,
                        )
                    )
        usage_obj = value(response, "usage")
        usage = None
        if usage_obj is not None:
            input_tokens = value(usage_obj, "input_tokens")
            output_tokens = value(usage_obj, "output_tokens")
            usage = Usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=(input_tokens + output_tokens)
                if input_tokens is not None and output_tokens is not None
                else None,
            )
        return ResearchResult(
            provider=self.name,
            model=self.model,
            content="\n\n".join(text_parts),
            duration_seconds=time.monotonic() - start,
            citations=dedupe_citations(citations),
            usage=usage,
            request_id=value(response, "id"),
        )

    def _text(self, response: Any) -> str:
        return "\n\n".join(
            text for block in value(response, "content", []) or [] if (text := value(block, "text"))
        )
