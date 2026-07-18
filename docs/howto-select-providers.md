# How to Select Providers

Choose a subset with a comma-separated list:

```text
/research --providers claude,perplexity "Your topic"
```

Available names are `claude`, `openai`, `gemini`, and `perplexity`. Unknown names are rejected;
missing API keys are recorded as provider failures while configured providers continue.

All providers use native web grounding. Their default models remain configurable:

| Provider | General default | Deep behavior | Override |
|---|---|---|---|
| Claude | `claude-sonnet-4-6` | standard refinement | `ANTHROPIC_MODEL` |
| OpenAI | `gpt-5.6-terra` | `o3-deep-research` | `OPENAI_MODEL`, `OPENAI_DEEP_MODEL` |
| Gemini | `gemini-2.5-pro` | standard refinement | `GEMINI_MODEL` |
| Perplexity | `sonar-pro` | `sonar-deep-research` | `PERPLEXITY_MODEL`, `PERPLEXITY_DEEP_MODEL` |

Cost and search controls:

- `OPENAI_MAX_TOOL_CALLS` defaults to `30` for deep research.
- `ANTHROPIC_MAX_SEARCHES` defaults to `8` per grounded request.
- `PERPLEXITY_REASONING_EFFORT` defaults to `medium` for deep research.

Provider pricing and model availability change. Check current provider documentation before a
large run rather than relying on a fixed estimate in this repository.
