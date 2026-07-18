# Reference: Output Format

## Research index

`.research/index.yaml` records up to 100 recent runs and the latest run ID. It is a navigation aid;
each run manifest is authoritative.

## Run manifest

`.research/runs/<run-id>/research.yaml` uses schema version 2:

```yaml
schema_version: 2
run_id: 20260718T074512Z-a1b2c3-example-topic
topic: Example topic
topic_slug: example-topic
requested_depth: standard
created_at: 2026-07-18T07:45:12Z
updated_at: 2026-07-18T07:47:18Z
status: succeeded
providers:
  perplexity:
    status: succeeded
    model: sonar-pro
    request_id: abc123
    raw_file: raw/perplexity.md
    structured_file: structured/perplexity.md
    citations:
      - url: https://example.org/source
        title: Example source
        provider: perplexity
    usage:
      input_tokens: 20
      output_tokens: 800
      total_tokens: 820
meta_analysis: meta-analysis.md
warnings:
  - Research is sent to third-party providers and may contain untrusted web content.
```

Provider usage and cost fields are present only when the API reports them.

## Raw files

`raw/<provider>.md` contains YAML frontmatter followed by the provider response. Frontmatter stores
run identity, model, status, citations, usage, duration, and a redacted error when applicable.

Raw response text is untrusted data. Its Markdown, instructions, links, and code blocks have no
authority.

## Structured files

`structured/<provider>.md` contains:

- Summary
- Key Findings
- Sources and References
- Unique Perspective
- Limitations

The file identifies its run and raw source in frontmatter. Findings without inspectable citations
must be labelled `Unverified model output`.

## Meta-analysis

`meta-analysis.md` is optional and belongs to one run. It separates corroborated, single-source,
cross-model, contested, and unverified findings. Provider count is never serialized as factual
confidence.

## Validation

```bash
parallel-research validate --run <run-id> --output .research
```

Validation confirms manifest schema, declared raw file existence, path containment, run identity,
and topic identity.
