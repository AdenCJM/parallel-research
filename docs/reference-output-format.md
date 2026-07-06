# Output Format Reference

## Overview

Parallel Research produces three types of files in the `.research/` directory: raw responses, structured markdown, and a manifest.

```
.research/
├── raw/                    # Phase 1 output (raw API responses)
├── structured/             # Phase 2 output (processed markdown)
├── meta-analysis.md        # Phase 3 output (optional, cross-reference synthesis)
└── research.yaml           # Manifest (all phases)
```

## Raw Files

**Location:** `.research/raw/{provider}-{timestamp}.md`

**Naming:** `{provider}-YYYYMMDD-HHMM.md` (e.g., `claude-20260326-1407.md`)

**Format:** Markdown with YAML frontmatter.

**Example:**

```yaml
---
provider: claude
model: claude-sonnet-4-6
topic: "How do blockchain gaming economies handle inflation?"
timestamp: 2026-03-26T14:07:50Z
duration_seconds: 45.3
---

# Research Results

Here is the raw API response...

## Key Findings

1. ...
2. ...
```

### Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `provider` | string | Provider name (e.g., "claude", "openai") |
| `model` | string | Model identifier (e.g., "claude-sonnet-4-6") |
| `topic` | string | The original research topic |
| `timestamp` | ISO 8601 | When the request was made (UTC) |
| `duration_seconds` | number | Wall-clock execution time |
| `error` | string (optional) | Error message if request failed |

### Content

Raw API response as returned by the provider. May include:
- Markdown headers and formatting
- Bullet lists and numbered lists
- Code blocks
- Tables (if provider supports)
- Inline URLs and citations

**Note:** Raw files are unstructured and provider-specific. Phase 2 processes these into a consistent template.

## Structured Files

**Location:** `.research/structured/{provider}-{topic_slug}.md`

**Naming:** `{provider}-{topic_slug}.md`  
Example: `claude-blockchain-gaming-inflation.md`

**Topic slug generation:**
- Lowercase
- Spaces → hyphens
- Remove non-alphanumeric (except hyphens)
- Collapse consecutive hyphens
- Truncate at 60 characters

**Format:** Markdown with YAML frontmatter (consistent across all providers).

**Example:**

```yaml
---
provider: claude
model: claude-sonnet-4-6
topic: "How do blockchain gaming economies handle inflation?"
topic_slug: how-do-blockchain-gaming-economies-handle-inflation
depth: standard
timestamp: 2026-03-26T14:07:50Z
source_file: raw/claude-20260326-1407.md
---

## Summary

[2-3 paragraph synthesis of key findings]

## Key Findings

- **Finding 1:** Specific claim with numbers or sources
- **Finding 2:** Another finding
- ...

## Sources & References

- [Source name](https://url.example.com)
- [Named paper or report](citation)

## Unique Insights

[Anything this provider surfaced that others may not — niche sources, contrarian takes, different framing]

## Limitations

[What this provider couldn't answer well, hedged on, or likely hallucinated]
```

### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|:---:|----------|
| `provider` | string | Yes | Provider name (matches raw file) |
| `model` | string | Yes | Model used |
| `topic` | string | Yes | Original research topic |
| `topic_slug` | string | Yes | URL-safe version of topic |
| `depth` | string | Yes | Depth level used (quick/standard/deep) |
| `timestamp` | ISO 8601 | Yes | When Phase 1 was run |
| `source_file` | string | Yes | Path to raw file (relative to `.research/`) |

### Content Sections

**Summary** (2-3 paragraphs)
Concise overview of the provider's findings. Should be readable standalone.

**Key Findings** (bullet list)
Specific claims with numbers, names, dates, or sources where available. Each bullet should be self-contained and verifiable.

**Sources & References** (bullet list)
URLs, citations, paper names. Used in meta-analysis for attribution.

**Unique Insights** (prose)
Findings unique to this provider. Alerts meta-analysis to valuable but unverified claims.

**Limitations** (prose)
What the provider couldn't answer, hedged on, or likely hallucinated. Transparency about reliability.

## Manifest File

**Location:** `.research/research.yaml`

**Updated by:** Phase 1 (initial creation), Phase 2 (adds structured file paths), Phase 3 (adds meta-analysis path)

**Format:** YAML dictionary.

**Example:**

```yaml
topic: "How do blockchain gaming economies handle inflation?"
topic_slug: how-do-blockchain-gaming-economies-handle-inflation
depth: standard
initiated: 2026-03-26T14:07:50Z
completed: 2026-03-26T14:10:20Z
status: complete
providers:
  claude:
    status: success
    model: claude-sonnet-4-6
    duration_seconds: 45.3
    raw_file: raw/claude-20260326-1407.md
    structured_file: structured/claude-blockchain-gaming-inflation.md
  openai:
    status: success
    model: gpt-4o
    duration_seconds: 52.1
    raw_file: raw/openai-20260326-1407.md
    structured_file: structured/openai-blockchain-gaming-inflation.md
  gemini:
    status: failed
    error: "RateLimitError: Rate limit exceeded after 3 retries"
    raw_file: raw/gemini-20260326-1408.md
    structured_file: null
  perplexity:
    status: success
    model: sonar-pro
    duration_seconds: 38.9
    raw_file: raw/perplexity-20260326-1410.md
    structured_file: structured/perplexity-blockchain-gaming-inflation.md
meta_analysis: meta-analysis.md
```

