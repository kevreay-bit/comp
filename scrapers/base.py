"""Base classes and utilities for raffle scrapers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List

from raffles.models import RaffleRecord


class BaseScraper(ABC):
    """Interface all raffle scrapers should implement."""

    source: str

    @abstractmethod
    def fetch(self) -> Iterable[RaffleRecord]:
        """Return raffle records gathered by the scraper."""

    def collect(self) -> List[RaffleRecord]:
        """Collect raffle records as a list."""

        return list(self.fetch())


__all__ = ["BaseScraper"]
