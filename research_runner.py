#!/usr/bin/env python3
"""Multi-LLM parallel research orchestrator.

Usage:
    python research_runner.py --topic "Your research topic" [--depth quick|standard|deep]
        [--providers claude,openai,gemini,perplexity] [--output .research/]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

from providers.base import Depth, ResearchResult
from providers.claude import ClaudeProvider
from providers.gemini import GeminiProvider
from providers.openai_provider import OpenAIProvider
from providers.perplexity import PerplexityProvider


ALL_PROVIDERS = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "perplexity": PerplexityProvider,
}


def slugify(topic: str) -> str:
    """Convert topic to a URL-safe slug.

    Lowercase, spaces to hyphens, strip non-alphanumeric except hyphens,
    collapse multiple hyphens, strip leading/trailing hyphens, truncate at 60 chars.
    """
    slug = topic.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug[:60]


def write_raw_file(
    output_dir: Path,
    result: ResearchResult,
    topic: str,
    timestamp: str,
) -> str:
    """Write raw markdown with YAML frontmatter. Returns relative path."""
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{result.provider}-{timestamp}.md"
    filepath = raw_dir / filename

    frontmatter = {
        "provider": result.provider,
        "model": result.model,
        "topic": topic,
        "timestamp": timestamp,
        "duration_seconds": round(result.duration_seconds, 1),
    }
    if result.error:
        frontmatter["error"] = result.error

    content = "---\n"
    content += yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    content += "---\n\n"
    content += result.content if result.content else f"*Error: {result.error}*"

    filepath.write_text(content)
    return f"raw/{filename}"


def write_manifest(
    output_dir: Path,
    topic: str,
    slug: str,
    depth: str,
    start_time: datetime,
    end_time: datetime,
    results: dict[str, ResearchResult],
    raw_paths: dict[str, str],
) -> None:
    """Write research.yaml manifest."""
    # Determine overall status
    statuses = {r.provider: ("success" if not r.error else "failed") for r in results.values()}
    any_success = "success" in statuses.values()
    all_success = all(s == "success" for s in statuses.values())

    manifest = {
        "topic": topic,
        "topic_slug": slug,
        "depth": depth,
        "initiated": start_time.isoformat(),
        "completed": end_time.isoformat(),
        "status": "complete" if all_success else ("partial" if any_success else "failed"),
        "providers": {},
        "meta_analysis": None,
    }

    for name, result in results.items():
        entry: dict = {"status": "success" if not result.error else "failed"}
        if result.error:
            entry["error"] = result.error
        else:
            entry["model"] = result.model
            entry["duration_seconds"] = round(result.duration_seconds, 1)
        entry["raw_file"] = raw_paths.get(name)
        entry["structured_file"] = None  # Filled by Phase 2 (Claude Code)
        manifest["providers"][name] = entry

    (output_dir / "research.yaml").write_text(
        yaml.dump(manifest, default_flow_style=False, sort_keys=False)
    )


async def run(
    topic: str,
    depth: Depth,
    provider_names: list[str],
    output_dir: Path,
) -> bool:
    """Run parallel research. Returns True if at least one provider succeeded."""
    # Load environment variables
    load_dotenv(Path.home() / ".env")
    load_dotenv(Path.cwd() / ".env", override=True)

    # Instantiate requested providers
    providers = {}
    for name in provider_names:
        if name not in ALL_PROVIDERS:
            print(f"WARNING: Unknown provider '{name}', skipping.", file=sys.stderr)
            continue
        instance = ALL_PROVIDERS[name]()
        if not instance.available:
            print(f"WARNING: No API key for '{name}', skipping.", file=sys.stderr)
            continue
        providers[name] = instance

    if not providers:
        print("ERROR: No providers available. Check your API keys in ~/.env", file=sys.stderr)
        return False

    print(f"Researching: {topic}")
    print(f"Depth: {depth.value} | Providers: {', '.join(providers.keys())}")

    output_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(topic)
    start_time = datetime.now(timezone.utc)
    timestamp = start_time.strftime("%Y%m%d-%H%M")

    # Run all providers in parallel via _safe_research (catches all exceptions)
    tasks = {
        name: provider._safe_research(topic, depth)
        for name, provider in providers.items()
    }
    raw_results = await asyncio.gather(*tasks.values())
    results = dict(zip(tasks.keys(), raw_results))

    end_time = datetime.now(timezone.utc)

    # Write raw files
    raw_paths: dict[str, str] = {}
    for name, result in results.items():
        raw_paths[name] = write_raw_file(output_dir, result, topic, timestamp)
        status = "OK" if not result.error else f"FAILED: {result.error}"
        print(f"  {name}: {status} ({result.duration_seconds:.1f}s)")

    # Write manifest
    write_manifest(output_dir, topic, slug, depth.value, start_time, end_time, results, raw_paths)

    any_success = any(not r.error for r in results.values())
    print(f"\nResults written to {output_dir}/")
    return any_success


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-LLM parallel research runner")
    parser.add_argument("--topic", required=True, help="Research topic")
    parser.add_argument(
        "--depth",
        choices=["quick", "standard", "deep"],
        default="standard",
        help="Research depth (default: standard)",
    )
    parser.add_argument(
        "--providers",
        default="claude,openai,gemini,perplexity",
        help="Comma-separated provider list (default: all)",
    )
    parser.add_argument(
        "--output",
        default=".research",
        help="Output directory (default: .research/)",
    )

    args = parser.parse_args()
    provider_list = [p.strip() for p in args.providers.split(",")]
    depth = Depth(args.depth)
    output_dir = Path(args.output)

    success = asyncio.run(run(args.topic, depth, provider_list, output_dir))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
