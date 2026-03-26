# Parallel Research

One command. Four LLMs. Structured output that lives in your project.

Parallel Research is a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that runs Claude, OpenAI, Gemini, and Perplexity on the same research topic simultaneously. Each model's response lands as its own structured markdown file in `.research/`, ready to be queried, compared, or fed as context to your next build.

Different models surface different sources and framings. Running them in parallel isn't about redundancy; it's about coverage.

```
/research "How do blockchain gaming economies handle inflation?"
```

```
.research/
├── raw/                          # Raw API responses
├── structured/                   # Processed, structured output per model
│   ├── claude-how-do-blockchain-gaming-economies-handle-inflation.md
│   ├── openai-how-do-blockchain-gaming-economies-handle-inflation.md
│   ├── gemini-how-do-blockchain-gaming-economies-handle-inflation.md
│   └── perplexity-how-do-blockchain-gaming-economies-handle-inflation.md
├── meta-analysis.md              # Cross-model synthesis (opt-in)
└── research.yaml                 # Manifest
```

## Why

**"I can just use ChatGPT / Perplexity deep research directly."**

You can. But you'll get one model's perspective, shaped by its training data and retrieval biases. Ask Perplexity and Claude the same question and you'll get different sources, different emphasis, and sometimes flat-out contradictory claims. That's the point. A single model gives you an answer. Multiple models give you a map of where the answers agree and where they don't.

**"Won't they just say the same thing?"**

Sometimes. When three out of four models independently arrive at the same conclusion, that's a high-confidence signal. When only one model surfaces a finding, you know to treat it with more scepticism. The meta-analysis makes this explicit. Without it, you'd never know what you were missing.

**"Running four LLMs sounds expensive."**

A `quick` depth run across all four providers costs a few cents. `standard` is under a dollar. `deep` can run a few dollars when using OpenAI's o3-deep-research or Perplexity's sonar-deep-research, but you're getting the equivalent of hours of manual research in minutes. You can also run just the providers you want with `--providers`.

**"I can research manually and paste it into my project."**

You can, but the output won't be structured or consistent. The real value here isn't saving you a browser tab. It's that the output is designed for Claude Code to consume as build context. Each file follows the same template with frontmatter metadata, so when you start building, Claude Code already has categorised, attributable research loaded. No copy-pasting, no reformatting, no "here's what I found" preamble.

**"Why not just one merged report?"**

Because you lose the ability to interrogate each model separately. Maybe Perplexity found a niche source you want to dig into. Maybe Claude's framing of the problem is better than OpenAI's. Separate files let you feed specific perspectives to Claude Code, compare directly, or throw out the one that hallucinated. A merged report hides all of that.

## Install

Clone directly into your Claude Code skills directory:

```bash
git clone git@github.com:AdenCJM/parallel-research.git ~/.claude/skills/parallel-research
```

Or if you're developing locally:

```bash
git clone git@github.com:AdenCJM/parallel-research.git ~/Projects/ParallelResearch
ln -sf ~/Projects/ParallelResearch ~/.claude/skills/parallel-research
```

Setup runs automatically on first use. If you want to run it manually:

```bash
cd ~/.claude/skills/parallel-research && ./setup
```

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). The setup script handles the virtual environment and all dependencies.

## API Keys

Add whichever providers you want to use to your `~/.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
GOOGLE_AI_API_KEY=AI...
PERPLEXITY_API_KEY=pplx-...
```

You don't need all four. Any provider with a missing key is skipped automatically. At least one is required.

## Usage

From any project in Claude Code:

```
/research "Your topic here"
```

### Depth

Controls how hard each model works.

| Depth | What happens | Time |
|-------|-------------|------|
| `quick` | Single API call per model | < 1 min |
| `standard` | Three-call refinement chain (research, identify gaps, synthesise) | < 3 min |
| `deep` | Native deep research for Perplexity and OpenAI; falls back to standard for Claude and Gemini | < 10 min |

```
/research --depth deep "Zero-knowledge proof implementations for gaming"
```

### Pick your models

```
/research --providers claude,perplexity "Your topic"
```

### Meta-analysis

Cross-references all providers' outputs and scores each claim by confidence (how many models agree).

```
/research --meta "Your topic"           # Fetch + meta-analysis in one go
/research --meta                        # Run meta-analysis on existing .research/
```

The meta-analysis flags agreements, contradictions, unique insights, and questions that none of the models could answer well.

## How it works

Three phases, run in sequence:

**Phase 1** (Python, parallel) hits all selected providers concurrently via `asyncio`. Each response is written to `.research/raw/` as markdown with YAML frontmatter. A `research.yaml` manifest tracks status, timings, and file paths. If a provider fails or times out, the others still complete.

**Phase 2** (Claude Code) reads each raw file and structures it into a consistent template: summary, key findings, sources, unique insights, and limitations. Output goes to `.research/structured/`.

**Phase 3** (Claude Code, opt-in) reads all structured files and cross-references claims across providers.

## Provider details

| Provider | Package | Deep research | Notes |
|----------|---------|:---:|-------|
| Perplexity | `perplexityai` | Native | `sonar-deep-research` for deep, `sonar-pro` otherwise |
| OpenAI | `openai` | Native | `o3-deep-research` via Responses API for deep, `gpt-4o` otherwise |
| Claude | `anthropic` | Fallback | `claude-sonnet-4-6`; deep falls back to standard |
| Gemini | `google-genai` | Fallback | `gemini-2.5-pro`; deep falls back to standard |

All providers use exponential backoff (1s, 2s, 4s) with max 3 retries on rate limits and server errors.

## Output format

Each structured file follows the same template:

```yaml
---
provider: perplexity
model: sonar-pro
topic: "How do blockchain gaming economies handle inflation?"
topic_slug: how-do-blockchain-gaming-economies-handle-inflation
depth: standard
timestamp: 2026-03-26T14:07:50Z
source_file: raw/perplexity-20260326-1407.md
---
```

Sections: **Summary**, **Key Findings**, **Sources & References**, **Unique Insights**, **Limitations**.

The `research.yaml` manifest tracks everything: which providers ran, which succeeded, durations, file paths, and whether meta-analysis has been generated.

## Project structure

```
├── research_runner.py       # asyncio orchestrator and CLI
├── providers/
│   ├── base.py              # BaseProvider ABC, ResearchResult, retry logic
│   ├── claude.py            # Anthropic Claude
│   ├── openai_provider.py   # OpenAI (chat completions + Responses API)
│   ├── gemini.py            # Google Gemini
│   └── perplexity.py        # Perplexity
├── SKILL.md                 # Claude Code skill instructions
├── pyproject.toml           # Dependencies
└── setup                    # First-run venv + install script
```

## Development

```bash
cd ~/Projects/ParallelResearch
./setup
source .venv/bin/activate

# Test the CLI directly (needs at least one API key in ~/.env)
python research_runner.py --topic "test topic" --depth quick --output .research/
```

## Licence

MIT
