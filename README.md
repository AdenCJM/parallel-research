# Parallel Research

Grounded research from multiple model providers, kept as inspectable evidence inside your project.

Parallel Research is a Claude Code skill that asks Claude, OpenAI, Gemini, and Perplexity to
research the same topic concurrently. Each invocation receives an isolated run directory, source
metadata, resumable background state, structured provider reports, and an optional evidence-aware
comparison.

```text
/research --meta "How are battery recycling mandates changing in Australia?"
```

```text
.research/
├── index.yaml
└── runs/
    └── 20260718T074512Z-a1b2c3-battery-recycling-australia/
        ├── research.yaml
        ├── raw/
        │   ├── claude.md
        │   ├── openai.md
        │   ├── gemini.md
        │   └── perplexity.md
        ├── structured/
        │   └── ...
        └── meta-analysis.md
```

## What it is for

Different providers can find different sources, frame uncertainty differently, and expose useful
contradictions. Parallel Research preserves those perspectives instead of flattening them into one
opaque answer.

Model agreement is not treated as proof. Meta-analysis distinguishes:

- corroboration by independent inspectable sources;
- single-source findings;
- cross-model agreement with unknown source independence;
- contested findings; and
- unverified model output.

All four integrations use provider-native web grounding in quick and standard modes. OpenAI and
Perplexity use specialized deep-research models in deep mode; Claude and Gemini currently use the
standard evidence-gap refinement workflow.

## Install

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/AdenCJM/parallel-research.git \
  ~/.claude/skills/parallel-research
cd ~/.claude/skills/parallel-research
./setup
```

The setup command creates a locked virtual environment. See the
[getting-started tutorial](docs/tutorial-getting-started.md) for development and symlink installs.

## Configure providers

Add the providers you intend to use to `~/.env` or the research project's `.env`:

```dotenv
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
GOOGLE_AI_API_KEY=...
PERPLEXITY_API_KEY=...
```

Project-local values override `~/.env`. Missing providers fail visibly without preventing other
providers from completing.

Research topics are sent to the selected third parties. Do not submit confidential information
without reviewing each provider's current data controls. Generated research may also contain
untrusted webpage content; the skill treats it as data and does not follow embedded instructions.

Add `.research/` to the consuming project's `.gitignore` if outputs should remain local.

## Use

From a project in Claude Code:

```text
/research "Your topic"
/research --depth quick --providers claude,perplexity "Your topic"
/research --depth deep "Your topic"
/research --meta "Your topic"
/research --meta
```

`--meta` without a topic selects one latest isolated run. It never scans or combines all prior
research.

Depth controls workflow, not a guaranteed time, cost, or token count:

| Depth | Behavior |
|---|---|
| `quick` | One grounded request per provider |
| `standard` | Grounded research, evidence-gap search, then synthesis |
| `deep` | Native deep research where supported; resumable when it outlives the local wait |

Deep research can take tens of minutes and incur material API cost. Review provider pricing before
use. Model defaults and provider controls can be overridden with the environment variables
documented in [provider selection](docs/howto-select-providers.md).

## Internal CLI

The Python executable is the deterministic fetch and run-state layer used by the skill:

```bash
parallel-research fetch --topic "Your topic" --depth standard
parallel-research status --run <run-id>
parallel-research resume --run <run-id>
parallel-research validate --run <run-id>
```

Structuring and meta-analysis remain Claude Code workflows. The Python CLI does not advertise an
unsupported `--meta` flag.

## Reliability and safety

- Every invocation receives a timestamped, randomized run ID.
- Manifests are written atomically.
- Background OpenAI request IDs are persisted before polling.
- Provider failures and missing keys are isolated.
- Citations and reported usage are captured structurally where APIs expose them.
- Stored error messages redact common credential formats.
- The agent reads only files declared by the selected run manifest.
- Raw research is explicitly treated as hostile data.

See [architecture](docs/reference-architecture.md), [output format](docs/reference-output-format.md),
and [design rationale](docs/explanation-design.md).

## Development

```bash
uv sync --locked --extra dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
uv run python scripts/check_markdown_links.py
bash scripts/audit_dependencies
uv build
```

Tests use fake or mocked providers and do not make billable requests. See
[CONTRIBUTING.md](CONTRIBUTING.md) before changing provider contracts.
Report vulnerabilities according to [SECURITY.md](SECURITY.md).

## Documentation

| Goal | Guide |
|---|---|
| Install and run the first query | [Getting started](docs/tutorial-getting-started.md) |
| Run a basic query | [Basic research](docs/howto-basic-research.md) |
| Choose providers and models | [Provider selection](docs/howto-select-providers.md) |
| Use deep research and resume | [Deep research](docs/howto-deep-research.md) |
| Compare evidence | [Meta-analysis](docs/howto-meta-analysis.md) |
| Add a provider | [Adding a provider](docs/howto-add-provider.md) |
| Understand provider contracts | [BaseProvider API](docs/reference-baseprovider-api.md) |

## Licence

[MIT](LICENSE)
