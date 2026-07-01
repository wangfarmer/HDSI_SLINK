from __future__ import annotations

import re
from html import unescape
from urllib.parse import urljoin, urlparse


WHITESPACE_RE = re.compile(r"\s+")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = unescape(value)
    text = WHITESPACE_RE.sub(" ", text).strip()
    return text or None


def absolute_url(base_url: str, maybe_url: str | None) -> str | None:
    if not maybe_url:
        return None
    return urljoin(base_url, maybe_url)


def domain_allowed(url: str, allowed_domains: list[str]) -> bool:
    hostname = urlparse(url).hostname or ""
    return hostname in allowed_domains


def matches_any(value: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, value) for pattern in patterns)


def first_email(text: str | None) -> str | None:
    if not text:
        return None
    match = EMAIL_RE.search(text)
    return match.group(0) if match else None


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
