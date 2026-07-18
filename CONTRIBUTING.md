# Contributing

Use Python 3.11 or newer and install the locked development environment:

```bash
uv sync --extra dev
```

Before opening a pull request, run:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
uv run python scripts/check_markdown_links.py
bash scripts/audit_dependencies
uv build
```

Provider changes must include mocked contract tests. Tests must not require API keys or make
billable requests. Live-provider checks should be run manually with an explicit budget.
