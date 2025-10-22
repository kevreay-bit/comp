"""Scraper for RafflePress style competition listings."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Iterable, Optional, Sequence
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from ..base import SiteScraper
from ..utils import parse_countdown_text, parse_int


class RafflePressScraper(SiteScraper):
    """Scrape RafflePress (WordPress) competition listing pages."""

    card_selector = ".rafflepress-contest, .rafflepress-listing, .rafflepress-giveaway"
    title_selectors: Sequence[str] = (
        ".rafflepress-title",
        "h2",
        "h3",
    )
    prize_selectors: Sequence[str] = (
        ".rafflepress-prize",
        ".rafflepress-title",
    )
    price_selectors: Sequence[str] = (
        ".rafflepress-price",
        ".ticket-price",
        "[data-price]",
    )
    deadline_selectors: Sequence[str] = (
        "[data-end]",
        ".rafflepress-countdown",
        ".countdown",
    )
    link_selectors: Sequence[str] = (
        "a.rafflepress-button",
        "a[href]",
    )
    sold_selectors: Sequence[str] = (
        "[data-sold]",
        ".rafflepress-progress__sold",
        ".rafflepress-sold",
    )
    remaining_selectors: Sequence[str] = (
        "[data-remaining]",
        ".rafflepress-progress__remaining",
        ".rafflepress-remaining",
    )
    total_selectors: Sequence[str] = (
        "[data-total]",
        "[data-max]",
        ".rafflepress-progress__total",
    )

    def __init__(
        self,
        *,
        base_url: str,
        listing_path: str,
        session: Optional[requests.Session] = None,
        now: Optional[datetime] = None,
    ) -> None:
        super().__init__(session=session, now=now)
        self.base_url = base_url.rstrip("/")
        self.listing_path = listing_path

    @property
    def source(self) -> str:  # pragma: no cover - trivial
        return self.base_url

    @property
    def listing_urls(self) -> Sequence[str]:
        return [urljoin(self.base_url + "/", self.listing_path.lstrip("/"))]

    def iter_competition_cards(self, soup: BeautifulSoup) -> Iterable[Tag]:
        return soup.select(self.card_selector)

    # Helpers ----------------------------------------------------------
    def _first_text(self, card: Tag, selectors: Sequence[str]) -> str:
        for selector in selectors:
            node = card.select_one(selector)
            if node:
                text = node.get_text(strip=True)
                if text:
                    return text
        return ""

    def _first_href(self, card: Tag) -> Optional[str]:
        for selector in self.link_selectors:
            node = card.select_one(selector)
            if node and node.has_attr("href"):
                return node["href"]
        return None

    def _parse_price(self, text: str) -> Optional[Decimal]:
        cleaned = "".join(ch for ch in text if ch.isdigit() or ch in ".,")
        if not cleaned:
            return None
        normalized = cleaned.replace(",", "")
        try:
            return Decimal(normalized)
        except ArithmeticError:
            return None

    def extract_title(self, card: Tag) -> str:
        return self._first_text(card, self.title_selectors)

    def extract_prize(self, card: Tag) -> str:
        prize = self._first_text(card, self.prize_selectors)
        return prize or self.extract_title(card)

    def extract_price(self, card: Tag) -> Optional[Decimal]:
        text = self._first_text(card, self.price_selectors)
        return self._parse_price(text) if text else None

    def extract_competition_url(self, card: Tag, page_url: str) -> str:
        href = self._first_href(card) or ""
        return self.to_absolute_url(page_url, href)

    def extract_ticket_totals(self, card: Tag) -> tuple[Optional[int], Optional[int], Optional[int]]:
        sold = self._extract_metric(card, self.sold_selectors, "data-sold")
        remaining = self._extract_metric(card, self.remaining_selectors, "data-remaining")
        total = self._extract_metric(card, self.total_selectors, "data-total", "data-max")
        return sold, remaining, total

    def extract_deadline(self, card: Tag) -> Optional[str]:
        # Prefer explicit data-end attributes if present.
        for selector in self.deadline_selectors:
            node = card.select_one(selector)
            if not node:
                continue
            if node.has_attr("data-end"):
                parsed = parse_countdown_text(node["data-end"], now=self._now)
                if parsed:
                    return parsed
            text = node.get_text(strip=True)
            if text:
                parsed = parse_countdown_text(text, now=self._now)
                if parsed:
                    return parsed
        return None

    def get_next_page_url(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        # RafflePress often uses numbered pagination links.
        rel_next = soup.select_one("a.next, a[rel='next'], .pagination a.next")
        if rel_next and rel_next.get("href"):
            return urljoin(current_url, rel_next["href"].strip())
        return None

    def _extract_metric(
        self, card: Tag, selectors: Sequence[str], *attribute_names: str
    ) -> Optional[int]:
        for selector in selectors:
            node = card.select_one(selector)
            if not node:
                continue
            for attribute in attribute_names:
                if node.has_attr(attribute):
                    parsed = parse_int(str(node[attribute]))
                    if parsed is not None:
                        return parsed
            text = node.get_text(" ", strip=True)
            parsed = parse_int(text)
            if parsed is not None:
                return parsed
        return None