### Root Fields

| Field | Type | Description |
|-------|------|-------------|
| `topic` | string | Original research topic |
| `topic_slug` | string | URL-safe slug for filenames |
| `depth` | string | Depth level (quick/standard/deep) |
| `initiated` | ISO 8601 | When Phase 1 started |
| `completed` | ISO 8601 | When Phase 1 finished |
| `status` | string | "complete" (all succeeded), "partial" (some succeeded), "failed" (none) |
| `providers` | dict | Per-provider status and file paths |
| `meta_analysis` | string \| null | Path to meta-analysis file (null if not generated) |

### Provider Entry Fields

Each provider key (e.g., `claude`, `openai`) has:

| Field | Type | Set When | Description |
|-------|------|----------|----------|
| `status` | string | Always | "success" or "failed" |
| `model` | string | Success only | Model identifier actually used |
| `duration_seconds` | number | Success only | Execution time |
| `error` | string | Failed only | Error reason (why it failed) |
| `raw_file` | string | Always | Path to raw file (Phase 1) |
| `structured_file` | string \| null | Phase 2+ | Path to structured file (null initially) |

## Meta-Analysis File

**Location:** `.research/meta-analysis.md`

**Generated by:** Phase 3 (only when `--meta` flag is used)

**Format:** Markdown (no frontmatter).

**Example:**

```markdown
# Meta-Analysis: How do blockchain gaming economies handle inflation?

Analysed 4 providers on 2026-03-26. Confidence scoring based on agreement:
- **High**: 3-4 providers agree
- **Medium**: 2 providers agree
- **Low**: 1 provider only

## High-Confidence Findings

- **Claim 1:** All providers agree on this finding with specifics
  - Claude: [detail]
  - OpenAI: [detail]
  - Perplexity: [detail]

- **Claim 2:** Another widely-agreed finding
  - ...

## Medium-Confidence Findings

- **Claim X:** Supported by Claude and OpenAI but not others
  - Claude: [source/detail]
  - OpenAI: [source/detail]
  - Gemini: (no mention)
  - Perplexity: (no mention)

## Contradictions

- **Claim:** Inflation control mechanisms
  - Claude: "Most games use dynamic mint caps"
  - Perplexity: "Token burns are primary deflationary mechanism"
  - OpenAI: "Combination of both"
  - Gemini: "Market-based sinks are underutilised"

## Unique Insights

- **Perplexity only:** Named specific Axie Infinity mechanism not mentioned by others
- **Claude only:** Historical comparison to macroeconomic policy theory

## Recommended Follow-Up

- Verify the Axie mechanism claim (low confidence, sourced from Perplexity only)
- Compare token-sink approaches across top 5 blockchain games
- Look deeper into "dynamic mint caps" — unclear if this is a standard pattern or one-off design
```

### Sections

**High-Confidence Findings** (bulleted list)
Claims supported by 3-4 providers. These are the strongest signals.

**Medium-Confidence Findings** (bulleted list)
Claims supported by 2 providers. Useful but warrant verification.

**Contradictions** (structured blocks)
Where providers disagree. Format: claim, then per-provider stance.

**Unique Insights** (bulleted list)
Single-provider findings that are potentially valuable but unverified.

**Recommended Follow-Up** (bulleted list)
Questions that remain, claims that need human verification, gaps to research further.

## File Lifecycle

```
Phase 1 (CLI)          Phase 2 (Claude Code)      Phase 3 (Claude Code)
┌──────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ Raw files    │  ─→   │ Structured files │  ─→   │ Meta-analysis    │
│ Manifest     │       │ Update manifest  │       │ Update manifest  │
└──────────────┘       └──────────────────┘       └──────────────────┘

Idempotent:
- Re-running Phase 1 overwrites raw files and manifest
- Re-running Phase 2 overwrites structured files only
- Re-running Phase 3 overwrites meta-analysis only
```

## Querying the Output

**Using Bash:**

```bash
# Find all structured files for a topic
ls .research/structured/*blockchain-gaming*.md

# Extract all sources from a structured file
grep -A 10 "^## Sources" .research/structured/claude-*.md

# Count findings per provider
for f in .research/structured/*.md; do
  provider=$(basename $f | cut -d- -f1)
  findings=$(grep -c "^- " $f)
  echo "$provider: $findings findings"
done
```

**Using Claude Code:**

Structured files are designed for Claude Code to consume as context. Frontmatter metadata enables filtering and provenance tracking. Example Claude Code usage:

```python
import yaml
from pathlib import Path

# Read all structured files for a topic
research_dir = Path(".research/structured")
files = list(research_dir.glob("*-my-topic*.md"))

for file in files:
    with open(file) as f:
        # Parse frontmatter
        content = f.read()
        frontmatter_text = content.split("---")[1]
        metadata = yaml.safe_load(frontmatter_text)
        print(f"{metadata['provider']} ({metadata['model']})")
        # Process markdown sections...
```
