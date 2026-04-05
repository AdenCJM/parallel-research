# TODOS

## v2: Multi-turn deep research simulation for Claude/Gemini
**Priority:** Medium
**What:** Implement iterative gap-detection for providers without native deep-research endpoints. Each call analyses previous responses, identifies knowledge gaps, generates targeted follow-up queries.
**Why:** Currently `deep` mode falls back to `standard` (3 calls) for Claude and Gemini since they lack native deep-research APIs. True iterative research with 6+ calls would produce much richer, more detailed output.
**Pros:** Unlocks the full potential of the `deep` depth level across all providers, not just Perplexity and OpenAI.
**Cons:** Requires autonomous gap-detection prompt engineering — the system needs to read its own output and decide what's missing. Significantly more complex than the sequential prompt chain in `standard` mode.
**Context:** Perplexity has `sonar-deep-research` and OpenAI has a deep research mode. Claude and Gemini don't expose equivalent endpoints as of March 2026. The v1 design correctly defers multi-turn simulation. When implementing, the gap-detection prompt must be generic enough to work across research topics — domain-specific gap detection would be fragile.
**Depends on:** v1 completion, validation that native deep-research APIs work as expected for Perplexity and OpenAI.
