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


class PerplexityProvider(BaseProvider):
    name = "perplexity"

    def __init__(self) -> None:
        super().__init__()
        self.api_key = os.environ.get("PERPLEXITY_API_KEY", "")
        self.model = os.environ.get("PERPLEXITY_MODEL", "sonar-pro")
        self.deep_model = os.environ.get("PERPLEXITY_DEEP_MODEL", "sonar-deep-research")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def research(
        self,
        topic: str,
        depth: Depth,
        progress: ProgressCallback | None = None,
    ) -> ResearchResult:
        from perplexity import AsyncPerplexity

        start = time.monotonic()
        client = AsyncPerplexity(api_key=self.api_key)
        model = self.deep_model if depth == Depth.DEEP else self.model
        messages: list[dict[str, str]] = [
            {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
            {"role": "user", "content": f"Research this topic comprehensively:\n\n{topic}"},
        ]
        try:
            if depth == Depth.DEEP:
                submission = await with_retries(
                    client.async_.chat.completions.create,
                    request={
                        "model": model,
                        "messages": messages,
                        "reasoning_effort": os.environ.get("PERPLEXITY_REASONING_EFFORT", "medium"),
                    },
                )
                self.active_request_id = submission.id
                if progress:
                    await progress(
                        {
                            "status": RunStatus.RUNNING,
                            "request_id": submission.id,
                            "model": model,
                        }
                    )
                completed = await self._poll_async(client, submission)
                return self._async_result(completed, model, start)
            response = await self._call(client, model, messages, depth)
            if depth == Depth.STANDARD:
                messages.extend(
                    [
                        {"role": "assistant", "content": response.choices[0].message.content},
                        {"role": "user", "content": REFINEMENT_PROMPT},
                    ]
                )
                response = await self._call(client, model, messages, depth)
                messages.extend(
                    [
                        {"role": "assistant", "content": response.choices[0].message.content},
                        {"role": "user", "content": SYNTHESIS_PROMPT},
                    ]
                )
                response = await self._call(client, model, messages, depth)
            return self._result(response, model, start)
        except Exception as exc:
            return ResearchResult(
                provider=self.name,
                model=model,
                content="",
                duration_seconds=time.monotonic() - start,
                status=RunStatus.FAILED,
                error=f"{type(exc).__name__}: {redact_secrets(exc)}",
            )

    async def resume(
        self,
        request_id: str,
        depth: Depth,
        progress: ProgressCallback | None = None,
    ) -> ResearchResult:
        from perplexity import AsyncPerplexity

        start = time.monotonic()
        self.active_request_id = request_id
        client = AsyncPerplexity(api_key=self.api_key)
        response = await with_retries(client.async_.chat.completions.get, request_id)
        if progress:
            await progress(
                {
                    "status": RunStatus.RUNNING,
                    "request_id": request_id,
                    "model": self.deep_model,
                }
            )
        completed = await self._poll_async(client, response)
        return self._async_result(completed, self.deep_model, start)

    async def _poll_async(self, client: Any, response: Any) -> Any:
        while value(response, "status") in {"CREATED", "IN_PROGRESS"}:
            await asyncio.sleep(5)
            response = await with_retries(client.async_.chat.completions.get, response.id)
        return response

    def _async_result(self, response: Any, model: str, start: float) -> ResearchResult:
        status = value(response, "status")
        if status != "COMPLETED" or value(response, "response") is None:
            return ResearchResult(
                provider=self.name,
                model=model,
                content="",
                duration_seconds=time.monotonic() - start,
                status=(
                    RunStatus.RESUMABLE
                    if status in {"CREATED", "IN_PROGRESS"}
                    else RunStatus.FAILED
                ),
                request_id=value(response, "id"),
                error=value(response, "error_message") or f"Request ended with status: {status}",
            )
        result = self._result(value(response, "response"), model, start)
        result.request_id = value(response, "id")
        return result

    async def _call(
        self,
        client: Any,
        model: str,
        messages: list[dict[str, str]],
        depth: Depth,
    ) -> Any:
        kwargs: dict[str, Any] = {"model": model, "messages": messages}
        if depth == Depth.DEEP:
            kwargs["reasoning_effort"] = os.environ.get("PERPLEXITY_REASONING_EFFORT", "medium")
        else:
            kwargs["max_tokens"] = depth.max_output_tokens
        return await with_retries(client.chat.completions.create, **kwargs)

    def _result(self, response: Any, model: str, start: float) -> ResearchResult:
        citations: list[Citation] = []
        search_results = value(response, "search_results", []) or []
        for item in search_results:
            url = value(item, "url")
            if url:
                citations.append(Citation(url=url, title=value(item, "title"), provider=self.name))
        for url in value(response, "citations", []) or []:
            citations.append(Citation(url=str(url), provider=self.name))
        return ResearchResult(
            provider=self.name,
            model=model,
            content=response.choices[0].message.content or "",
            duration_seconds=time.monotonic() - start,
            citations=dedupe_citations(citations),
            usage=usage_from(value(response, "usage")),
            request_id=value(response, "id"),
        )
