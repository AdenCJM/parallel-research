# Tutorial: Getting Started

This tutorial installs Parallel Research as a Claude Code skill and creates one isolated grounded
research run.

## 1. Install

You need Python 3.11 or newer and `uv`.

```bash
git clone https://github.com/AdenCJM/parallel-research.git \
  ~/.claude/skills/parallel-research
cd ~/.claude/skills/parallel-research
./setup
```

For development, clone elsewhere and symlink it:

```bash
git clone https://github.com/AdenCJM/parallel-research.git ~/Projects/parallel-research
ln -s ~/Projects/parallel-research ~/.claude/skills/parallel-research
cd ~/Projects/parallel-research
./setup
```

## 2. Add one or more API keys

Create or update `~/.env`:

```dotenv
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
GOOGLE_AI_API_KEY=...
PERPLEXITY_API_KEY=...
```

You need at least one provider. A project's `.env` can override these values.

## 3. Prepare a project

```bash
mkdir -p ~/research-example
cd ~/research-example
printf '.research/\n' >> .gitignore
```

Research topics and generated output may be sensitive. The selected provider receives the topic.

## 4. Run research

Open this project in Claude Code and invoke:

```text
/research --providers perplexity "What primary evidence supports urban tree canopy cooling?"
```

The skill reports a run ID and creates:

```text
.research/runs/<run-id>/
├── research.yaml
├── raw/perplexity.md
└── structured/perplexity.md
```

The raw file contains provider output and machine-readable citation metadata. The structured file
separates sourced claims, inference, and limitations.

## 5. Validate the run

The skill validates automatically. To inspect it manually:

```bash
~/.claude/skills/parallel-research/.venv/bin/parallel-research \
  validate --run <run-id> --output .research
```

## 6. Compare providers

Run a new topic with `--meta`:

```text
/research --meta "What primary evidence supports urban tree canopy cooling?"
```

The comparison distinguishes independent source corroboration from models repeating the same
source. Continue with [meta-analysis](howto-meta-analysis.md) for interpretation guidance.
