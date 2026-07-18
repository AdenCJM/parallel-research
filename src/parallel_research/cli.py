from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from .manifest import latest_run_id, load_manifest, record_artifact, resolve_run
from .models import Depth, RunManifest, RunStatus
from .orchestrator import fetch, resume_run, validate_run

DEFAULT_PROVIDERS = "claude,openai,gemini,perplexity"


def _providers(value: str) -> list[str]:
    return list(dict.fromkeys(item.strip().lower() for item in value.split(",") if item.strip()))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="parallel-research")
    parser.add_argument("--version", action="version", version="parallel-research 0.2.0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Start an isolated research run")
    fetch_parser.add_argument("--topic", required=True)
    fetch_parser.add_argument("--depth", choices=[item.value for item in Depth], default="standard")
    fetch_parser.add_argument("--providers", default=DEFAULT_PROVIDERS)
    fetch_parser.add_argument("--output", default=".research")

    status_parser = subparsers.add_parser("status", help="Show a run manifest summary")
    status_parser.add_argument("--run", required=True, dest="run_id")
    status_parser.add_argument("--output", default=".research")

    resume_parser = subparsers.add_parser("resume", help="Resume background provider requests")
    resume_parser.add_argument("--run", required=True, dest="run_id")
    resume_parser.add_argument("--output", default=".research")

    validate_parser = subparsers.add_parser("validate", help="Validate one run's integrity")
    validate_parser.add_argument("--run", required=True, dest="run_id")
    validate_parser.add_argument("--output", default=".research")

    latest_parser = subparsers.add_parser("latest", help="Print the latest isolated run ID")
    latest_parser.add_argument("--output", default=".research")

    artifact_parser = subparsers.add_parser(
        "record-artifact", help="Record a structured report or meta-analysis in a run manifest"
    )
    artifact_parser.add_argument("--run", required=True, dest="run_id")
    artifact_parser.add_argument("--file", required=True, dest="relative_file")
    artifact_parser.add_argument("--provider")
    artifact_parser.add_argument("--meta", action="store_true")
    artifact_parser.add_argument("--output", default=".research")
    return parser


def _print_summary(run: RunManifest, directory: Path) -> None:
    print(f"Run: {run.run_id}")
    print(f"Topic: {run.topic}")
    print(f"Status: {run.status.value}")
    for name, state in run.providers.items():
        detail = f" ({state.error})" if state.error else ""
        print(f"  {name}: {state.status.value}{detail}")
    print(f"Output: {directory}")


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "fetch":
            if args.depth == Depth.DEEP.value:
                print(
                    "WARNING: Deep research can take tens of minutes and incur material API cost.",
                    file=sys.stderr,
                )
            manifest, directory = asyncio.run(
                fetch(
                    args.topic,
                    Depth(args.depth),
                    _providers(args.providers),
                    Path(args.output),
                )
            )
            _print_summary(manifest, directory)
            raise SystemExit(0 if manifest.status != RunStatus.FAILED else 1)
        if args.command == "status":
            directory = resolve_run(Path(args.output), args.run_id)
            _print_summary(load_manifest(directory), directory)
            return
        if args.command == "resume":
            manifest, directory = asyncio.run(resume_run(Path(args.output), args.run_id))
            _print_summary(manifest, directory)
            raise SystemExit(0 if manifest.status != RunStatus.FAILED else 1)
        if args.command == "validate":
            directory = resolve_run(Path(args.output), args.run_id)
            errors = validate_run(directory)
            if errors:
                print("Run validation failed:", file=sys.stderr)
                for error in errors:
                    print(f"  - {error}", file=sys.stderr)
                raise SystemExit(1)
            print(f"Run is valid: {args.run_id}")
            return
        if args.command == "latest":
            print(latest_run_id(Path(args.output)))
            return
        if args.command == "record-artifact":
            if args.meta == bool(args.provider):
                raise ValueError("Select exactly one of --meta or --provider")
            record_artifact(
                Path(args.output),
                args.run_id,
                args.relative_file,
                provider=args.provider,
                meta=args.meta,
            )
            print(f"Recorded artifact for run {args.run_id}: {args.relative_file}")
            return
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


def legacy_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Compatibility interface; prefer `parallel-research fetch`."
    )
    parser.add_argument("--topic", required=True)
    parser.add_argument("--depth", choices=[item.value for item in Depth], default="standard")
    parser.add_argument("--providers", default=DEFAULT_PROVIDERS)
    parser.add_argument("--output", default=".research")
    args = parser.parse_args(argv)
    main(
        [
            "fetch",
            "--topic",
            args.topic,
            "--depth",
            args.depth,
            "--providers",
            args.providers,
            "--output",
            args.output,
        ]
    )
