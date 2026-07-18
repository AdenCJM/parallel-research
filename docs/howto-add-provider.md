# How to Add a Provider

Add `src/parallel_research/providers/<name>.py` and implement `BaseProvider` as documented in the
[provider API reference](reference-baseprovider-api.md).

Register it in `src/parallel_research/providers/__init__.py`:

```python
ALL_PROVIDERS = {
    # existing providers
    "example": ExampleProvider,
}
```

## Implementation checklist

1. Read the provider's current official API documentation.
2. Use its native grounding or search capability.
3. Make model names configurable through environment variables.
4. Bound output tokens, searches, reasoning effort, or tool calls where supported.
5. Convert citations into `Citation` objects.
6. Convert reported usage into `Usage`.
7. Persist background request IDs through the progress callback.
8. Implement `resume` only when the API can retrieve the original request.
9. Let `safe_research` handle top-level isolation and secret redaction.

## Test without spending money

Add mocked SDK contract tests and include the provider in a fake-registry orchestration test. Cover:

- missing credentials;
- grounded success with citations;
- transient retry;
- authentication failure;
- empty response;
- local timeout;
- background request persistence and resume, when supported; and
- credentials embedded in exception text.

Run the full suite:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
uv build
```

Do not add live API calls to default tests. A manual provider smoke test should use an explicit
topic, provider subset, and budget.
