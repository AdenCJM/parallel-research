from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..models import Citation, Usage


def value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def dedupe_citations(citations: Iterable[Citation]) -> list[Citation]:
    unique: dict[str, Citation] = {}
    for citation in citations:
        url = citation.url.strip()
        if url and url not in unique:
            citation.url = url
            unique[url] = citation
    return list(unique.values())


def usage_from(obj: Any) -> Usage | None:
    if obj is None:
        return None
    input_tokens = (
        value(obj, "input_tokens")
        or value(obj, "prompt_tokens")
        or value(obj, "prompt_token_count")
    )
    output_tokens = (
        value(obj, "output_tokens")
        or value(obj, "completion_tokens")
        or value(obj, "candidates_token_count")
    )
    total_tokens = value(obj, "total_tokens") or value(obj, "total_token_count")
    searches = value(obj, "num_search_queries") or value(obj, "search_queries")
    cost = value(value(obj, "cost", {}), "total_cost")
    if not any(
        item is not None for item in (input_tokens, output_tokens, total_tokens, searches, cost)
    ):
        return None
    return Usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        searches=searches,
        reported_cost_usd=cost,
    )
