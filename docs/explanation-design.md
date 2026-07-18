# Explanation: Design Rationale

## Why multiple providers?

Provider differences are useful for discovering alternative sources, frames, and disagreements.
They do not create independent evidence by themselves. The system therefore preserves provider
provenance while scoring evidence by inspectable source support rather than model votes.

## Why native grounding everywhere?

Prompting an ungrounded model to provide URLs invites fabricated or stale citations. Quick and
standard modes enable each provider's search capability and capture citation metadata separately
from prose. Output without an inspectable citation remains visible but is labelled unverified.

## Why isolated runs?

A flat `.research/` directory allowed timestamp collisions, manifest replacement, and accidental
comparison of unrelated topics. Each invocation now receives a randomized run directory. The index
points to runs, while each run manifest is authoritative.

## Why agent-driven structuring?

Claude Code can organize nuanced prose without introducing another fixed synthesis API dependency.
The deterministic Python layer owns provider calls and state; the skill owns interpretation. The
boundary is explicit: Python has no `--meta` option, and agent-written artifacts are recorded through
validated CLI commands.

## Why treat output as hostile?

Grounded models read webpages that may contain prompt injection. A retrieved instruction has no
authority over the coding agent. The skill confines itself to one manifest, forbids acting on raw
commands, and processes content only as claims, citations, and limitations.

## Why resumable state?

Deep research can outlive an interactive wait. A hard timeout can abandon billable remote work.
Parallel Research persists a background request ID immediately, marks the provider `resumable`, and
retrieves the same request later instead of submitting a duplicate.

## Why atomic YAML?

YAML remains readable to humans and agents. Temporary-file replacement prevents readers from seeing
a partially written manifest. A schema version makes future migrations explicit.

## Why no fixed time or price promises?

Provider pricing, search behavior, access tiers, and model latency change. The application records
reported usage and exposes effort controls, but the documentation avoids guarantees that cannot be
enforced. Users should review current provider pricing before deep runs.

## Remaining limitations

- Citation presence does not prove source quality or that a claim accurately represents the source.
- URL canonicalization during agent meta-analysis is heuristic.
- Claude and Gemini deep mode currently use standard refinement rather than native asynchronous deep
  research.
- Secret redaction covers common patterns but cannot recognize every possible credential format.
- High-stakes conclusions still require human verification against primary sources.
