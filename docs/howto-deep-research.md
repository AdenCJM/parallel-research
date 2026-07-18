# How to Run and Resume Deep Research

Deep mode uses specialized deep-research APIs for OpenAI and Perplexity. Claude and Gemini use the
grounded standard refinement workflow.

```text
/research --depth deep "What evidence supports long-duration energy storage technologies?"
```

Deep requests may take tens of minutes and can incur material cost. Parallel Research warns before
starting, persists background request IDs, and stops waiting locally after a bounded period.

## Understand `resumable`

A provider marked `resumable` is not a failed research job. It means the remote background request
was still running when the local wait ended, or its status could not yet be confirmed.

Check status:

```bash
parallel-research status --run <run-id> --output .research
```

Resume without submitting a duplicate request:

```bash
parallel-research resume --run <run-id> --output .research
```

The stored request ID is used to retrieve the original job. Providers without asynchronous job
handles fail normally rather than pretending they can resume.

## Control cost and search effort

Set controls before invoking the skill:

```bash
export OPENAI_MAX_TOOL_CALLS=20
export PERPLEXITY_REASONING_EFFORT=low
```

These are effort controls, not guaranteed spending caps. Check provider dashboards after running.

## Compare depths safely

Each invocation is already isolated, so run both depths normally and compare their run IDs:

```text
/research --depth standard "Your topic"
/research --depth deep "Your topic"
```

Do not point both at a shared flat file set or combine their structured files implicitly.
