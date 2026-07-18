# Roadmap

## Native deep research for Claude and Gemini

Adopt provider-native asynchronous deep-research APIs only after they expose stable request handles,
citations, cost controls, and resume behavior compatible with the run manifest.

## Evidence verification

Add optional source fetching and claim-to-passage checks. Keep this separate from cross-model
agreement and require explicit network access.

## Historical run migration

Provide an opt-in command that imports the v0.1 flat `.research/` layout into schema-versioned run
directories without deleting original files.

## Live provider evaluation

Maintain a manually triggered, budget-limited evaluation across representative factual topics. Track
citation validity, duplicate-source rate, latency, and reported provider cost without exposing keys
to pull-request builds.
