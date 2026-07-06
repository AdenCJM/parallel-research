# BaseProvider API Reference

## Overview

`BaseProvider` is the abstract base class that all research providers implement. It defines the interface, error handling contract, and shared utilities.

**Location:** `providers/base.py`

## Classes

### `Depth` (Enum)

Controls research intensity and resource constraints.

```python
class Depth(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
```

#### Properties

**`max_output_tokens: int`**
- `QUICK`: 4096
- `STANDARD`: 8192
- `DEEP`: 16384

**`timeout_seconds: int`**
- `QUICK`: 60
- `STANDARD`: 180
- `DEEP`: 600

#### Usage

```python
from providers.base import Depth

depth = Depth("standard")
tokens = depth.max_output_tokens  # 8192
timeout = depth.timeout_seconds   # 180
```

### `ResearchResult` (Dataclass)

The return value from all provider `research()` calls.

```python
@dataclass
class ResearchResult:
    provider: str           # e.g., "claude", "openai"
    model: str              # e.g., "claude-sonnet-4-6"
    content: str            # Raw markdown response (empty if error)
    duration_seconds: float # Execution time
    error: str | None       # Error message (None if successful)
```

#### Fields

| Field | Type | Required | Description |
|-------|------|:---:|----------|
| `provider` | `str` | Yes | Provider name (lowercase, matches class name prefix) |
| `model` | `str` | Yes | Model identifier used (e.g., "claude-sonnet-4-6", "gpt-4o") |
| `content` | `str` | Yes | The research response in markdown. Empty string if `error` is set. |
| `duration_seconds` | `float` | Yes | Wall-clock execution time (includes retries, network latency) |
| `error` | `str \| None` | No | Error description if the request failed. `None` on success. |

#### Examples

```python
# Successful result
result = ResearchResult(
    provider="claude",
    model="claude-sonnet-4-6",
    content="# Research Results\n\n...",
    duration_seconds=45.3,
    error=None,
)

# Failed result
result = ResearchResult(
    provider="openai",
    model="gpt-4o",
    content="",
    duration_seconds=5.2,
    error="RateLimitError: Rate limit exceeded, retried 3 times",
)
```

### `BaseProvider` (Abstract Base Class)

The interface all providers must implement.

```python
class BaseProvider(ABC):
    name: str  # e.g., "claude", "openai", "gemini", "perplexity"

    @abstractmethod
    async def research(self, topic: str, depth: Depth) -> ResearchResult:
        """Run research query. Must never raise."""
        ...

    async def _safe_research(self, topic: str, depth: Depth) -> ResearchResult:
        """Wrapper that catches all exceptions."""
        ...

    @property
    @abstractmethod
    def available(self) -> bool:
        """True if API key is present and provider is ready."""
        ...
```

#### Abstract Methods

**`async research(topic: str, depth: Depth) -> ResearchResult`**

Implement this method in subclasses. Must never raise exceptions — all errors become `ResearchResult.error` strings.

**Contract:**
- Accept `topic` (string) and `depth` (Depth enum)
- Return `ResearchResult` with `content` or `error` (never both non-empty)
- Handle all API calls, retries, and error cases internally
- Track execution time and set `duration_seconds`
- Never raise — callers depend on exception-free returns

**Responsibilities:**
1. Check `self.available` before making API calls
2. Build appropriate prompts for the depth level
3. Make API calls via provider SDK
4. Handle rate limits and transient errors (use `with_retries()`)
5. Parse response and extract markdown
6. Catch all exceptions and return them as error strings
7. Set `model` to the actual model used (important for tracking)

#### Protected Methods

**`async _safe_research(topic: str, depth: Depth) -> ResearchResult`**

Wrapper around `research()` that adds:
- Timeout enforcement (`asyncio.wait_for()`)
- Exception catching (catches any exception that slips through)
- Time tracking

**Contract:** Always returns `ResearchResult`, never raises. Used by the orchestrator.

#### Properties

**`available: bool` (abstract)**

Return `True` if the provider is ready to run (API key present, credentials valid).

**Example:**
```python
@property
def available(self) -> bool:
    return bool(self.api_key)
```

#### Class Attributes

**`name: str` (required)**

Must match the provider's slug (used in filenames, provider lists).

