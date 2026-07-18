# How to Generate Meta-Analysis

Meta-analysis is performed by the Claude Code skill over one explicitly selected run.

Fetch and compare in one invocation:

```text
/research --meta "What evidence supports long-duration energy storage technologies?"
```

Compare the latest existing run:

```text
/research --meta
```

The second form resolves `.research/index.yaml` to one run ID. It never scans every prior raw or
structured file. If the latest run is not the intended subject, provide or select the correct run
instead of combining output.

## Interpret evidence labels

| Label | Meaning |
|---|---|
| Corroborated | Multiple independent inspectable sources support the claim |
| Single-source | One inspectable source supports the claim |
| Cross-model agreement | Multiple models state it, but source independence is unknown |
| Contested | Credible outputs or sources disagree |
| Unverified | No inspectable source supports the claim |

Three models repeating one article remain one source. Cross-model agreement can reveal stable
framing, but it does not reduce the need to verify consequential claims.

The result is written to `.research/runs/<run-id>/meta-analysis.md` and recorded in that run's
manifest.

## Verify the artifact

```bash
parallel-research validate --run <run-id> --output .research
parallel-research status --run <run-id> --output .research
```

Review the **Recommended Verification** section before relying on research for legal, medical,
financial, safety, or other high-stakes decisions.
