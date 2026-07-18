from __future__ import annotations

import asyncio
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


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self) -> None:
        super().__init__()
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.model = os.environ.get("OPENAI_MODEL", "gpt-5.6-terra")
        self.deep_model = os.environ.get("OPENAI_DEEP_MODEL", "o3-deep-research")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def research(
        self,
        topic: str,
        depth: Depth,
        progress: ProgressCallback | None = None,
    ) -> ResearchResult:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        start = time.monotonic()
        try:
            if depth == Depth.DEEP:
                response = await with_retries(
                    client.responses.create,
                    model=self.deep_model,
                    instructions=RESEARCH_SYSTEM_PROMPT,
                    input=topic,
                    tools=[{"type": "web_search_preview"}],
                    max_tool_calls=int(os.environ.get("OPENAI_MAX_TOOL_CALLS", "30")),
                    background=True,
                )
                self.active_request_id = response.id
                if progress:
                    await progress(
                        {
                            "status": RunStatus.RUNNING,
                            "request_id": response.id,
                            "model": self.deep_model,
                        }
                    )
                response = await self._poll(client, response)
                return self._result(response, self.deep_model, start)

            response = await self._grounded_call(client, topic, depth.max_output_tokens)
            if depth == Depth.STANDARD:
                response = await self._grounded_call(
                    client,
                    REFINEMENT_PROMPT,
                    depth.max_output_tokens,
                    previous_response_id=response.id,
                )
                response = await self._grounded_call(
                    client,
                    SYNTHESIS_PROMPT,
                    depth.max_output_tokens,
                    previous_response_id=response.id,
                )
            return self._result(response, self.model, start)
        except Exception as exc:
            return ResearchResult(
                provider=self.name,
                model=self.deep_model if depth == Depth.DEEP else self.model,
                content="",
                duration_seconds=time.monotonic() - start,
                status=RunStatus.FAILED,
                request_id=self.active_request_id,
                error=f"{type(exc).__name__}: {redact_secrets(exc)}",
            )

    async def resume(
        self,
        request_id: str,
        depth: Depth,
        progress: ProgressCallback | None = None,
    ) -> ResearchResult:
        from openai import AsyncOpenAI

        start = time.monotonic()
        self.active_request_id = request_id
        client = AsyncOpenAI(api_key=self.api_key)
        response = await with_retries(client.responses.retrieve, request_id)
        if progress:
            await progress(
                {"status": RunStatus.RUNNING, "request_id": request_id, "model": self.deep_model}
            )
        async with asyncio.timeout(depth.wait_seconds):
            response = await self._poll(client, response)
        return self._result(response, self.deep_model, start)

    async def _grounded_call(
        self,
        client: Any,
        prompt: str,
        max_output_tokens: int,
        previous_response_id: str | None = None,
    ) -> Any:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "instructions": RESEARCH_SYSTEM_PROMPT,
            "input": prompt,
            "tools": [{"type": "web_search"}],
            "max_output_tokens": max_output_tokens,
        }
        if previous_response_id:
            kwargs["previous_response_id"] = previous_response_id
        return await with_retries(client.responses.create, **kwargs)

    async def _poll(self, client: Any, response: Any) -> Any:
        while value(response, "status") in {"queued", "in_progress"}:
            await asyncio.sleep(5)
            response = await with_retries(client.responses.retrieve, response.id)
        return response

    def _result(self, response: Any, model: str, start: float) -> ResearchResult:
        status = value(response, "status")
        if status != "completed":
            resumable = status in {"queued", "in_progress"}
            return ResearchResult(
                provider=self.name,
                model=model,
                content="",
                duration_seconds=time.monotonic() - start,
                status=RunStatus.RESUMABLE if resumable else RunStatus.FAILED,
                request_id=value(response, "id"),
                error=f"Request ended with status: {status}",
            )
        citations: list[Citation] = []
        for item in value(response, "output", []) or []:
            for block in value(item, "content", []) or []:
                for annotation in value(block, "annotations", []) or []:
                    url = value(annotation, "url")
                    if url:
                        citations.append(
                            Citation(
                                url=url,
                                title=value(annotation, "title"),
                                provider=self.name,
                            )
                        )
        return ResearchResult(
            provider=self.name,
            model=model,
            content=value(response, "output_text", "") or "",
            duration_seconds=time.monotonic() - start,
            citations=dedupe_citations(citations),
            usage=usage_from(value(response, "usage")),
            request_id=value(response, "id"),
        )
