"""Base classes and helpers for raffle scrapers."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

try:  # pragma: no cover - fallback for minimal environments
    import requests  # type: ignore
except ImportError:  # pragma: no cover
    import urllib.error
    import urllib.request

    class _Response:
        def __init__(self, url: str, status_code: int, data: bytes) -> None:
            self.url = url
            self.status_code = status_code
            self._data = data

        def raise_for_status(self) -> None:
            if not 200 <= self.status_code < 400:
                raise urllib.error.HTTPError(self.url, self.status_code, "", None, None)

        @property
        def text(self) -> str:
            return self._data.decode("utf-8", errors="replace")

        def json(self) -> Any:
            return json.loads(self.text)

    class _Session:
        def __init__(self) -> None:
            self.headers: Dict[str, str] = {}

        def get(self, url: str, timeout: float = 15.0) -> _Response:
            request = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
                status_code = getattr(response, "status", 200)
            return _Response(url, status_code, data)

    class _RequestsModule:
        Session = _Session

    requests = _RequestsModule()  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class ScraperResult:
    """Represents the structured data returned by a scraper."""

    tickets_remaining: Optional[int]
    deadline: Optional[datetime]
    metadata: Dict[str, Any] = field(default_factory=dict)


class Scraper(ABC):
    """Abstract base class for raffle scrapers."""

    def __init__(self, url: str, session: Optional[Any] = None) -> None:
        self.url = url
        self.session = session or requests.Session()
        self.session.headers.setdefault(
            "User-Agent",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        )

    def fetch_html(self, *, timeout: float = 15.0) -> str:
        """Fetch the raw HTML for the scraper's URL."""

        logger.debug("Fetching HTML for %s", self.url)
        response = self.session.get(self.url, timeout=timeout)
        response.raise_for_status()
        return response.text

    def fetch_json(self, endpoint: str, *, timeout: float = 15.0) -> Any:
        """Fetch JSON data for a related endpoint."""

        logger.debug("Fetching JSON from %s", endpoint)
        response = self.session.get(endpoint, timeout=timeout)
        response.raise_for_status()
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            logger.exception("Failed to decode JSON from %s", endpoint)
            raise ValueError(f"Endpoint {endpoint} did not return valid JSON") from exc

    @abstractmethod
    def run(self) -> ScraperResult:
        """Execute the scraper and return structured data."""

        raise NotImplementedError
