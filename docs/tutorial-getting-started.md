# Getting Started with Parallel Research

Learn how to set up Parallel Research and run your first multi-LLM research query in 15 minutes.

## What You'll Do

1. Install Parallel Research as a Claude Code skill
2. Get API keys for at least one LLM provider
3. Run your first research query
4. Review the output files

By the end, you'll have structured research from up to four LLMs in `.research/` directory, ready to use in your projects.

## What You'll Need

- Python 3.11 or later (check with `python3 --version`)
- Homebrew (macOS; for installing Python if needed)
- API key(s) from at least one provider:
  - [Anthropic (Claude)](https://console.anthropic.com)
  - [OpenAI (GPT-4o)](https://platform.openai.com/account/api-keys)
  - [Google AI (Gemini)](https://aistudio.google.com)
  - [Perplexity AI](https://www.perplexity.ai/settings/account)
- 20 minutes

## Step 1: Install Parallel Research

Parallel Research is a Claude Code skill. Clone it into your skills directory:

```bash
git clone git@github.com:AdenCJM/parallel-research.git ~/.claude/skills/parallel-research
```

Or, if you don't have SSH set up:

```bash
git clone https://github.com/AdenCJM/parallel-research.git ~/.claude/skills/parallel-research
```

Verify installation:

```bash
ls -la ~/.claude/skills/parallel-research/
```

You should see: `README.md`, `SKILL.md`, `research_runner.py`, `providers/`, `setup`, etc.

## Step 2: Set Up the Virtual Environment

Run the setup script (one-time):

```bash
cd ~/.claude/skills/parallel-research && ./setup
```

This creates a Python virtual environment and installs dependencies. Takes 1-2 minutes.

Expected output:
```
Setting up Parallel Research...
Creating virtual environment...
Installing dependencies via uv...
✓ Setup complete
```

If setup fails, check:
- Python 3.11+ is installed: `python3 --version`
- `uv` is installed: `which uv` (install with `pip install uv` if missing)

## Step 3: Get API Keys

You need at least one API key. Add as many as you want to use:

### Claude (Anthropic)

1. Visit https://console.anthropic.com
2. Click "API keys" in the left sidebar
3. Click "Create key"
4. Copy the key (starts with `sk-ant-`)

### OpenAI

1. Visit https://platform.openai.com/account/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-proj-`)

### Google AI (Gemini)

1. Visit https://aistudio.google.com/app/apikey
2. Click "Create API key"
3. Copy the key (starts with `AIza`)

### Perplexity

1. Visit https://www.perplexity.ai/settings/account
2. Scroll to "API keys"
3. Click "Create key"
4. Copy the key (starts with `pplx-`)

## Step 4: Add API Keys to ~/.env

Open (or create) `~/.env`:

```bash
nano ~/.env
```

Or with your preferred editor:

```bash
open -a TextEdit ~/.env  # macOS
code ~/.env              # VS Code
```

Add your API keys (at least one):

```bash
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
GOOGLE_AI_API_KEY=AIza...
PERPLEXITY_API_KEY=pplx-...
```

Save and close. Verify the keys are readable:

```bash
cat ~/.env | grep API_KEY
```

You should see at least one key.

## Step 5: Run Your First Research

Navigate to a project directory (or create one):

```bash
mkdir -p ~/my-projects/research-test && cd ~/my-projects/research-test
```

Run research on a topic of your choice:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "What are the latest developments in AI safety?" \
  --depth quick
```

Watch the output:

```
Researching: What are the latest developments in AI safety?
Depth: quick | Providers: claude, openai, gemini, perplexity
  claude: OK (18.3s)
  openai: OK (22.1s)
  gemini: OK (16.7s)
  perplexity: OK (25.4s)

Results written to .research/
```

**Congrats!** Your first research completed in under 2 minutes.

## Step 6: Explore the Output

See what was created:

```bash
ls -la .research/
```

You'll see:

```
.research/
├── raw/
│   ├── claude-20260326-1407.md
│   ├── openai-20260326-1407.md
│   ├── gemini-20260326-1408.md
│   └── perplexity-20260326-1410.md
└── research.yaml
```

### Raw Files

Each provider's raw response is saved as Markdown:

```bash
cat .research/raw/claude-*.md
```

This is the unstructured output directly from the LLM. It's useful for reference but harder to compare across providers.

### Manifest

The manifest tracks which providers ran, execution times, and status:

```bash
cat .research/research.yaml
```

Output:

```yaml
topic: "What are the latest developments in AI safety?"
topic_slug: what-are-the-latest-developments-in-ai-safety
depth: quick
initiated: 2026-03-26T14:07:50Z
completed: 2026-03-26T14:08:20Z
status: complete
providers:
  claude:
    status: success
    model: claude-sonnet-4-6
    duration_seconds: 18.3
    raw_file: raw/claude-20260326-1407.md
  # ... other providers
meta_analysis: null
```

## Step 7: Understand the Three Depths

You used `--depth quick`. Let's understand when to use each:

| Depth | Time | Use Case |
|-------|------|----------|
| **quick** | <1 min | Scout a topic; is there interesting research here? |
| **standard** | 3 min | Main research mode; balance time/quality |
| **deep** | 10 min | Comprehensive analysis; comparison papers |

Try standard depth for deeper results:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "What are the latest developments in AI safety?" \
  --depth standard
```

This takes ~3 minutes but produces richer output (each provider runs a 3-call refinement chain).

## Step 8: Create an Alias (Optional)

Typing the full path is tedious. Create a shell alias:

```bash
# Add to ~/.zshrc (or ~/.bash_profile for bash)
echo "alias research='~/.claude/skills/parallel-research/.venv/bin/python ~/.claude/skills/parallel-research/research_runner.py'" >> ~/.zshrc

# Reload shell
source ~/.zshrc

# Now you can use:
research --topic "Your topic" --depth quick
```

## Checking Your Work

You've completed this tutorial if:

✅ Python 3.11+ is installed
✅ `~/.claude/skills/parallel-research/` exists
✅ `.venv/` virtual environment exists in that directory
✅ API keys are in `~/.env`
✅ You ran research and got output in `.research/`
✅ `.research/raw/` contains markdown files from each provider
✅ `.research/research.yaml` shows provider status

## Next Steps

- **[Basic Research](howto-basic-research.md)** — Run different depth levels and select specific providers
- **[Deep Research](howto-deep-research.md)** — For comprehensive analysis
- **[Meta-Analysis](howto-meta-analysis.md)** — Cross-reference findings across providers
- **[Architecture](reference-architecture.md)** — Understand how it works under the hood
- **[Claude Code Integration](../SKILL.md)** — Use `/research` directly in Claude Code

## Troubleshooting

### Setup failed: "python3 --version shows 3.10"

Upgrade Python:

```bash
# macOS with Homebrew
brew install python@3.11
brew link python@3.11
python3 --version  # Should now show 3.11+
```

### "ModuleNotFoundError: No module named 'anthropic'"

Virtual environment wasn't activated or setup failed. Retry:

```bash
cd ~/.claude/skills/parallel-research
./setup
source .venv/bin/activate
python -c "import anthropic; print('OK')"
```

### "ERROR: No providers available. Check your API keys"

No API keys found in `~/.env`:

```bash
# Verify keys are set
cat ~/.env

# Add a key if empty
echo "ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE" >> ~/.env
```

### Research times out (> 60s for quick)

A provider is slow or rate-limited. Retry or use fewer providers:

```bash
research --topic "Your topic" --depth quick --providers claude,perplexity
```

### One provider failed, others succeeded

This is normal. The manifest shows which providers succeeded:

```bash
cat .research/research.yaml | grep status
```

You can proceed with the successful providers' data.

## Resources

- **[Reference Documentation](reference-architecture.md)** — Architecture, APIs, output format
- **[Design Rationale](explanation-design.md)** — Why it works this way
- **[GitHub Repository](https://github.com/AdenCJM/parallel-research)** — Source code, issues, contributions
- **[Anthropic Docs](https://docs.anthropic.com/)** — Claude API reference
- **[OpenAI Docs](https://platform.openai.com/docs/)** — OpenAI API reference

## Support

If something breaks:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Read the [Architecture](reference-architecture.md) for detailed explanations
3. Open an issue on [GitHub](https://github.com/AdenCJM/parallel-research/issues)
