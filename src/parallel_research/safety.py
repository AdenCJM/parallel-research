from __future__ import annotations

import re

_SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)((?:api[_-]?key|x-api-key)\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"\b(?:sk-(?:ant-|proj-)?|pplx-|AIza)[A-Za-z0-9_\-]{12,}\b"),
)


def redact_secrets(value: object) -> str:
    """Return an error-safe string with common credentials removed."""
    text = str(value)
    for pattern in _SECRET_PATTERNS:
        if pattern.groups:
            text = pattern.sub(r"\1[REDACTED]", text)
        else:
            text = pattern.sub("[REDACTED]", text)
    return text[:2000]
