# Parallel Research

Multi-LLM deep research skill for Claude Code. Runs Claude, OpenAI, Gemini, and Perplexity in parallel on a research topic and outputs structured markdown.

## Project Structure

- `research_runner.py`: asyncio orchestrator, CLI entry point
- `providers/`: one module per LLM provider, all implement `BaseProvider`
- `SKILL.md`: Claude Code skill instructions (orchestrates phases)
- `setup`: first-run bash script (creates venv, installs deps via uv)

## Development

```bash
./setup                    # Create venv and install deps
source .venv/bin/activate  # Activate for local dev
```

## Installation

Symlink this directory into your Claude Code skills:
```bash
ln -sf ~/Projects/ParallelResearch ~/.claude/skills/parallel-research
```

## API Keys

Set in `~/.env`:
```
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
GOOGLE_AI_API_KEY=...
PERPLEXITY_API_KEY=...
```
