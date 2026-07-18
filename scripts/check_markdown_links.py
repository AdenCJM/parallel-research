#!/usr/bin/env python3
"""Fail when a repository Markdown file links to a missing local target."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures: list[str] = []
    for markdown in sorted(root.rglob("*.md")):
        if any(part.startswith(".") and part not in {".", ".."} for part in markdown.parts):
            continue
        for raw_target in LINK.findall(markdown.read_text(encoding="utf-8")):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            target = unquote(target.split("#", 1)[0])
            if not target or "://" in target or target.startswith(("mailto:", "citation")):
                continue
            resolved = (markdown.parent / target).resolve()
            if not resolved.exists():
                failures.append(f"{markdown.relative_to(root)} -> {raw_target}")
    if failures:
        print("Missing local Markdown links:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print("All local Markdown links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
