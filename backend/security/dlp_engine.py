"""Data Loss Prevention (DLP) & Secret Scanner for AEGIS."""

from __future__ import annotations

import re
from typing import TypedDict


class DLPFinding(TypedDict):
    category: str
    match: str
    start: int
    end: int


class DLPResult(TypedDict):
    has_sensitive_data: bool
    findings: list[DLPFinding]
    sanitized_text: str


SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("OPENAI_API_KEY", re.compile(r"\bsk-[a-zA-Z0-9_\-]{32,}\b")),
    ("SLACK_TOKEN", re.compile(r"\bxox[baprs]-[0-9a-zA-Z]{10,48}\b")),
    ("GITHUB_TOKEN", re.compile(r"\bghp_[0-9a-zA-Z]{36}\b")),
    (
        "JWT_TOKEN",
        re.compile(
            r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"
        ),
    ),
    (
        "PRIVATE_KEY",
        re.compile(r"-----BEGIN\s+([A-Z\s]+)?PRIVATE KEY-----"),
    ),
    (
        "CREDIT_CARD",
        re.compile(
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b"
        ),
    ),
    ("US_SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
]


def scan_for_secrets(text: str | None) -> DLPResult:
    """Scan text for API keys, credentials, tokens, and PII.

    Returns whether sensitive data was discovered, the list of findings,
    and a redacted sanitized string suitable for safe logging.
    """
    if not text:
        return {
            "has_sensitive_data": False,
            "findings": [],
            "sanitized_text": "",
        }

    findings: list[DLPFinding] = []
    sanitized = text

    for category, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            val = match.group(0)
            findings.append(
                {
                    "category": category,
                    "match": val[:4] + "..." + val[-2:] if len(val) > 8 else "***",
                    "start": match.start(),
                    "end": match.end(),
                }
            )
            # Redact in sanitized output
            replacement = f"[{category}_REDACTED]"
            sanitized = pattern.sub(replacement, sanitized)

    return {
        "has_sensitive_data": len(findings) > 0,
        "findings": findings,
        "sanitized_text": sanitized,
    }
