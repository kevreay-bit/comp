"""Base classes and utilities shared by scraper implementations."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Iterable, Sequence

import requests
from bs4 import BeautifulSoup  # type: ignore

from .models import RaffleEntry
from .pipeline import raffle_queue

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base scraper exposing fetch/parse hooks and orchestration logic."""

    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    )
    max_retries = 3
    backoff_factor = 1.5
    timeout = 15

    def __init__(self, *, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", self.user_agent)
        self.queue = raffle_queue

    def run(self) -> Sequence[RaffleEntry]:
        """Execute the scraper and push normalized data into the queue."""

        try:
            logger.info("Running scraper %s", self.__class__.__name__)
            raw_payload = self.fetch()
            entries = list(self.parse(raw_payload))
            self.queue.extend(entries)
            logger.info("%s scraped %d entries", self.__class__.__name__, len(entries))
            return entries
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Scraper %s failed: %s", self.__class__.__name__, exc)
            raise

    @abstractmethod
    def fetch(self) -> object:
        """Collect raw payload from the upstream service."""

    @abstractmethod
    def parse(self, payload: object) -> Iterable[RaffleEntry]:
        """Transform raw payload into :class:`RaffleEntry` instances."""

    # Helper methods -----------------------------------------------------
    def request_with_retry(self, url: str, *, method: str = "GET", **kwargs) -> requests.Response:
        """Perform an HTTP request with basic retry logic."""

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug("%s request attempt %d to %s", method, attempt, url)
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as exc:  # pragma: no cover - network
                last_error = exc
                wait_time = self.backoff_factor ** attempt
                logger.warning(
                    "Request attempt %d failed for %s: %s. Retrying in %.1fs",
                    attempt,
                    url,
                    exc,
                    wait_time,
                )
                time.sleep(wait_time)
        assert last_error is not None  # for type checkers
        logger.error("All retries exhausted for %s", url)
        raise last_error

    @staticmethod
    def soup_from_response(response: requests.Response) -> BeautifulSoup:
        return BeautifulSoup(response.text, "html.parser")


__all__ = ["BaseScraper"]
