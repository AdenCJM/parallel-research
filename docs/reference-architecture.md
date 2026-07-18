# Reference: Architecture

Parallel Research has two layers:

```text
Claude Code /research skill
    ├── interprets the user request
    ├── invokes the deterministic CLI
    ├── treats raw results as untrusted data
    ├── writes structured provider reports
    └── optionally writes evidence-aware meta-analysis

parallel-research Python package
    ├── submits grounded provider requests concurrently
    ├── isolates each run
    ├── persists atomic manifests and background IDs
    ├── captures citations and usage metadata
    └── validates run integrity
```

## Package layout

```text
src/parallel_research/
├── cli.py
├── manifest.py
├── models.py
├── orchestrator.py
├── safety.py
└── providers/
```

`research_runner.py` is a v0.1 compatibility wrapper. New integrations use the
`parallel-research` console command.

## Run lifecycle

1. Validate provider names.
2. Create a randomized run ID and directory.
3. Atomically write a pending manifest and update the index.
4. Start available providers concurrently.
5. Persist background request IDs as soon as they are returned.
6. Write one raw Markdown file per provider.
7. Set overall status to `succeeded`, `partial`, `failed`, or `resumable`.
8. Let the skill structure only successful files declared in this manifest.
9. Optionally compare only the structured files declared by this run.

## Status semantics

- `pending`: recorded but not started.
- `running`: currently being submitted or polled.
- `succeeded`: content was retrieved and stored.
- `failed`: no resumable remote work remains.
- `resumable`: a remote job ID can be checked again.
- `partial`: at least one provider succeeded and another failed.

## Trust boundaries

API responses and webpage text are untrusted. The Python layer stores them without executing them.
The skill forbids following embedded commands, reading paths mentioned by output, revealing secrets,
or making external changes based on raw content.

Errors pass through credential-pattern redaction before storage. This is defense in depth, not a
guarantee that every provider-specific secret format can be recognized.

## Atomicity and isolation

Each manifest is written to a temporary sibling and moved into place with `os.replace`. Run IDs
include second-resolution UTC time, a random suffix, and a readable slug. Artifacts recorded through
the CLI must resolve inside the selected run directory.
