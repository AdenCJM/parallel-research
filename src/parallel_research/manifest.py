from __future__ import annotations

import os
import re
import secrets
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .models import Depth, ProviderState, RunManifest, RunStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_text(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat().replace("+00:00", "Z")


def slugify(topic: str) -> str:
    normalized = unicodedata.normalize("NFKD", topic).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug[:60].rstrip("-") or "research"


def make_run_id(topic: str, now: datetime | None = None) -> str:
    moment = now or utc_now()
    stamp = moment.strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{secrets.token_hex(3)}-{slugify(topic)}"


def run_dir(output_root: Path, run_id: str) -> Path:
    return output_root / "runs" / run_id


def create_manifest(
    output_root: Path,
    topic: str,
    depth: Depth,
    provider_names: list[str],
) -> tuple[RunManifest, Path]:
    output_root = output_root.resolve()
    run_id = make_run_id(topic)
    directory = run_dir(output_root, run_id)
    (directory / "raw").mkdir(parents=True, exist_ok=False)
    (directory / "structured").mkdir()
    now = utc_text()
    manifest = RunManifest(
        schema_version=2,
        run_id=run_id,
        topic=topic,
        topic_slug=slugify(topic),
        requested_depth=depth.value,
        created_at=now,
        updated_at=now,
        status=RunStatus.PENDING,
        providers={name: ProviderState() for name in provider_names},
    )
    save_manifest(directory, manifest)
    update_index(output_root, manifest)
    return manifest, directory


def _atomic_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(4)}.tmp")
    try:
        temporary.write_text(
            yaml.safe_dump(data, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def save_manifest(directory: Path, manifest: RunManifest) -> None:
    manifest.updated_at = utc_text()
    _atomic_yaml(directory / "research.yaml", manifest.to_dict())


def load_manifest(directory: Path) -> RunManifest:
    path = directory / "research.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 2:
        raise ValueError(f"Unsupported or invalid manifest: {path}")
    return RunManifest.from_dict(data)


def resolve_run(output_root: Path, run_id: str) -> Path:
    candidate = run_dir(output_root.resolve(), run_id)
    if not candidate.is_dir():
        raise FileNotFoundError(f"Research run not found: {run_id}")
    return candidate


def latest_run_id(output_root: Path) -> str:
    index_path = output_root.resolve() / "index.yaml"
    if not index_path.is_file():
        raise FileNotFoundError(f"Research index not found: {index_path}")
    data = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    run_id = data.get("latest_run") if isinstance(data, dict) else None
    if not run_id:
        raise ValueError("Research index has no latest_run")
    return str(run_id)


def record_artifact(
    output_root: Path,
    run_id: str,
    relative_file: str,
    *,
    provider: str | None = None,
    meta: bool = False,
) -> RunManifest:
    directory = resolve_run(output_root, run_id)
    manifest = load_manifest(directory)
    artifact = (directory / relative_file).resolve()
    try:
        artifact.relative_to(directory.resolve())
    except ValueError as exc:
        raise ValueError("Artifact path must remain inside the selected run") from exc
    if not artifact.is_file():
        raise FileNotFoundError(f"Artifact does not exist: {relative_file}")
    normalized = artifact.relative_to(directory.resolve()).as_posix()
    expected = "meta-analysis.md" if meta else f"structured/{provider}.md"
    if normalized != expected:
        raise ValueError(f"Artifact path must be {expected}")
    text = artifact.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("Artifact must begin with YAML frontmatter")
    try:
        metadata = yaml.safe_load(text.split("---", 2)[1])
    except yaml.YAMLError as exc:
        raise ValueError(f"Artifact frontmatter is invalid: {exc}") from exc
    if not isinstance(metadata, dict) or metadata.get("run_id") != manifest.run_id:
        raise ValueError("Artifact run_id must match the selected run")
    if not meta and metadata.get("provider") != provider:
        raise ValueError("Structured artifact provider must match --provider")
    if meta:
        manifest.meta_analysis = normalized
    else:
        if not provider or provider not in manifest.providers:
            raise ValueError(f"Provider is not part of this run: {provider}")
        manifest.providers[provider].structured_file = normalized
    save_manifest(directory, manifest)
    update_index(output_root.resolve(), manifest)
    return manifest


def update_index(output_root: Path, manifest: RunManifest) -> None:
    index_path = output_root / "index.yaml"
    data: dict[str, Any] = {"schema_version": 1, "latest_run": manifest.run_id, "runs": []}
    if index_path.exists():
        loaded = yaml.safe_load(index_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data.update(loaded)
    entries = [entry for entry in data.get("runs", []) if entry.get("run_id") != manifest.run_id]
    entries.append(
        {
            "run_id": manifest.run_id,
            "topic": manifest.topic,
            "created_at": manifest.created_at,
            "status": manifest.status.value,
            "manifest": f"runs/{manifest.run_id}/research.yaml",
        }
    )
    data["schema_version"] = 1
    data["latest_run"] = manifest.run_id
    data["runs"] = entries[-100:]
    _atomic_yaml(index_path, data)
