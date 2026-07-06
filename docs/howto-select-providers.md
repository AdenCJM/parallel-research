# How to Run Research with Specific Providers

Run research using only the providers you want, such as testing one model or avoiding high-cost APIs.

## Why Select Specific Providers?

- **Cost control:** Some models (e.g., OpenAI's o3-deep-research) are expensive; test with Claude first
- **Availability:** If one API is down, run the others
- **Testing:** Isolate one provider's behavior to debug issues
- **Speed:** Fewer providers = faster research

## Prerequisites

- API keys for your chosen providers in `~/.env`
- Virtual environment activated (see [Getting Started](tutorial-getting-started.md))

## Steps

### 1. Run Research with Claude Only

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Your research topic" \
  --providers claude
```

Expected output:
```
Researching: Your research topic
Depth: standard | Providers: claude
  claude: OK (45.3s)

Results written to .research/
```

### 2. Run Research with Multiple Specific Providers

Comma-separated list (no spaces):

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Quantum computing milestones" \
  --providers claude,perplexity
```

Expected output:
```
Researching: Quantum computing milestones
Depth: standard | Providers: claude, perplexity
  claude: OK (42.5s)
  perplexity: OK (38.9s)

Results written to .research/
```

### 3. Skip a Single Provider

Run all providers except one by using a subset:

```bash
# Run all except Gemini (which is down)
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Your topic" \
  --providers claude,openai,perplexity
```

## Provider Options

Valid provider names (case-sensitive, lowercase):

| Provider | Use Case | Notes |
|----------|----------|-------|
| `claude` | Balanced, reasoning-heavy research | Best for nuanced topics |
| `openai` | Web search, current events (via ChatGPT search) | Good for recent news |
| `gemini` | Multi-modal capable, Google knowledge | Good for general topics |
| `perplexity` | Real-time web search, citations | Best for recent developments |

## Verification

Check the manifest to see which providers ran:

```bash
cat .research/research.yaml | grep -A 5 "providers:"
```

Expected output:
```yaml
providers:
  claude:
    status: success
    raw_file: raw/claude-20260326-1407.md
  perplexity:
    status: success
    raw_file: raw/perplexity-20260326-1410.md
  openai:
    WARNING: missing API key, skipped
  gemini:
    WARNING: missing API key, skipped
```

## Common Patterns

### Test One Provider Before Full Research

```bash
# Quick test with Claude
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Will neural networks ever explain their decisions?" \
  --depth quick \
  --providers claude
```

If successful, run full research with all providers:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Will neural networks ever explain their decisions?" \
  --depth standard
```

### Use Cheap Providers for Initial Research

Claude and Gemini are generally cheaper than OpenAI's deep research and Perplexity's sonar-deep-research. Use them first:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Your expensive research topic" \
  --providers claude,gemini \
  --depth standard
```

Then, if you need deeper insight, add the expensive providers:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Your expensive research topic" \
  --providers openai,perplexity \
  --depth deep
```

### Compare Two Models

Run separately with `--meta` to get a comparison:

```bash
# First run: Claude only
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "How to scale machine learning" \
  --providers claude \
  --output .research_claude

# Second run: Perplexity only
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "How to scale machine learning" \
  --providers perplexity \
  --output .research_perplexity

# Manually compare structured files:
diff .research_claude/structured/*.md .research_perplexity/structured/*.md
```

## Troubleshooting

**Error: "Unknown provider 'xyzprovider'"**

Check spelling (case-sensitive):

```bash
# Valid names:
--providers claude,openai,gemini,perplexity
```

**Error: "No providers available"**

None of your selected providers have API keys set:

```bash
# Check which providers have keys
cat ~/.env | grep API_KEY

# Add missing keys to ~/.env
echo "OPENAI_API_KEY=sk-proj-..." >> ~/.env
```

**Output has mixed success/failure**

Some providers succeeded, others failed. Check the manifest:

```bash
cat .research/research.yaml
```

Failed providers will have:
```yaml
  gemini:
    status: failed
    error: "RateLimitError: Rate limit exceeded after 3 retries"
```

Retry just that provider later, or proceed with the successful ones.

## Next Steps

- [Run deep research](howto-deep-research.md) for comprehensive findings
- [Set up meta-analysis](howto-meta-analysis.md) to compare outputs
- [Understand output format](reference-output-format.md)
