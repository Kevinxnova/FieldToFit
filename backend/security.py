"""Small, framework-independent helpers for protecting privileged endpoints."""

from __future__ import annotations

import hmac
import os
from urllib.parse import urlsplit, urlunsplit


def allowed_origins() -> set[str]:
    """Explicit origins only. Never trust the incoming Host header as an allowlist."""
    origins = {x.strip().rstrip('/') for x in os.getenv('ALLOWED_ORIGINS', os.getenv('FRONTEND_URL', 'http://localhost:5173')).split(',') if x.strip()}
    for origin in list(origins):
        parsed = urlsplit(origin)
        if parsed.hostname in {'localhost', '127.0.0.1'}:
            alternate = '127.0.0.1' if parsed.hostname == 'localhost' else 'localhost'
            if parsed.port:
                alternate += ':' + str(parsed.port)
            origins.add(urlunsplit((parsed.scheme, alternate, '', '', '')))
    return origins


def secret_is_configured(name: str) -> bool:
    """Return whether a non-empty secret exists in the environment."""
    return bool(os.getenv(name, "").strip())


def secret_matches(provided: str | None, name: str) -> bool:
    """Compare a provided value with an environment secret in constant time."""
    expected = os.getenv(name, "").strip()
    candidate = (provided or "").strip()
    return bool(expected and candidate and hmac.compare_digest(candidate, expected))


def bearer_matches(authorization: str | None, name: str = "CRON_SECRET") -> bool:
    """Validate an Authorization: Bearer header against an environment secret."""
    expected = os.getenv(name, "").strip()
    candidate = authorization or ""
    return bool(
        expected
        and hmac.compare_digest(candidate, f"Bearer {expected}")
    )
