# Architecture Reference

## Overview

Parallel Research is a three-phase, asyncio-based system for orchestrating research queries across multiple LLM providers simultaneously.

```
Phase 1: Parallel Fetch          Phase 2: Structure         Phase 3: Meta-Analysis
(Python asyncio)                 (Claude Code logic)        (Optional synthesis)

User topic ─┬─→ Claude          Raw responses              Structured files
            ├─→ OpenAI          in .research/raw/  ─→      in .research/structured/ ─→
            ├─→ Gemini          with YAML metadata         cross-reference claims
            └─→ Perplexity                                 write meta-analysis.md
```

## Phase 1: Parallel Fetch (Python)

**Entry point:** `research_runner.py:run()` — the async orchestrator.

1. Load environment variables from `~/.env` and project `.env`
2. Instantiate provider classes (claude.py, openai_provider.py, etc.)
3. Check API key availability; skip providers with missing keys
4. Run `provider._safe_research(topic, depth)` concurrently via `asyncio.gather()`
5. Write raw markdown files to `.research/raw/{provider}-{timestamp}.md`
6. Write manifest to `.research/research.yaml` with status and file paths

**Key data structures:**

- `Depth` enum: `QUICK`, `STANDARD`, `DEEP` — controls token limits and timeouts
- `ResearchResult`: dataclass holding provider name, model, content, duration, and optional error
- `BaseProvider`: abstract base class; all providers inherit from this

**Concurrency model:** All providers run in parallel via `asyncio.gather()`. The slowest provider determines overall completion time (no sequential chaining).

**Error handling:** Each provider is wrapped in `_safe_research()`, which catches all exceptions (timeouts, API errors, malformed responses) and returns them as `ResearchResult.error` strings. Phase 1 succeeds if *any* provider succeeds.

## Phase 2: Structure Raw Output (Claude Code)

**Entry point:** Claude Code skill (SKILL.md) — manual Claude-driven processing.

For each provider with `status: success` in `research.yaml`:

1. Read raw file from `.research/raw/{provider}-{timestamp}.md`
2. Parse YAML frontmatter and markdown content
3. Extract and reorganise content into standard template (Summary, Key Findings, Sources, Unique Insights, Limitations)
4. Write to `.research/structured/{provider}-{topic_slug}.md`
5. Update `research.yaml` with `structured_file` path

**Template structure:**
```yaml
---
provider: {provider_name}
model: {model_used}
topic: "{original_topic}"
topic_slug: {url_safe_slug}
depth: {depth}
timestamp: {timestamp}
source_file: {path_to_raw_file}
---

## Summary
[2-3 paragraph synthesis]

## Key Findings
- [Finding with specifics]

## Sources & References
- [URL or citation]

## Unique Insights
[What only this provider surfaced]

## Limitations
[What this provider couldn't answer well]
```

**Output format:** Markdown with YAML frontmatter. Each provider gets exactly one file per topic. Files are idempotent — re-running Phase 2 overwrites previous structured files for the same topic.

## Phase 3: Meta-Analysis (Optional)

**Entry point:** Claude Code with `--meta` flag.

1. Read all `.research/structured/{provider}-{topic_slug}.md` files
2. Parse YAML frontmatter and content from each
3. Cross-reference claims across providers:
   - **High confidence** (3-4 providers agree)
   - **Medium confidence** (2 providers agree)
   - **Low confidence** (1 provider only)
   - **Contradictions** (providers disagree)
4. Write `.research/meta-analysis.md` with synthesis and confidence scoring
5. Update `research.yaml` with `meta_analysis` path

**Output format:** Single markdown file with sections for agreement levels, contradictions, unique insights, and recommended follow-ups.

## Provider Abstraction

All providers inherit from `BaseProvider` (providers/base.py) and implement:

```python
async def research(self, topic: str, depth: Depth) -> ResearchResult:
    """Run research query. Must never raise."""
    ...

@property
def available(self) -> bool:
    """True if API key is present and valid."""
    ...
```

**Provider implementations:**

| Provider | File | Model(s) | Deep Research | Fallback |
|----------|------|----------|:---:|----------|
| Claude | `providers/claude.py` | claude-sonnet-4-6 | None | Standard |
| OpenAI | `providers/openai_provider.py` | gpt-4o, o3-deep-research | Native | Standard |
| Gemini | `providers/gemini.py` | gemini-2.5-pro | None | Standard |
| Perplexity | `providers/perplexity.py` | sonar-pro, sonar-deep-research | Native | Standard |

