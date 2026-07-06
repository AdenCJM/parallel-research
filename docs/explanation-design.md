# Design Rationale

## Why Parallel, Not Sequential?

**Problem:** Running research on one LLM at a time means waiting for each response before starting the next. With four providers, and each taking 30-100 seconds, sequential queries take 4-6 minutes total.

**Our approach:** Run all providers concurrently via `asyncio.gather()`. Wall-clock time = the slowest provider, not the sum.

**Trade-off:** Requires async/await throughout the codebase (more complex than synchronous code), but net result: 3-5x faster research for the same total API cost.

## Why Three Phases?

**Problem:** Raw API responses are unstructured, provider-specific, and inconsistent. Comparing Claude's response to Perplexity's requires mental parsing.

**Our approach:**
- **Phase 1 (Python):** Fetch all responses in parallel. Fast, reliable, focused.
- **Phase 2 (Claude Code):** Humans (via Claude Code UI) structure the raw output into a consistent template. Better quality than programmatic extraction (humans catch nuance).
- **Phase 3 (Optional):** Cross-reference claims, identify contradictions, score confidence.

**Trade-off:** Phase 2 requires manual Claude Code intervention (can't fully automate). But the result is high-quality structured docs that live in the project as a permanent artifact.

## Why Separate Files per Provider?

**Problem:** Merging all responses into a single report hides which model said what. If one provider hallucinates, you can't trace it back. If you want to dig deeper into Perplexity's sources but not Claude's, you can't isolate them.

**Our approach:** One structured file per provider per topic. Each file includes metadata (model, timestamp, source) and a "Unique Insights" section for provider-specific findings.

**Benefits:**
- Traceability: every claim has a source provider
- Selectivity: feed specific perspectives to Claude Code
- Comparison: read Claude's take, then Perplexity's, side-by-side
- Auditing: re-run one provider to test changes without re-fetching others

**Trade-off:** More files to manage, but meta-analysis ties them together.

## Why YAML Frontmatter?

**Problem:** Metadata (provider, model, timestamp) needs to be machine-readable for Claude Code to filter and track.

**Our approach:** YAML frontmatter in every markdown file.

**Benefits:**
- Parseable by `yaml.safe_load()` in Python and simple regex in shells
- Preserved by Claude Code when editing
- Renders as a table in markdown viewers (minor visual benefit)
- Extensible: add new fields without breaking existing parsers

**Trade-off:** Adds 10 lines per file. Verbose but standardised.

## Why Exponential Backoff on Retries?

**Problem:** Rate limits (HTTP 429) are transient. Retrying immediately often fails; sleeping longer wastes time.

**Our approach:** Exponential backoff with delays [1s, 2s, 4s]. Max 3 retries.

**Why this sequence:**
- 1s: Catches tokens-per-minute limits (quick reset)
- 2s: Handles short rate-limit windows
- 4s: Fallback for longer-lasting limits
- 3 retries: Balances retry cost against success probability (9 seconds total max backoff)

**Detection:**
- HTTP status 429, 500, 502, 503, 529
- SDK-specific rate-limit exception names (e.g., "RateLimitError", "rate_limit")

**Trade-off:** Retries delay failure signals slightly, but ensure transient blips don't break the research.

## Why Deep Depth Falls Back to Standard (Claude & Gemini)

**Problem:** Perplexity and OpenAI have native "deep research" APIs that iterate internally and return richer results. Claude and Gemini don't expose equivalent APIs (as of March 2026).

**Our approach:**
- **OpenAI/Perplexity:** Use native deep-research endpoints
- **Claude/Gemini:** Fall back to 3-call refinement chain (standard depth)

**Why not multi-turn simulation for Claude/Gemini?**
- Gap detection is hard: requires the model to critique its own output and identify unknowns
- Fragile: domain-specific gap detection doesn't generalise across topics
- Cost: 6+ calls vs 3 costs more than native deep-research APIs

**Future:** v2 roadmap includes autonomous gap detection for Claude/Gemini deep mode.

## Why asyncio, Not Threads or subprocess?

**Problem:** Concurrency model choice affects code complexity, error handling, and resource usage.

**Choices:**
- **Threads:** Easy to understand but GIL limits Python CPU concurrency. Good for I/O-bound work, which this is.
- **subprocess:** Overkill for calling HTTP client libraries; adds inter-process overhead.
- **asyncio:** Purpose-built for I/O concurrency. Native in SDK libraries (Anthropic, OpenAI all use async).

**Our choice:** asyncio.

**Benefits:**
- Lightweight: thousands of concurrent tasks (doesn't matter here, but scales)
- Native integration: all provider SDKs have `Async*` variants we use
- Single-threaded: no lock contention, simpler error handling
- First-class in Python 3.11+

**Trade-off:** Requires async/await syntax; async code is less familiar to some Python developers.

## Why Timeout per Depth?

**Problem:** Requests hang unpredictably. Without timeouts, a stalled provider blocks the entire research.

**Our approach:** Set timeout based on depth:
- QUICK: 60s (single API call)
- STANDARD: 180s (three API calls)
- DEEP: 600s (deep-research API may take longer)

**Implementation:** `asyncio.wait_for()` per provider.

**Trade-off:** Timeouts are hard to calibrate. Too short = false failures. Too long = wasted time on slow providers. Current values are conservative (may need tuning per region/time).

## Why _safe_research() Wrapping?

**Problem:** Providers can fail in ways not caught by their own error handling (e.g., `asyncio.TimeoutError`, memory errors, bugs in our code).

**Our approach:** Wrap each provider's `research()` call in `_safe_research()`, which:
1. Enforces timeout
2. Catches *any* exception (including programmer bugs)
3. Returns it as `ResearchResult.error`

**Benefits:**
- Phase 1 never crashes due to one provider's failure
- Error messages are consistent and attributed

**Trade-off:** Makes debugging harder (exceptions are swallowed). Mitigated by logging error strings prominently to stdout.

## Why Manifest over Direct Polling?

**Problem:** Claude Code needs to know which providers succeeded, where the files are, what the execution times were.

**Our approach:** Write `research.yaml` after Phase 1, update it in Phases 2 and 3.

**Benefits:**
- Single source of truth (YAML file)
- Phases can re-run independently without losing prior progress
- Human-readable (can inspect manifest directly)
- Extensible (add new fields for future features)

**Trade-off:** Slight latency between file creation and manifest updates. Mitigated by Phase 1 writing manifest synchronously.

## Why Not a Webhook or Callback?

**Problem:** Long-running research (10+ minutes) means Phase 1 completes, Phase 2 is manual, Phase 3 is optional. Need a way to signal "research is ready" without polling.

**Why not webhooks?**
- Requires network ingress (user's firewall, cloud setup)
- Adds infrastructure complexity
- Webhook servers are stateful (need to track which calls to make)

**Why not callbacks?**
- Similar complexity to webhooks
- Less portable (tied to a service)

**Our choice:** Manifest polling (implicit).

**Reality:** Users run Phase 1, see output, manually do Phase 2 in Claude Code. Phase 3 is explicitly flagged with `--meta`. No automation needed yet.

## Why Output to .research/?

**Problem:** Research results need a home that doesn't clutter the project root.

**Our approach:** Dedicated `.research/` directory, similar to `.git/`, `node_modules/`, etc.

**Benefits:**
- Clear scope (everything in `.research/` is research output)
- Easy to .gitignore (add to `.gitignore`)
- Keeps project root clean
- Discoverable (standard location)

**Trade-off:** Another directory to navigate. Mitigated by symlinks or `cd .research/` usage.

## Why topic_slug in Filenames?

**Problem:** Topics are long human-readable strings. Filenames need to be valid on Windows, macOS, Linux and fit in 255 chars.

**Our approach:** Slugify topics:
1. Lowercase
2. Replace spaces with hyphens
3. Remove non-alphanumeric (except hyphens)
4. Collapse multiple hyphens
5. Truncate at 60 chars

**Example:** "How do blockchain gaming economies handle inflation?" → "how-do-blockchain-gaming-economies-handle-inflation"

**Benefits:**
- Filesystem-safe
- Readable in logs and file lists
- Deterministic (same topic always produces same slug)

**Trade-off:** Very long topics get truncated. Very similar topics might collide (unlikely in practice; addressed by timestamp in raw files).

## Why Colour-Coded Status Output?

**Problem:** Running four providers in parallel, and reporting status per provider, can be hard to scan.

**Our approach:** (Future enhancement) Colour the status line:
- Green: success
- Red: failed
- Yellow: partial (mixed success/failure)

**Rationale:** Visual scanning of output is faster than reading text. Especially useful for long research runs (600+ seconds).

## Why Not Compress on Disk?

**Problem:** Raw + structured files can total 100+ KB per research topic. Hundreds of researches = significant disk usage.

**Why not gzip or compress?**
- Claude Code consumes these files directly (adding decompression step breaks integration)
- Disk is cheap; human time is not (complexity not worth it)

**Our choice:** No compression.

**Trade-off:** Larger disk footprint. Mitigated by `.gitignore .research/` to avoid repo bloat.

## Comparison to Alternatives

### Single-Provider Deep Research (e.g., just Perplexity)

**Pros:** Fast, cheap, focused output  
**Cons:** Miss alternative perspectives; can't cross-check for hallucinations; no consensus signal

### Manual Research + Paste

**Pros:** Human filter on quality  
**Cons:** Slow (hours), fragile (manual copy-paste), loses source attribution

### Aggregate into Single Markdown File

**Pros:** Simpler (one file instead of four)  
**Cons:** Lose traceability; can't re-run one provider without re-fetching all; can't isolate one model's take

### Database (SQLite, PostgreSQL)

**Pros:** Queryable, structured data, supports full-text search  
**Cons:** Overkill for local research; requires setup; breaks portability (files are portable, DBs are tied to host)

### API Server + Web UI

**Pros:** User-friendly, discoverable  
**Cons:** Infrastructure overhead; requires hosting; solves different problem (management UI vs research tool)

**Why Parallel Research chose files:**
- Portable (lives in the project repo)
- Inspectable (cat, grep, Claude Code read)
- Version-controllable (`.gitignore` if needed, or commit if permanent)
- Composable (feed to Claude Code directly)
- Simple (no database, no server)
