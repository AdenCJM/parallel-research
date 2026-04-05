# Parallel Research — Multi-LLM Deep Research Skill

Run multiple LLMs in parallel on a research topic. Output lands in `.research/` as structured markdown files — one per model, plus an optional meta-analysis.

## Trigger

`/research`: invoke this skill when the user runs `/research` or asks to "research" a topic using multiple LLMs.

## Usage

```
/research "Your research topic here"
/research --depth deep --providers claude,perplexity "Your topic"
/research --meta "Your topic"          # Fetch + meta-analysis
/research --meta                       # Meta-analysis on existing .research/
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| topic | (required) | The research topic, a question or phrase |
| `--depth` | `standard` | `quick` (single call, <1 min), `standard` (3-call refinement, <3 min), `deep` (native deep research where available, <10 min) |
| `--providers` | all available | Comma-separated: `claude,openai,gemini,perplexity` |
| `--meta` | off | Run cross-model meta-analysis |

## Execution

### First-Run Setup

Before running research, check if the skill's virtual environment exists:

1. Check if `~/.claude/skills/parallel-research/.venv/` exists
2. If NOT, run: `cd ~/.claude/skills/parallel-research && ./setup`
3. Verify the setup completed without errors
4. Continue to Phase 1

### Phase 1 — Parallel Fetch (Python)

Run the research runner script:

```bash
cd ~/.claude/skills/parallel-research && .venv/bin/python research_runner.py \
  --topic "{topic}" \
  --depth {depth} \
  --providers {providers} \
  --output "{project_directory}/.research"
```

Where `{project_directory}` is the user's current working directory.

Tell the user which providers are running and at what depth. If a provider fails or is skipped (missing API key), report it but continue.

After Phase 1 completes, read `.research/research.yaml` to see which providers succeeded.

### Phase 2 — Structure Raw Output

For each provider with `status: success` in `research.yaml`:

1. Read the raw file from `.research/raw/{provider}-{timestamp}.md`
2. Using your own reasoning, extract and organise the content into this template:

```markdown
---
provider: {provider_name}
model: {model_used}
topic: "{original_topic}"
topic_slug: {slug}
depth: {depth}
timestamp: {timestamp}
source_file: {raw_file_path}
---

## Summary
[2-3 paragraph synthesis of the provider's findings]

## Key Findings
- [Finding 1 — with specifics, numbers, or named sources where available]
- [Finding 2]
- ...

## Sources & References
- [Source 1 — URL or citation if provided by the model]
- ...

## Unique Insights
[Anything this provider surfaced that others may not — different framing, niche sources, contrarian takes]

## Limitations
[What this provider couldn't answer, hedged on, or likely hallucinated]
```

3. Write to `.research/structured/{provider}-{topic_slug}.md`
4. Update `research.yaml` — set `structured_file` for this provider

Skip providers that failed in Phase 1.

### Phase 3 — Meta-Analysis (only when `--meta` is used)

Read all files in `.research/structured/`. Cross-reference claims across providers:

1. **Agreements** — Claims made by 2+ providers (high confidence)
2. **Contradictions** — Providers that disagree on a fact or framing
3. **Unique insights** — Findings from only one provider
4. **Confidence scoring** — High (3-4 agree), Medium (2 agree), Low (1 only)

Write to `.research/meta-analysis.md` in this format:

```markdown
---
topic: "{topic}"
providers_analysed: [claude, openai, gemini, perplexity]
timestamp: {timestamp}
---

## High-Confidence Findings
[Claims supported by 3-4 providers]

## Medium-Confidence Findings
[Claims supported by 2 providers]

## Contradictions
[Where providers disagree — state both positions and which providers hold each]

## Unique Insights
[Findings from only one provider — potentially valuable but unverified]

## Recommended Follow-Up
[Questions that remain unanswered or need human verification]
```

Update `research.yaml` — set `meta_analysis` to the file path.

### Completion

Tell the user:
- How many providers succeeded vs failed
- Where the output files are (`.research/structured/`)
- If meta-analysis was generated
- That they can reference these files as context for subsequent work

## Output Structure

```
.research/
├── raw/                     # Phase 1: raw API responses
├── structured/              # Phase 2: Claude Code processed outputs
├── meta-analysis.md         # Phase 3: cross-model synthesis (when --meta)
└── research.yaml            # Manifest tracking all files and status
```

## Required API Keys

Set in `~/.env` (or project `.env`):

```
ANTHROPIC_API_KEY      # Claude
OPENAI_API_KEY         # OpenAI
GOOGLE_AI_API_KEY      # Gemini
PERPLEXITY_API_KEY     # Perplexity
```

Providers with missing keys are skipped automatically — at least one key is required.
