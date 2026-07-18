# Reference: BaseProvider API

Providers inherit from `parallel_research.providers.base.BaseProvider`.

## Required members

```python
class ExampleProvider(BaseProvider):
    name = "example"

    @property
    def available(self) -> bool:
        ...

    async def research(
        self,
        topic: str,
        depth: Depth,
        progress: ProgressCallback | None = None,
    ) -> ResearchResult:
        ...
```

`available` reports whether required credentials are configured. `research` should return a
`ResearchResult`; `safe_research` supplies timeout, cancellation, redaction, and failure isolation.

## ResearchResult

```python
ResearchResult(
    provider="example",
    model="example-grounded-1",
    content="...",
    duration_seconds=1.2,
    status=RunStatus.SUCCEEDED,
    citations=[Citation(url="https://example.org")],
    usage=Usage(input_tokens=10, output_tokens=100),
    request_id="request-id",
)
```

Use `RunStatus.RESUMABLE` only when `request_id` identifies retrievable remote work. Override
`resume` for providers that support retrieval without duplicate submission.

## Progress callback

Call the asynchronous progress callback immediately after receiving a background request ID:

```python
await progress({
    "status": RunStatus.RUNNING,
    "request_id": response.id,
    "model": model,
})
```

This persists the handle before long polling begins.

## Retry behavior

Use `with_retries` around SDK calls. It retries bounded transient conditions such as rate limits,
timeouts, connection failures, and selected server status codes. It does not retry validation or
authentication errors.

## Provider requirements

A production provider must:

- use grounded retrieval for research modes;
- extract inspectable citations where exposed;
- apply real output/search controls where supported;
- preserve remote request IDs;
- avoid logging credentials;
- return untrusted response text without executing it; and
- include mocked contract tests that make no billable requests.

See [adding a provider](howto-add-provider.md).
