# How to Run Deep Research

Run research with maximum depth for the most comprehensive results. Deep research uses native deep-research APIs for Perplexity and OpenAI, and iterative refinement for Claude and Gemini.

## Why Deep Research?

- **Best for complex topics** that need multiple angles (e.g., emerging technologies, policy analysis)
- **Best for generating comparison papers** (compare 4 models on the same hard question)
- **Uses more tokens** (16K vs 8K) and time (up to 10 minutes vs 3 minutes)
- **Costs more** (especially OpenAI's o3-deep-research and Perplexity's sonar-deep-research)

## When to Use Each Depth

| Depth | Time | Tokens | Cost | Use Case |
|-------|------|--------|------|----------|
| **quick** | <1 min | 4K | Low | "What's the current definition of X?" |
| **standard** | 3 min | 8K | Medium | "Explain how X works" |
| **deep** | 10 min | 16K | High | "Compare approaches to X" or "Forecast implications of X" |

## Prerequisites

- API keys for at least one provider in `~/.env`
- Virtual environment activated
- 10+ minutes available (deep research is slow)
- Budget awareness (deep research costs more)

## Steps

### 1. Run Deep Research with All Providers

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "How will quantum computing disrupt cryptography in the next 5 years?" \
  --depth deep
```

Expected output:
```
Researching: How will quantum computing disrupt cryptography in the next 5 years?
Depth: deep | Providers: claude, openai, gemini, perplexity
  claude: OK (124.5s)     # Falls back to standard (iterative)
  openai: OK (287.3s)     # Uses native o3-deep-research
  gemini: OK (118.2s)     # Falls back to standard (iterative)
  perplexity: OK (312.8s) # Uses native sonar-deep-research

Results written to .research/
```

### 2. Run Deep Research with Fast Providers Only

OpenAI's o3-deep-research and Perplexity's sonar-deep-research take longer but deliver richer results:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Economic impact of AI automation on labor markets" \
  --depth deep \
  --providers openai,perplexity
```

This takes ~6 minutes total (OpenAI + Perplexity run in parallel) vs 12+ minutes for all providers.

### 3. Run Standard Research If Deep Is Too Slow

If you're on a slow connection or want results faster, use standard depth:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Your topic" \
  --depth standard
```

This gives 80% of deep research's quality in 30% of the time.

## Understanding Deep Research Behavior

### What Deep Research Does (Per Provider)

**Perplexity (sonar-deep-research):**
- Uses native deep-research endpoint
- Iterates internally on search queries
- Returns multiple perspectives with high citation density
- ~5 minutes per research

**OpenAI (o3-deep-research, Responses API):**
- Uses native deep-research endpoint
- Reasons through the problem in detail
- Outputs structured thinking patterns
- ~5 minutes per research

**Claude (falls back to standard):**
- No native deep-research API in Anthropic SDK (as of March 2026)
- Falls back to 3-call refinement chain
- Call 1: Initial research
- Call 2: Identify gaps ("What are the 3 biggest unknowns?")
- Call 3: Synthesize findings
- ~2 minutes per research

**Gemini (falls back to standard):**
- Same as Claude (no native deep-research API)
- 3-call refinement chain
- ~2 minutes per research

### Comparing Deep vs Standard Output

Raw output comparison:

```bash
# Run the same topic at both depths (in separate directories)
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Zero-knowledge proof use cases" \
  --depth standard \
  --output .research_standard

~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Zero-knowledge proof use cases" \
  --depth deep \
  --output .research_deep

# Compare file sizes
wc -l .research_standard/raw/*.md .research_deep/raw/*.md
```

Deep research files are typically 2-3x larger (more findings, more citations).

## Cost Estimation

Rough cost breakdown (as of March 2026):

| Scenario | Providers | Time | Est. Cost |
|----------|-----------|------|-----------|
| Quick (quick depth) | All 4 | <1 min | ~$0.02 |
| Standard (standard depth) | All 4 | 3 min | ~$0.10 |
| Deep (deep depth, all providers) | All 4 | 12 min | ~$0.30-1.00 |
| Deep (OpenAI + Perplexity only) | 2 | 6 min | ~$0.20-0.50 |
| Deep (Claude + Gemini only) | 2 | 4 min | ~$0.05 |

**Note:** Costs are estimates based on token usage and provider pricing. Check your provider dashboards for actual costs.

## Verification

Check execution times in the manifest:

```bash
cat .research/research.yaml | grep duration_seconds
```

Expected output (deep research is slower):
```
    duration_seconds: 124.5  # Claude
    duration_seconds: 287.3  # OpenAI (slowest)
    duration_seconds: 118.2  # Gemini
    duration_seconds: 312.8  # Perplexity (slowest)
```

## Troubleshooting

**Error: "Timeout after 600s"**

Deep research hit the timeout limit (600 seconds / 10 minutes):

```bash
# Retry with standard depth
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Your topic" \
  --depth standard
```

Or run specific providers only (some may be faster):

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Your topic" \
  --depth deep \
  --providers claude,gemini  # Faster fallback
```

**Research took too long, check if costs are high**

Review your API usage dashboard:
- **OpenAI:** https://platform.openai.com/account/usage/overview
- **Anthropic:** https://console.anthropic.com
- **Google AI:** https://aistudio.google.com/app/apikey
- **Perplexity:** https://www.perplexity.ai/settings/account

If costs are higher than expected, stick to standard depth for future research.

**One provider times out, others succeed**

Check manifest for mixed status:

```bash
cat .research/research.yaml
```

The successful providers' output is still valid. You can:
1. Retry just the slow provider later
2. Proceed with the successful ones (3 providers is still useful)
3. Remove the slow provider from future runs (`--providers` without it)

## Next Steps

- [Set up meta-analysis](howto-meta-analysis.md) to synthesize deep findings
- [Structure your research](howto-structure-research.md) using Claude Code
- [Read the architecture guide](reference-architecture.md) to understand depth levels
