# How to Generate Meta-Analysis

Cross-reference claims across providers to identify high-confidence findings, contradictions, and unique insights.

## Why Meta-Analysis?

- **Identify high-confidence findings:** What 3+ providers agree on
- **Spot contradictions:** Where providers disagree (signals need for deeper research)
- **Flag unverified insights:** Valuable findings from only one provider
- **Confidence scoring:** Know which claims to trust vs investigate further

## Prerequisites

- Research output in `.research/` (from Phase 1)
- At least 2 providers succeeded (meta-analysis on single provider is not useful)
- Virtual environment activated

## Steps

### 1. Run Meta-Analysis on Existing Research

If you already have research in `.research/`:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --meta
```

This reads all `.research/raw/` files and generates `meta-analysis.md`.

### 2. Fetch & Analyze in One Step

Combine research and meta-analysis:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "What are the most promising battery technologies?" \
  --depth standard \
  --meta
```

This runs Phase 1 (fetch), then Phase 3 (meta-analysis). Phase 2 (structured files) is skipped — meta-analysis works directly from raw output.

### 3. Review the Meta-Analysis Output

Read the generated meta-analysis:

```bash
cat .research/meta-analysis.md
```

Structure (from the reference):

```markdown
# Meta-Analysis: [Your Topic]

## High-Confidence Findings
[Claims supported by 3-4 providers]

## Medium-Confidence Findings
[Claims supported by 2 providers]

## Contradictions
[Where providers disagree]

## Unique Insights
[Single-provider findings]

## Recommended Follow-Up
[Questions remaining]
```

## Understanding the Output

### High-Confidence Findings

These are your strongest signals. All or most providers independently arrived at the same conclusion.

**Example:**
```markdown
- **Finding:** Battery density has improved 2-3% annually over the past decade
  - Claude: Cites Department of Energy report showing 2.1% improvement
  - OpenAI: Corroborates with lithium-ion density trend data
  - Perplexity: Aligns on timeline, mentions solid-state battery target of 5% improvement
  - Gemini: References academic papers showing consistent trend
```

Action: Use confidently in decision-making.

### Medium-Confidence Findings

Two providers agree, but not universal consensus. May indicate emerging consensus or a less-studied angle.

**Example:**
```markdown
- **Finding:** Solid-state batteries will dominate by 2030
  - Claude: Predicts 40% market penetration by 2030
  - Perplexity: Agrees, cites Toyota and Samsung timelines
  - OpenAI: No mention (focuses on current tech)
  - Gemini: No mention
```

Action: Investigate further before relying on this for high-stakes decisions.

### Contradictions

Different providers disagree. This is valuable signal — it means the answer is genuinely uncertain or the question was misunderstood differently.

**Example:**
```markdown
- **Question:** Will solid-state batteries replace lithium-ion?
  - Claude: "Solid-state will coexist; lithium-ion won't disappear entirely"
  - Perplexity: "Solid-state will dominate in EVs; lithium-ion relegated to edge devices"
  - OpenAI: "Timelines unclear; adoption depends on manufacturing scale"
  - Gemini: "Multiple battery types will serve different niches"
```

Action: This is the question to research *deeper*. Each provider has valid reasoning; the disagreement is real.

### Unique Insights

Valuable findings from only one provider — potentially a competitive advantage or a hallucination.

**Example:**
```markdown
- **Perplexity only:** Samsung SDI's recent patent on lithium-metal anodes
  (not mentioned by Claude, OpenAI, or Gemini)
```

Action: Verify before citing. Perplexity has strong search capabilities; if it found a real source, this is genuinely new insight.

## Common Patterns

### Use Meta-Analysis to Resolve Disagreement

When team members disagree on a question, run research with meta-analysis:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "When will <disputed_claim> actually happen?" \
  --depth standard \
  --meta
```

Meta-analysis reveals:
- What experts (via LLMs) broadly agree on
- Where genuine uncertainty exists
- Which angles need deeper investigation

### Build Confidence Incrementally

Start with quick research + meta-analysis to scout:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Your question" \
  --depth quick \
  --meta
```

If you see high-confidence findings, use them. If you see contradictions, follow up with deeper research:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Your question" \
  --depth deep \
  --meta
```

### Identify Research Gaps

Recommended Follow-Up section highlights unknowns:

```bash
# Extract follow-up questions
grep -A 50 "Recommended Follow-Up" .research/meta-analysis.md
```

Example:
```
## Recommended Follow-Up

- Verify Samsung SDI patent (claimed by Perplexity only, not found by others)
- Compare cost curves for competing battery chemistries
- Trace supply chain constraints that may slow adoption
- Check for discrepancies in "2030 penetration" predictions
```

Each follow-up becomes a new research topic:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Samsung SDI lithium-metal anodes patent details and timeline" \
  --depth deep \
  --meta
```

## Confidence Scoring Explained

Meta-analysis assigns confidence based on agreement:

| Confidence | Providers Agree | Your Action |
|------------|-----------------|-----------|
| **High** | 3-4 | Use confidently; low fact-check burden |
| **Medium** | 2 | Investigate further; may be emerging consensus |
| **Low** | 1 | Verify independently; may be hallucination or niche insight |

**Note:** Confidence ≠ truth. High agreement could mean all models have the same training bias. Always verify critical claims independently.

## Verification

Check that meta-analysis was generated:

```bash
cat .research/research.yaml | grep meta_analysis
```

Expected output:
```yaml
meta_analysis: meta-analysis.md
```

Verify the file exists and has content:

```bash
ls -lh .research/meta-analysis.md
wc -l .research/meta-analysis.md
```

Should be 50-200 lines depending on complexity.

## Troubleshooting

**Error: "No providers succeeded"**

Meta-analysis requires at least some successful raw output:

```bash
# Check what failed
cat .research/research.yaml | grep status
```

If all providers failed, resolve API key or network issues and retry.

**Meta-analysis has no findings**

Either:
1. Raw output was too brief (use `--depth deep`)
2. Providers gave contradictory output (legitimate, shows in Contradictions section)

Retry with more providers or deeper research:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "Your topic" \
  --depth deep \
  --meta
```

**One provider seems to hallucinate (unique insight not found by others)**

This is expected. Meta-analysis flags unique insights explicitly so you can investigate. Steps:

1. Note the claim
2. Search for it independently (Google, academic databases)
3. If real, great — you found something others missed
4. If false, good — you caught a hallucination before using it

## Next Steps

- [Structure raw output](howto-structure-research.md) using Claude Code
- [Use meta-analysis in Claude Code](howto-claude-code-integration.md) as context for builds
- [Read the output format](reference-output-format.md) for meta-analysis schema
