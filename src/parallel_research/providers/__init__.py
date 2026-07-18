from .base import BaseProvider
from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .openai_provider import OpenAIProvider
from .perplexity import PerplexityProvider

ALL_PROVIDERS: dict[str, type[BaseProvider]] = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "perplexity": PerplexityProvider,
}

__all__ = ["ALL_PROVIDERS", "BaseProvider"]
