from __future__ import annotations

import asyncio
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from .manifest import (
    create_manifest,
    load_manifest,
    resolve_run,
    save_manifest,
    update_index,
    utc_text,
)
from .models import Depth, ResearchResult, RunManifest, RunStatus
from .providers import ALL_PROVIDERS, BaseProvider
from .safety import redact_secrets


def load_environment(project_dir: Path) -> None:
    load_dotenv(Path.home() / ".env")
    load_dotenv(project_dir / ".env", override=True)


def write_raw_result(directory: Path, manifest: RunManifest, result: ResearchResult) -> str:
    relative = f"raw/{result.provider}.md"
    path = directory / relative
    frontmatter: dict[str, Any] = {
        "schema_version": 2,
        "run_id": manifest.run_id,
        "provider": result.provider,
        "model": result.model,
        "topic": manifest.topic,
        "depth": manifest.requested_depth,
        "status": result.status.value,
        "request_id": result.request_id,
        "duration_seconds": round(result.duration_seconds, 2),
        "citations": [citation.to_dict() for citation in result.citations],
        "usage": result.usage.to_dict() if result.usage else None,
        "error": result.error,
    }
    frontmatter = {key: value for key, value in frontmatter.items() if value is not None}
    body = (
        result.content or f"*No research content. {result.error or 'Provider returned no text.'}*"
    )
    path.write_text(
        "---\n"
        + yaml.safe_dump(frontmatter, default_flow_style=False, sort_keys=False)
        + "---\n\n"
        + body,
        encoding="utf-8",
    )
    return relative


def _apply_result(manifest: RunManifest, result: ResearchResult, raw_file: str) -> None:
    state = manifest.providers[result.provider]
    state.status = result.status
    state.model = result.model
    state.request_id = result.request_id or state.request_id
    state.completed_at = utc_text()
    state.duration_seconds = round(result.duration_seconds, 2)
    state.raw_file = raw_file
    state.citations = [citation.to_dict() for citation in result.citations]
    state.usage = result.usage.to_dict() if result.usage else None
    state.error = redact_secrets(result.error) if result.error else None


def _overall_status(manifest: RunManifest) -> RunStatus:
    statuses = [state.status for state in manifest.providers.values()]
    if statuses and all(status == RunStatus.SUCCEEDED for status in statuses):
        return RunStatus.SUCCEEDED
    if any(status == RunStatus.RESUMABLE for status in statuses):
        return RunStatus.RESUMABLE
    if any(status == RunStatus.SUCCEEDED for status in statuses):
        return RunStatus.PARTIAL
    return RunStatus.FAILED


async def fetch(
    topic: str,
    depth: Depth,
    provider_names: list[str],
    output_root: Path,
    *,
    project_dir: Path | None = None,
    provider_registry: Mapping[str, type[BaseProvider]] | None = None,
) -> tuple[RunManifest, Path]:
    project = (project_dir or Path.cwd()).resolve()
    load_environment(project)
    registry = provider_registry or ALL_PROVIDERS
    unknown = [name for name in provider_names if name not in registry]
    if unknown:
        raise ValueError(f"Unknown providers: {', '.join(unknown)}")
    if not provider_names:
        raise ValueError("At least one provider is required")

    manifest, directory = create_manifest(output_root, topic, depth, provider_names)
    manifest.status = RunStatus.RUNNING
    manifest.warnings.append(
        "Research is sent to third-party providers and may contain untrusted web content."
    )
    save_manifest(directory, manifest)
    update_index(output_root.resolve(), manifest)
    lock = asyncio.Lock()

    async def run_one(name: str) -> ResearchResult:
        provider = registry[name]()
        state = manifest.providers[name]
        state.started_at = utc_text()
        if not provider.available:
            return ResearchResult(
                provider=name,
                model="unknown",
                content="",
                duration_seconds=0,
                status=RunStatus.FAILED,
                error=f"No API key configured for {name}",
            )

        async def progress(update: dict[str, Any]) -> None:
            async with lock:
                if "status" in update:
                    state.status = RunStatus(update["status"])
                state.request_id = update.get("request_id", state.request_id)
                state.model = update.get("model", state.model)
                save_manifest(directory, manifest)

        return await provider.safe_research(topic, depth, progress)

    results = await asyncio.gather(*(run_one(name) for name in provider_names))
    for result in results:
        raw_file = write_raw_result(directory, manifest, result)
        _apply_result(manifest, result, raw_file)

    manifest.status = _overall_status(manifest)
    if manifest.status not in {RunStatus.RUNNING, RunStatus.RESUMABLE}:
        manifest.completed_at = utc_text()
    save_manifest(directory, manifest)
    update_index(output_root.resolve(), manifest)
    return manifest, directory


