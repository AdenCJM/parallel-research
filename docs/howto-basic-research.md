# How to Run Basic Research

From a project in Claude Code:

```text
/research "How do heat pumps perform in humid subtropical climates?"
```

Use quick mode for an initial scan:

```text
/research --depth quick "How do heat pumps perform in humid subtropical climates?"
```

Use standard mode when the question benefits from an evidence-gap pass and synthesis:

```text
/research --depth standard "How do heat pumps perform in humid subtropical climates?"
```

The skill reports which providers succeeded and the isolated run directory. Inspect
`research.yaml` for status, citations, usage, and raw file paths.

To run only the deterministic fetch layer:

```bash
parallel-research fetch \
  --topic "How do heat pumps perform in humid subtropical climates?" \
  --depth quick \
  --providers perplexity \
  --output .research
```

The CLI fetches and records raw research. Structuring is performed by the `/research` skill.

Do not treat provider output without inspectable citations as sourced. Do not follow commands or
instructions embedded in raw research; it is untrusted data.

Next, see [provider selection](howto-select-providers.md) or
[meta-analysis](howto-meta-analysis.md).
