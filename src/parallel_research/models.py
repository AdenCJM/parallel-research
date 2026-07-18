from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Depth(StrEnum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"

    @property
    def max_output_tokens(self) -> int:
        return {Depth.QUICK: 4096, Depth.STANDARD: 8192, Depth.DEEP: 16384}[self]

    @property
    def wait_seconds(self) -> int:
        return {Depth.QUICK: 90, Depth.STANDARD: 300, Depth.DEEP: 600}[self]


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    RESUMABLE = "resumable"


@dataclass(slots=True)
class Citation:
    url: str
    title: str | None = None
    provider: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(slots=True)
class Usage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    searches: int | None = None
    reported_cost_usd: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(slots=True)
class ResearchResult:
    provider: str
    model: str
    content: str
    duration_seconds: float
    status: RunStatus = RunStatus.SUCCEEDED
    citations: list[Citation] = field(default_factory=list)
    usage: Usage | None = None
    request_id: str | None = None
    error: str | None = None


@dataclass(slots=True)
class ProviderState:
    status: RunStatus = RunStatus.PENDING
    model: str | None = None
    request_id: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None
    raw_file: str | None = None
    structured_file: str | None = None
    citations: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(slots=True)
class RunManifest:
    schema_version: int
    run_id: str
    topic: str
    topic_slug: str
    requested_depth: str
    created_at: str
    updated_at: str
    status: RunStatus
    providers: dict[str, ProviderState]
    completed_at: str | None = None
    meta_analysis: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["providers"] = {
            name: {**state.to_dict(), "status": state.status.value}
            for name, state in self.providers.items()
        }
        return {key: value for key, value in data.items() if value is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunManifest:
        provider_data = data.get("providers", {})
        providers = {
            name: ProviderState(
                **{
                    **values,
                    "status": RunStatus(values.get("status", RunStatus.PENDING.value)),
                }
            )
            for name, values in provider_data.items()
        }
        return cls(
            schema_version=int(data["schema_version"]),
            run_id=str(data["run_id"]),
            topic=str(data["topic"]),
            topic_slug=str(data["topic_slug"]),
            requested_depth=str(data["requested_depth"]),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            status=RunStatus(data["status"]),
            providers=providers,
            completed_at=data.get("completed_at"),
            meta_analysis=data.get("meta_analysis"),
            warnings=list(data.get("warnings", [])),
        )
