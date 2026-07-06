# How to Add a New Provider

Add support for a new LLM provider (e.g., Anthropic's API wrapper, a local model, a proprietary API).

## Prerequisites

- Understanding of Python async/await
- API documentation for the provider you're adding
- Ability to test the implementation
- Familiarity with `BaseProvider` API (see [BaseProvider Reference](reference-baseprovider-api.md))

## Overview

Adding a provider involves:
1. Creating a new Python file in `providers/`
2. Implementing the `BaseProvider` interface
3. Registering it in `research_runner.py`
4. Testing with real API calls

## Steps

### Step 1: Create the Provider File

Create `providers/new_provider.py`:

```bash
touch providers/new_provider.py
```

### Step 2: Implement the BaseProvider Interface

Start with the boilerplate:

```python
# providers/new_provider.py

from __future__ import annotations

import os
import time

from .base import (
    BaseProvider,
    Depth,
    ResearchResult,
    RESEARCH_SYSTEM_PROMPT,
    REFINEMENT_PROMPT,
    SYNTHESIS_PROMPT,
    with_retries,
)


class NewproviderProvider(BaseProvider):
    """Description of your provider."""

    name = "newprovider"  # Must be lowercase, matches class name prefix

    def __init__(self) -> None:
        # Load API key from environment
        self.api_key = os.environ.get("NEWPROVIDER_API_KEY", "")

    @property
    def available(self) -> bool:
        """Check if API key is present and valid."""
        return bool(self.api_key)

    async def research(self, topic: str, depth: Depth) -> ResearchResult:
        """Run research query. Must never raise."""
        start = time.monotonic()
        model = "your-model-name"
        
        try:
            # Implement research logic here
            if depth == Depth.QUICK:
                result = await self._quick_research(topic, start, model)
            elif depth == Depth.STANDARD:
                result = await self._standard_research(topic, start, model)
            else:  # DEEP
                result = await self._deep_research(topic, start, model)
            
            return result
            
        except Exception as exc:
            return ResearchResult(
                provider=self.name,
                model=model,
                content="",
                duration_seconds=time.monotonic() - start,
                error=f"{type(exc).__name__}: {exc}",
            )

    async def _quick_research(
        self, topic: str, start: float, model: str
    ) -> ResearchResult:
        """Single API call."""
        # TODO: Implement
        pass

    async def _standard_research(
        self, topic: str, start: float, model: str
    ) -> ResearchResult:
        """Three-call refinement chain."""
        # TODO: Implement
        pass

    async def _deep_research(
        self, topic: str, start: float, model: str
    ) -> ResearchResult:
        """Deep research (native or fallback)."""
        # TODO: Implement
        pass
```

### Step 3: Implement Quick Research

Quick research is a single API call:

```python
async def _quick_research(
    self, topic: str, start: float, model: str
) -> ResearchResult:
    """Single API call."""
    from newprovider import AsyncNewProvider  # Your SDK
    
    client = AsyncNewProvider(api_key=self.api_key)
    
    response = await with_retries(
        client.chat.completions.create,
        model=model,
        messages=[
            {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
            {"role": "user", "content": f"Research the following topic:\n\n{topic}"},
        ],
        max_tokens=Depth.QUICK.max_output_tokens,
        timeout=Depth.QUICK.timeout_seconds,
    )
    
    # Extract content from response (provider-specific)
    content = response.choices[0].message.content
    
    return ResearchResult(
        provider=self.name,
        model=model,
        content=content,
        duration_seconds=time.monotonic() - start,
    )
```

### Step 4: Implement Standard Research

Three-call refinement chain:

```python
async def _standard_research(
    self, topic: str, start: float, model: str
) -> ResearchResult:
    """Three-call refinement chain: initial → gaps → synthesis."""
    from newprovider import AsyncNewProvider
    
    client = AsyncNewProvider(api_key=self.api_key)
    messages = [
        {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
        {"role": "user", "content": f"Research the following topic:\n\n{topic}"},
    ]
    
    # Call 1: Initial research
    r1 = await with_retries(
        client.chat.completions.create,
        model=model,
        messages=messages,
        max_tokens=4096,
        timeout=Depth.STANDARD.timeout_seconds,
    )
    r1_content = r1.choices[0].message.content
    messages.append({"role": "assistant", "content": r1_content})
    
    # Call 2: Identify gaps
    messages.append({"role": "user", "content": REFINEMENT_PROMPT})
    r2 = await with_retries(
        client.chat.completions.create,
        model=model,
        messages=messages,
        max_tokens=4096,
    )
    r2_content = r2.choices[0].message.content
    messages.append({"role": "assistant", "content": r2_content})
    
    # Call 3: Synthesis
    messages.append({"role": "user", "content": SYNTHESIS_PROMPT})
    r3 = await with_retries(
        client.chat.completions.create,
        model=model,
        messages=messages,
        max_tokens=Depth.STANDARD.max_output_tokens,
    )
    r3_content = r3.choices[0].message.content
    
    return ResearchResult(
        provider=self.name,
        model=model,
        content=r3_content,
        duration_seconds=time.monotonic() - start,
    )
```

### Step 5: Implement Deep Research

Deep research can be native or fallback to standard:

```python
async def _deep_research(
    self, topic: str, start: float, model: str
) -> ResearchResult:
    """Native deep research (if available) or fallback to standard."""
    # If your provider has a native deep-research endpoint, use it here
    # Otherwise, fall back to standard:
    return await self._standard_research(topic, start, model)
```

Example with native deep research (like OpenAI's approach):

```python
async def _deep_research(
    self, topic: str, start: float, model: str
) -> ResearchResult:
    """Use provider's native deep-research API."""
    from newprovider import AsyncNewProvider
    
    client = AsyncNewProvider(api_key=self.api_key)
    
    # Some providers have dedicated deep-research endpoints
    response = await with_retries(
        client.deep_research.create,
        query=topic,
        model="newprovider-deep",  # Deep research model variant
        max_tokens=Depth.DEEP.max_output_tokens,
        timeout=Depth.DEEP.timeout_seconds,
    )
    
    return ResearchResult(
        provider=self.name,
        model="newprovider-deep",
        content=response.result,
        duration_seconds=time.monotonic() - start,
    )
```

### Step 6: Register in research_runner.py

Add your provider to the `ALL_PROVIDERS` dict:

```python
# research_runner.py

from providers.new_provider import NewproviderProvider

ALL_PROVIDERS = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "perplexity": PerplexityProvider,
    "newprovider": NewproviderProvider,  # ADD THIS LINE
}
```

### Step 7: Test

Create a test script:

```bash
# test_new_provider.py

import asyncio
import os
from providers.new_provider import NewproviderProvider
from providers.base import Depth
from dotenv import load_dotenv

async def test():
    load_dotenv()
    provider = NewproviderProvider()
    
    if not provider.available:
        print("ERROR: API key not found in environment")
        return
    
    print("Testing quick research...")
    result = await provider.research("What is quantum computing?", Depth.QUICK)
    print(f"Status: {'OK' if not result.error else 'FAILED'}")
    print(f"Duration: {result.duration_seconds:.1f}s")
    if result.error:
        print(f"Error: {result.error}")
    else:
        print(f"Content length: {len(result.content)} chars")
        print(f"First 200 chars: {result.content[:200]}")

asyncio.run(test())
```

Run the test:

```bash
source .venv/bin/activate
python test_new_provider.py
```

### Step 8: Update Dependencies (if needed)

If your provider requires new Python packages:

```bash
# Add to pyproject.toml
echo 'newprovider = "^1.0"' >> pyproject.toml

# Reinstall
./setup
```

### Step 9: Test Integration

Run research with your new provider:

```bash
~/.claude/skills/parallel-research/.venv/bin/python \
  ~/.claude/skills/parallel-research/research_runner.py \
  --topic "What is machine learning?" \
  --depth quick \
  --providers newprovider
```

Expected output:
```
Researching: What is machine learning?
Depth: quick | Providers: newprovider
  newprovider: OK (32.5s)

Results written to .research/
```

## Implementation Patterns

### Error Handling

Never raise from `research()` — catch all exceptions:

```python
async def research(self, topic: str, depth: Depth) -> ResearchResult:
    start = time.monotonic()
    model = "your-model"
    
    try:
        # Implementation
        response = await self.client.call(...)
        return ResearchResult(
            provider=self.name,
            model=model,
            content=response.text,
            duration_seconds=time.monotonic() - start,
        )
    except ValueError as exc:
        return ResearchResult(
            provider=self.name,
            model=model,
            content="",
            duration_seconds=time.monotonic() - start,
            error=f"ValueError: {exc}",
        )
    except Exception as exc:
        return ResearchResult(
            provider=self.name,
            model=model,
            content="",
            duration_seconds=time.monotonic() - start,
            error=f"{type(exc).__name__}: {exc}",
        )
```

### Handling Async Clients

Always use the async variant of the SDK:

```python
# WRONG (blocks event loop)
from newprovider import NewProvider
client = NewProvider(api_key=self.api_key)

# RIGHT (async)
from newprovider import AsyncNewProvider
client = AsyncNewProvider(api_key=self.api_key)
await client.chat.completions.create(...)
```

### Using with_retries() for Resilience

Wrap API calls to handle rate limits:

```python
response = await with_retries(
    client.chat.completions.create,
    model=model,
    messages=messages,
    max_tokens=8192,
    timeout=180,
)
```

The `with_retries()` function handles 429, 500, 502, 503, 529 automatically.

### Extracting Content from Responses

Different providers have different response shapes. Always extract carefully:

```python
# OpenAI-style
content = response.choices[0].message.content

# Anthropic-style
content = response.content[0].text

# Gemini-style
content = response.candidates[0].content.parts[0].text

# Perplexity-style
content = response.choices[0].message.content
```

## Testing Checklist

Before submitting:

- [ ] `available` property returns True when API key is set
- [ ] Quick research completes in < 60 seconds
- [ ] Standard research completes in < 180 seconds
- [ ] Deep research completes in < 600 seconds
- [ ] All responses contain Markdown content (not empty strings)
- [ ] Error handling works (no exceptions raised)
- [ ] Timeout enforcement works (graceful degradation at depth limit)
- [ ] Rate limit retry works (returns success after transient 429)
- [ ] Bad API key returns `ResearchResult` with error (never raises)
- [ ] Meta-analysis works on output (raw files are valid markdown)

## Common Issues

### SDK Not Imported

```python
# ERROR: ModuleNotFoundError: No module named 'newprovider'

# FIX: Add to imports, lazy-load inside method
from newprovider import AsyncNewProvider  # Move inside research()
```

### Content Extraction Fails

```python
# ERROR: IndexError: list index out of range

# FIX: Add defensive checks
content = ""
if response.choices and len(response.choices) > 0:
    content = response.choices[0].message.content or ""
```

### Timeout Not Enforced

```python
# Wrong: no timeout passed
response = await client.call(...)

# Right: timeout enforced
response = await with_retries(
    client.call,
    ...,
    timeout=depth.timeout_seconds,
)
```

## Next Steps

- [Run research with your provider](howto-select-providers.md)
- [Contribute back](../CONTRIBUTING.md) (if you want to share your provider)
