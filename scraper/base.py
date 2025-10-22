"""Base classes and helpers for site scrapers."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Iterator, List, Optional, Sequence
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from .utils import normalize_ticket_metrics

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ScrapedCompetition:
    """Normalized representation of a competition listing."""

    title: str
    prize: str
    price: Optional[Decimal]
    tickets_total: Optional[int]
    tickets_sold: Optional[int]
    tickets_remaining: Optional[int]
    sold_ratio: Optional[float]
    deadline: Optional[str]
    url: str
    source: str


class SiteScraper(ABC):
    """Abstract base class for scraping competition listing pages."""

    #: Default timeout (seconds) for HTTP requests.
    timeout: int = 20
    #: Default headers for HTTP requests.
    headers: dict = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/117.0 Safari/537.36"
        )
    }

    def __init__(self, session: Optional[requests.Session] = None, *, now: Optional[datetime] = None) -> None:
        self.session = session or requests.Session()
        self._now = now

    @property
    @abstractmethod
    def source(self) -> str:
        """Human-friendly name of the site."""

    @property
    @abstractmethod
    def listing_urls(self) -> Sequence[str]:
        """Return one or more URLs containing competition listings."""

    def scrape(self) -> List[ScrapedCompetition]:
        """Scrape all listings and return normalized competition details."""

        competitions: List[ScrapedCompetition] = []
        for listing_url in self.listing_urls:
            logger.debug("Scraping listing URL: %s", listing_url)
            for soup, page_url in self._iterate_pages(listing_url):
                competitions.extend(self.parse_listing_page(soup, page_url))
        return competitions

    def _iterate_pages(self, url: str) -> Iterator[tuple[BeautifulSoup, str]]:
        seen: set[str] = set()
        next_url: Optional[str] = url
        while next_url and next_url not in seen:
            seen.add(next_url)
            response = self.session.get(next_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            yield soup, next_url
            next_url = self.get_next_page_url(soup, next_url)

    def parse_listing_page(self, soup: BeautifulSoup, page_url: str) -> List[ScrapedCompetition]:
        """Parse competitions from a listing page."""

        competitions: List[ScrapedCompetition] = []
        for card in self.iter_competition_cards(soup):
            competitions.append(self._build_competition(card, page_url))
        return competitions

    @abstractmethod
    def iter_competition_cards(self, soup: BeautifulSoup) -> Iterable[Tag]:
        """Yield elements representing individual competitions."""

    @abstractmethod
    def extract_title(self, card: Tag) -> str:
        """Extract the competition title from a card element."""

    @abstractmethod
    def extract_prize(self, card: Tag) -> str:
        """Extract the prize description from a card element."""

    @abstractmethod
    def extract_price(self, card: Tag) -> Optional[Decimal]:
        """Extract the ticket price from a card element."""

    @abstractmethod
    def extract_competition_url(self, card: Tag, page_url: str) -> str:
        """Return an absolute URL to the competition detail page."""

    @abstractmethod
    def extract_ticket_totals(self, card: Tag) -> tuple[Optional[int], Optional[int], Optional[int]]:
        """Return (sold, remaining, total) tickets for the competition."""

    @abstractmethod
    def extract_deadline(self, card: Tag) -> Optional[str]:
        """Return the ISO-formatted deadline for the competition."""

    def get_next_page_url(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """Return the URL for the next page, if any."""

        rel_next = soup.select_one("a[rel='next'], a.pagination__next, a.next")
        if rel_next and rel_next.get("href"):
            href = rel_next["href"].strip()
            return urljoin(current_url, href)
        return None

    def _build_competition(self, card: Tag, page_url: str) -> ScrapedCompetition:
        title = self.extract_title(card)
        prize = self.extract_prize(card)
        price = self.extract_price(card)
        sold, remaining, total = self.extract_ticket_totals(card)
        metrics = normalize_ticket_metrics(total=total, sold=sold, remaining=remaining)
        deadline = self.extract_deadline(card)
        url = self.extract_competition_url(card, page_url)
        return ScrapedCompetition(
            title=title,
            prize=prize,
            price=price,
            tickets_total=metrics.total,
            tickets_sold=metrics.sold,
            tickets_remaining=metrics.remaining,
            sold_ratio=metrics.sold_ratio,
            deadline=deadline,
            url=url,
            source=self.source,
        )

    def to_absolute_url(self, base_url: str, href: str) -> str:
        return urljoin(base_url, href)


__all__ = ["SiteScraper", "ScrapedCompetition"]
