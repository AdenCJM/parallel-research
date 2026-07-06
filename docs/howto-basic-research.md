# How to Run Basic Research

Run your first research query using all available providers.

## Prerequisites

- Python 3.11 or later installed
- At least one LLM API key (Claude, OpenAI, Gemini, or Perplexity)
- `.venv/` virtual environment set up (see [Getting Started](tutorial-getting-started.md))

## Steps

### 1. Check API Key Availability

```bash
cd ~/.claude/skills/parallel-research
source .venv/bin/activate
```

Verify your API keys are in `~/.env`:

```bash
cat ~/.env | grep -E 'ANTHROPIC_API_KEY|OPENAI_API_KEY|GOOGLE_AI_API_KEY|PERPLEXITY_API_KEY'
```

Expected output (at least one present):
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
```

If missing, add them now:

```bash
echo "ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE" >> ~/.env
```

### 2. Run a Quick Research

Navigate to your project directory:

```bash
cd ~/my-project
```

Run a quick research (under 1 minute, single API call per provider):

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "What are the latest developments in quantum computing?" \
  --depth quick
```

Expected output:
```
Researching: What are the latest developments in quantum computing?
Depth: quick | Providers: claude, openai, gemini, perplexity
  claude: OK (23.1s)
  openai: OK (18.4s)
  gemini: FAILED: RateLimitError: Rate limit exceeded (5.2s)
  perplexity: OK (31.5s)

Results written to .research/
```

### 3. Check the Output

List all files generated:

```bash
ls -lah .research/
```

You'll see:
- `.research/raw/` — raw API responses
- `.research/research.yaml` — manifest
- No structured files yet (that's Phase 2, manual)

Inspect the manifest:

```bash
cat .research/research.yaml
```

Look for provider status and file paths:
```yaml
status: partial          # Some providers succeeded
providers:
  claude:
    status: success
    model: claude-sonnet-4-6
    duration_seconds: 23.1
    raw_file: raw/claude-20260326-1407.md
```

### 4. Read Raw Output

View Claude's raw response:

```bash
cat .research/raw/claude-*.md
```

Or open in your editor:

```bash
open .research/raw/claude-*.md  # macOS
code .research/raw/claude-*.md  # VS Code
```

## Verification

You'll know it worked if:
- ✅ `.research/` directory exists
- ✅ `research.yaml` lists at least one provider with `status: success`
- ✅ At least one raw file in `.research/raw/` contains research content (not errors)
- ✅ Execution times are logged per provider

## Troubleshooting

**Error: "No providers available. Check your API keys"**

```bash
# Verify at least one API key is set
env | grep -i api_key
```

Add a key to `~/.env` and try again.

**Error: "ModuleNotFoundError: No module named 'providers'"**

```bash
# Ensure you're in the correct directory
cd ~/.claude/skills/parallel-research
source .venv/bin/activate
```

Or use the full path:
```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Your topic" --depth quick
```

**All providers return "FAILED"**

Check network connectivity and API key validity:

```bash
# Test Claude API (if key is set)
python -c "from anthropic import Anthropic; print('Claude OK')"

# Test OpenAI API
python -c "from openai import OpenAI; print('OpenAI OK')"
```

If an import fails, reinstall dependencies:

```bash
cd ~/.claude/skills/parallel-research
./setup
```

**One provider times out (takes > 60s)**

It may be rate-limited or under heavy load. Retry with `--depth quick` or increase the timeout:

```bash
# Deeper research with more time
python research_runner.py \
  --topic "Your topic" \
  --depth standard  # Allows 180s per provider
```

## Next Steps

- [Run standard research](howto-standard-research.md) for deeper results
- [Use specific providers](howto-select-providers.md) to test one model
- [Set up meta-analysis](howto-meta-analysis.md) to compare provider outputs
- [Read the output format guide](reference-output-format.md) to understand the files
