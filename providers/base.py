from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, TypeVar

import httpx


class Depth(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"

    @property
    def max_output_tokens(self) -> int:
        return {Depth.QUICK: 4096, Depth.STANDARD: 8192, Depth.DEEP: 16384}[self]

    @property
    def timeout_seconds(self) -> int:
        return {Depth.QUICK: 60, Depth.STANDARD: 180, Depth.DEEP: 600}[self]


@dataclass
class ResearchResult:
    provider: str
    model: str
    content: str
    duration_seconds: float
    error: str | None = None


RESEARCH_SYSTEM_PROMPT = (
    "You are a research assistant. Provide comprehensive, well-sourced research "
    "on the given topic. Include specific facts, figures, named sources, and URLs "
    "where available. Structure your response with clear sections."
)

REFINEMENT_PROMPT = (
    "Given your previous response, identify the 3 biggest gaps or unanswered "
    "questions, then research those in depth."
)

SYNTHESIS_PROMPT = (
    "Synthesise all your findings into a single coherent, comprehensive response. "
    "Preserve all specific facts, figures, and sources."
)


T = TypeVar("T")


async def with_retries(
    fn: Callable[..., T],
    *args,
    max_retries: int = 3,
    **kwargs,
) -> T:
    """Call fn with exponential backoff on rate limit and server errors."""
    delays = [1, 2, 4]
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except (httpx.HTTPStatusError, Exception) as exc:
            last_exc = exc
            status = getattr(exc, "status_code", None) or getattr(
                getattr(exc, "response", None), "status_code", None
            )
            is_retryable = status in (429, 500, 502, 503, 529) if status else False

            # Also retry on common SDK rate limit exceptions
            exc_name = type(exc).__name__.lower()
            if "ratelimit" in exc_name or "rate_limit" in exc_name:
                is_retryable = True

            if not is_retryable or attempt >= max_retries:
                raise

            delay = delays[attempt] if attempt < len(delays) else delays[-1]
            await asyncio.sleep(delay)

    raise last_exc  # type: ignore[misc]


class BaseProvider(ABC):
    """Base class for all research providers."""

    name: str  # e.g. "claude", "openai", "gemini", "perplexity"

    @abstractmethod
    async def research(self, topic: str, depth: Depth) -> ResearchResult:
        """Run research query. Must never raise — return ResearchResult with error set on failure."""
        ...

    async def _safe_research(self, topic: str, depth: Depth) -> ResearchResult:
        """Wrapper that catches all exceptions and returns them as ResearchResult errors."""
        start = time.monotonic()
        try:
            return await asyncio.wait_for(
                self.research(topic, depth),
                timeout=depth.timeout_seconds,
            )
        except asyncio.TimeoutError:
            return ResearchResult(
                provider=self.name,
                model="unknown",
                content="",
                duration_seconds=time.monotonic() - start,
                error=f"Timeout after {depth.timeout_seconds}s",
            )
        except Exception as exc:
            return ResearchResult(
                provider=self.name,
                model="unknown",
                content="",
                duration_seconds=time.monotonic() - start,
                error=f"{type(exc).__name__}: {exc}",
            )