async def resume_run(
    output_root: Path,
    run_id: str,
    *,
    project_dir: Path | None = None,
    provider_registry: Mapping[str, type[BaseProvider]] | None = None,
) -> tuple[RunManifest, Path]:
    project = (project_dir or Path.cwd()).resolve()
    load_environment(project)
    registry = provider_registry or ALL_PROVIDERS
    directory = resolve_run(output_root, run_id)
    manifest = load_manifest(directory)
    depth = Depth(manifest.requested_depth)
    resumable = [
        name
        for name, state in manifest.providers.items()
        if state.status == RunStatus.RESUMABLE and state.request_id
    ]
    if not resumable:
        raise ValueError(f"Run {run_id} has no resumable provider requests")

    lock = asyncio.Lock()

    async def resume_one(name: str) -> ResearchResult:
        if name not in registry:
            raise ValueError(f"Provider implementation unavailable: {name}")
        provider = registry[name]()
        state = manifest.providers[name]
        if not provider.available:
            return ResearchResult(
                provider=name,
                model=state.model or "unknown",
                content="",
                duration_seconds=0,
                status=RunStatus.RESUMABLE,
                request_id=state.request_id,
                error=f"No API key configured for {name}",
            )

        async def progress(update: dict[str, Any]) -> None:
            async with lock:
                state.status = RunStatus(update.get("status", state.status))
                state.model = update.get("model", state.model)
                save_manifest(directory, manifest)

        return await provider.safe_resume(state.request_id or "", depth, progress)

    results = await asyncio.gather(*(resume_one(name) for name in resumable))
    for result in results:
        raw_file = write_raw_result(directory, manifest, result)
        _apply_result(manifest, result, raw_file)
    manifest.status = _overall_status(manifest)
    if manifest.status != RunStatus.RESUMABLE:
        manifest.completed_at = utc_text()
    save_manifest(directory, manifest)
    update_index(output_root.resolve(), manifest)
    return manifest, directory


def validate_run(directory: Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = load_manifest(directory)
    except Exception as exc:
        return [redact_secrets(exc)]
    for name, state in manifest.providers.items():
        if state.structured_file:
            errors.extend(
                _validate_declared_artifact(
                    directory,
                    state.structured_file,
                    manifest.run_id,
                    f"{name} structured artifact",
                    provider=name,
                )
            )
        if not state.raw_file:
            errors.append(f"{name}: raw_file is missing")
            continue
        raw_path = directory / state.raw_file
        try:
            raw_path.resolve().relative_to(directory.resolve())
        except ValueError:
            errors.append(f"{name}: raw_file escapes the run directory")
            continue
        if not raw_path.is_file():
            errors.append(f"{name}: raw file does not exist: {state.raw_file}")
            continue
        text = raw_path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            errors.append(f"{name}: raw file has no YAML frontmatter")
            continue
        try:
            metadata = yaml.safe_load(text.split("---", 2)[1])
        except yaml.YAMLError as exc:
            errors.append(f"{name}: invalid frontmatter: {exc}")
            continue
        if not isinstance(metadata, dict):
            errors.append(f"{name}: frontmatter must be a mapping")
            continue
        if metadata.get("run_id") != manifest.run_id:
            errors.append(f"{name}: run_id does not match manifest")
        if metadata.get("topic") != manifest.topic:
            errors.append(f"{name}: topic does not match manifest")
    if manifest.meta_analysis:
        errors.extend(
            _validate_declared_artifact(
                directory,
                manifest.meta_analysis,
                manifest.run_id,
                "meta-analysis",
            )
        )
    return errors


def _validate_declared_artifact(
    directory: Path,
    relative_file: str,
    run_id: str,
    label: str,
    *,
    provider: str | None = None,
) -> list[str]:
    artifact = (directory / relative_file).resolve()
    try:
        artifact.relative_to(directory.resolve())
    except ValueError:
        return [f"{label}: path escapes the run directory"]
    if not artifact.is_file():
        return [f"{label}: file does not exist: {relative_file}"]
    text = artifact.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return [f"{label}: file has no YAML frontmatter"]
    try:
        metadata = yaml.safe_load(text.split("---", 2)[1])
    except yaml.YAMLError as exc:
        return [f"{label}: invalid frontmatter: {exc}"]
    errors: list[str] = []
    if not isinstance(metadata, dict) or metadata.get("run_id") != run_id:
        errors.append(f"{label}: run_id does not match manifest")
    if provider and metadata.get("provider") != provider:
        errors.append(f"{label}: provider does not match manifest")
    return errors
