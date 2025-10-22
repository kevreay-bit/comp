"""Scrapers for Shopify-powered competition sites."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Optional, Sequence
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from ..base import SiteScraper
from ..utils import parse_countdown_text, parse_int


@dataclass(slots=True)
class ShopifySelectors:
    """CSS selectors required to extract competition attributes."""

    card: str = "article.product-card, div.product-card, div.card--standard"
    link: Sequence[str] = field(
        default_factory=lambda: (
            "a.product-card__link",
            "a.full-unstyled-link",
            "a.card__information",
            "a[href]",
        )
    )
    title: Sequence[str] = field(
        default_factory=lambda: (
            ".product-card__title",
            ".card__heading",
            ".product-item__title",
            "h3",
        )
    )
    prize: Sequence[str] = field(
        default_factory=lambda: (
            ".product-card__subtitle",
            ".product-card__title",
            ".card__heading",
        )
    )
    price: Sequence[str] = field(
        default_factory=lambda: (
            ".price-item--regular",
            ".product-price",
            "span.money",
        )
    )
    deadline: Sequence[str] = field(
        default_factory=lambda: (
            ".product-card__countdown",
            ".countdown",
            ".card__countdown",
        )
    )
    sold: Sequence[str] = field(
        default_factory=lambda: (
            "[data-sold]",
            "[data-progress-sold]",
            ".progress__sold",
            ".sold-count",
        )
    )
    remaining: Sequence[str] = field(
        default_factory=lambda: (
            "[data-remaining]",
            ".progress__remaining",
            ".remaining-count",
        )
    )
    total: Sequence[str] = field(
        default_factory=lambda: (
            "[data-total]",
            "[data-total-tickets]",
            "[data-progress-total]",
            ".total-count",
        )
    )


class ShopifyStoreScraper(SiteScraper):
    """Generic scraper for Shopify collection listing pages."""

    def __init__(
        self,
        *,
        store_domain: str,
        collection_path: str = "/collections/all",
        selectors: Optional[ShopifySelectors] = None,
        session: Optional[requests.Session] = None,
        now: Optional[datetime] = None,
    ) -> None:
        super().__init__(session=session, now=now)
        self.store_domain = store_domain.rstrip("/")
        self.collection_path = collection_path or "/collections/all"
        self.selectors = selectors or ShopifySelectors()

    @property
    def source(self) -> str:  # pragma: no cover - simple property
        return self.store_domain

    @property
    def listing_urls(self) -> Sequence[str]:
        base = f"https://{self.store_domain}" if not self.store_domain.startswith("http") else self.store_domain
        return [urljoin(base + "/", self.collection_path.lstrip("/"))]

    def iter_competition_cards(self, soup: BeautifulSoup) -> Iterable[Tag]:
        return soup.select(self.selectors.card)

    # Helper utilities -------------------------------------------------
    def _first_text(self, card: Tag, selectors: Sequence[str], default: str = "") -> str:
        for selector in selectors:
            node = card.select_one(selector)
            if node:
                text = node.get_text(strip=True)
                if text:
                    return text
        return default

    def _first_href(self, card: Tag, selectors: Sequence[str]) -> Optional[str]:
        for selector in selectors:
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

    def _extract_metric_from_nodes(self, card: Tag, selectors: Sequence[str], *attribute_names: str) -> Optional[int]:
        for selector in selectors:
            node = card.select_one(selector)
            if not node:
                continue
            for attribute in attribute_names:
                if node.has_attr(attribute):
                    parsed = parse_int(str(node[attribute]))
                    if parsed is not None:
                        return parsed
            parsed = parse_int(node.get_text(" ", strip=True))
            if parsed is not None:
                return parsed
        return None

    def _extract_metric_from_card(self, card: Tag, *attribute_names: str) -> Optional[int]:
        for attribute in attribute_names:
            if card.has_attr(attribute):
                parsed = parse_int(str(card[attribute]))
                if parsed is not None:
                    return parsed
        return None

    # Extraction methods -----------------------------------------------
    def extract_title(self, card: Tag) -> str:
        return self._first_text(card, self.selectors.title)

    def extract_prize(self, card: Tag) -> str:
        prize = self._first_text(card, self.selectors.prize)
        return prize or self.extract_title(card)

    def extract_price(self, card: Tag) -> Optional[Decimal]:
        text = self._first_text(card, self.selectors.price)
        return self._parse_price(text) if text else None

    def extract_competition_url(self, card: Tag, page_url: str) -> str:
        href = self._first_href(card, self.selectors.link) or ""
        return self.to_absolute_url(page_url, href)

    def extract_ticket_totals(self, card: Tag) -> tuple[Optional[int], Optional[int], Optional[int]]:
        sold = self._extract_metric_from_card(
            card, "data-sold", "data-sold-tickets", "data-progress-sold"
        )
        remaining = self._extract_metric_from_card(
            card, "data-remaining", "data-remaining-tickets"
        )
        total = self._extract_metric_from_card(
            card, "data-total", "data-total-tickets", "data-progress-total"
        )

        if sold is None:
            sold = self._extract_metric_from_nodes(
                card,
                self.selectors.sold,
                "data-sold",
                "data-progress-sold",
                "data-tickets-sold",
            )
        if remaining is None:
            remaining = self._extract_metric_from_nodes(
                card,
                self.selectors.remaining,
                "data-remaining",
                "data-tickets-remaining",
            )
        if total is None:
            total = self._extract_metric_from_nodes(
                card,
                self.selectors.total,
                "data-total",
                "data-total-tickets",
                "data-progress-total",
            )

        return sold, remaining, total

    def extract_deadline(self, card: Tag) -> Optional[str]:
        text = self._first_text(card, self.selectors.deadline)
        return parse_countdown_text(text, now=self._now) if text else None


class DreamCarGiveawaysScraper(ShopifyStoreScraper):
    """Scraper implementation for dreamcargiveaways.co.uk."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(store_domain="dreamcargiveaways.co.uk", **kwargs)

