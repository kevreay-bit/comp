"""Utility helpers shared across scrapers."""

from __future__ import annotations

import re
from typing import Iterable, List, Optional
from urllib.parse import urljoin

_JSON_ENDPOINT_CANDIDATES = (
    re.compile(r"(?:src|href)=\"([^\"]+\.json)\"", re.IGNORECASE),
    re.compile(r"/raffles?(?:/api)?", re.IGNORECASE),
    re.compile(r"data-endpoint=\"([^\"]+)\"", re.IGNORECASE),
)


def discover_json_endpoints(html: str, base_url: str) -> List[str]:
    """Identify likely JSON endpoints embedded in the HTML source."""

    matches: List[str] = []
    for pattern in _JSON_ENDPOINT_CANDIDATES:
        for match in pattern.finditer(html):
            endpoint = _extract_endpoint(match)
            if not endpoint:
                continue
            absolute = urljoin(base_url, endpoint)
            if absolute not in matches:
                matches.append(absolute)
    return matches


def _extract_endpoint(match: re.Match[str]) -> Optional[str]:
    if match.lastindex:
        return match.group(match.lastindex)
    return match.group(0)


def iter_json_candidates(base_url: str, slugs: Iterable[str]) -> Iterable[str]:
    """Yield additional Shopify-style JSON endpoints for a base URL."""

    for slug in slugs:
        yield urljoin(base_url, f"/collections/{slug}/products.json")
        yield urljoin(base_url, f"/{slug}.json")