**Provider responsibilities:**

- Parse `topic` and `depth` arguments
- Make API calls with appropriate system prompts
- Handle rate limits and transient errors (retry with backoff)
- Return `ResearchResult` with content or error (never raise exceptions)
- Track execution time via `time.monotonic()`

## Depth Levels

Each `Depth` enum value defines output token limits and request timeouts:

```python
Depth.QUICK    → 4096 tokens, 60s timeout, single API call
Depth.STANDARD → 8192 tokens, 180s timeout, 3-call refinement chain
Depth.DEEP     → 16384 tokens, 600s timeout, native deep research (Perplexity/OpenAI only)
```

**Refinement chain (standard depth):**
1. Initial research query
2. Gap identification ("what are the 3 biggest unknowns?")
3. Synthesis (consolidate findings into coherent response)

This iterative approach works on all providers, even those without native deep-research APIs.

## CLI Interface

**Entry point:** `python research_runner.py [options]`

```
--topic TEXT                  Research topic (required)
--depth {quick|standard|deep} Depth level (default: standard)
--providers NAMES             Comma-separated list (default: all)
--output DIR                  Output directory (default: .research/)
```

**Example:**
```bash
python research_runner.py \
  --topic "Zero-knowledge proof implementations" \
  --depth deep \
  --providers claude,perplexity \
  --output my_research/
```

## Output Directory Structure

```
.research/
├── raw/
│   ├── claude-20260326-1407.md
│   ├── openai-20260326-1407.md
│   ├── gemini-20260326-1408.md
│   └── perplexity-20260326-1410.md
├── structured/
│   ├── claude-topic-slug.md
│   ├── openai-topic-slug.md
│   ├── gemini-topic-slug.md
│   └── perplexity-topic-slug.md
├── meta-analysis.md
└── research.yaml
```

## Manifest Schema (research.yaml)

```yaml
topic: "Your research topic"
topic_slug: "your-research-topic"
depth: "standard"
initiated: "2026-03-26T14:07:50Z"
completed: "2026-03-26T14:10:20Z"
status: "complete" | "partial" | "failed"
providers:
  claude:
    status: "success" | "failed"
    model: "claude-sonnet-4-6"
    duration_seconds: 45.3
    raw_file: "raw/claude-20260326-1407.md"
    structured_file: "structured/claude-topic-slug.md"
  openai:
    status: "success"
    model: "gpt-4o"
    duration_seconds: 52.1
    raw_file: "raw/openai-20260326-1407.md"
    structured_file: "structured/openai-topic-slug.md"
  # ... other providers
meta_analysis: "meta-analysis.md" | null
```

## Error Handling

**Provider-level errors:** Caught in `BaseProvider._safe_research()`, returned as `ResearchResult.error` strings. Phase 1 continues; the user sees "OK" or "FAILED: {reason}" per provider.

**Timeout strategy:** Each provider is wrapped in `asyncio.wait_for(timeout=depth.timeout_seconds)`. Timeouts become `ResearchResult` errors, not exceptions.

**Retryable errors:** Exponential backoff (1s, 2s, 4s) on HTTP 429, 500, 502, 503, 529 and SDK-specific rate limit exceptions. Max 3 retries.

**Non-retryable errors:** 4xx errors (auth, validation), missing API keys, malformed responses — logged and surfaced immediately.

## Dependencies

See `pyproject.toml`:

- `httpx` — async HTTP client (used by SDK retries)
- `anthropic` — Claude API
- `openai` — OpenAI API
- `google-genai` — Gemini API
- `perplexityai` — Perplexity API
- `python-dotenv` — load `.env` files
- `pyyaml` — manifest serialisation

## Configuration

**Environment variables** (in `~/.env` or project `.env`):

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
GOOGLE_AI_API_KEY=AI...
PERPLEXITY_API_KEY=pplx-...
```

Missing keys are detected at runtime; providers are skipped silently. At least one key is required to run research.

**Virtual environment:** Created by `./setup` script using `uv`. Stored in `.venv/`.