**Examples:**
```python
class ClaudeProvider(BaseProvider):
    name = "claude"

class OpenAIProvider(BaseProvider):
    name = "openai"
```

## System Prompts (Constants)

These are shared across all providers for consistency.

### `RESEARCH_SYSTEM_PROMPT`

Used in all initial research queries.

```python
"You are a research assistant. Provide comprehensive, well-sourced research "
"on the given topic. Include specific facts, figures, named sources, and URLs "
"where available. Structure your response with clear sections."
```

### `REFINEMENT_PROMPT`

Used in the gap-identification step (standard depth, call 2 of 3).

```python
"Given your previous response, identify the 3 biggest gaps or unanswered "
"questions, then research those in depth."
```

### `SYNTHESIS_PROMPT`

Used in the final synthesis step (standard depth, call 3 of 3).

```python
"Synthesise all your findings into a single coherent, comprehensive response. "
"Preserve all specific facts, figures, and sources."
```

## Utilities

### `async with_retries(fn, *args, max_retries=3, **kwargs) -> T`

Decorator-like function that retries a coroutine with exponential backoff.

**Parameters:**
- `fn`: Async function to call
- `args`, `kwargs`: Arguments to pass to `fn`
- `max_retries`: Number of retries (default: 3)

**Retryable status codes:** 429 (rate limit), 500, 502, 503, 529 (server errors)

**Backoff delays:** [1s, 2s, 4s]

**Example:**

```python
from providers.base import with_retries

response = await with_retries(
    client.messages.create,
    model="claude-sonnet-4-6",
    max_tokens=8192,
    messages=[...],
    max_retries=3,
)
```

## Implementation Pattern

All providers follow this structure:

```python
from providers.base import (
    BaseProvider,
    Depth,
    ResearchResult,
    RESEARCH_SYSTEM_PROMPT,
    REFINEMENT_PROMPT,
    SYNTHESIS_PROMPT,
    with_retries,
)

class MyProvider(BaseProvider):
    name = "myprovider"  # Used in filenames and provider lists

    def __init__(self) -> None:
        self.api_key = os.environ.get("MY_API_KEY", "")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def research(self, topic: str, depth: Depth) -> ResearchResult:
        start = time.monotonic()
        model = "my-model-name"
        
        try:
            # Dispatch based on depth
            if depth == Depth.QUICK:
                return await self._quick_research(topic, start, model)
            elif depth == Depth.STANDARD:
                return await self._standard_research(topic, start, model)
            else:  # DEEP
                return await self._deep_research(topic, start, model)
                
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
        # Single API call
        response = await with_retries(
            self.client.call,
            topic=topic,
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            max_tokens=Depth.QUICK.max_output_tokens,
        )
        return ResearchResult(
            provider=self.name,
            model=model,
            content=response.text,
            duration_seconds=time.monotonic() - start,
        )

    async def _standard_research(
        self, topic: str, start: float, model: str
    ) -> ResearchResult:
        # 3-call refinement chain
        # Call 1: initial research
        # Call 2: gap identification
        # Call 3: synthesis
        # ...

    async def _deep_research(
        self, topic: str, start: float, model: str
    ) -> ResearchResult:
        # Native deep research or fallback to _standard_research
        # ...
```

## Error Handling Contract

**Critical:** Providers must never raise exceptions from `research()`. All errors become `ResearchResult.error` strings.

**The wrapping `_safe_research()` method catches any exceptions that escape**, but it's better to handle them in `research()` so error messages are more specific.

**Example:**

```python
async def research(self, topic: str, depth: Depth) -> ResearchResult:
    start = time.monotonic()
    model = "my-model"
    
    try:
        # API call
        response = await self.client.call(topic)
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
            error=f"ValidationError: {exc}",  # Specific error message
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

## Testing

When adding a new provider, test:

1. **Availability check:** `MyProvider().available` returns `True` when API key is set, `False` otherwise
2. **Quick research:** Returns `ResearchResult` with content in <1 minute
3. **Standard research:** Returns structured response with multiple paragraphs
4. **Timeout handling:** Graceful degradation if request exceeds depth timeout
5. **Rate limit retry:** Returns success after transient 429 errors
6. **Auth failure:** Returns `ResearchResult` with auth error (never raises)
7. **Malformed response:** Returns error, never crashes on unexpected API response shape
