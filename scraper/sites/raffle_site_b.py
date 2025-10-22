"""Scraper for the fictional "Raffle Site B" relying on Playwright."""

from __future__ import annotations

import contextlib
import logging
from datetime import datetime
from typing import Iterable, List

from ..base import BaseScraper
from ..models import RaffleEntry

try:  # pragma: no cover - optional dependency
    from playwright.sync_api import Browser, Page, sync_playwright
except Exception:  # pragma: no cover - optional dependency
    Browser = Page = None  # type: ignore
    sync_playwright = None

logger = logging.getLogger(__name__)


class RaffleSiteBScraper(BaseScraper):
    """Scrape raffle listings rendered dynamically via JavaScript."""

    url = "https://raffle-site-b.example.com/dashboard"
    selector = "section.raffle"

    def fetch(self) -> List[str]:
        if sync_playwright is None:
            raise RuntimeError(
                "Playwright is required to scrape Raffle Site B. Install playwright and"
                " browsers to enable this scraper."
            )

        html_pages: List[str] = []
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            try:
                page = browser.new_page()
                logger.debug("Navigating to %s", self.url)
                page.goto(self.url, wait_until="networkidle")
                cards = page.query_selector_all(self.selector)
                for card in cards:
                    html_pages.append(card.inner_html())
            finally:
                with contextlib.suppress(Exception):
                    browser.close()
        return html_pages

    def parse(self, payload: List[str]) -> Iterable[RaffleEntry]:
        for html in payload:
            data = self._extract_fields(html)
            if data:
                yield data

    def _extract_fields(self, html: str) -> RaffleEntry | None:
        """Very small HTML snippet parser relying on simple string operations."""

        from bs4 import BeautifulSoup  # Local import to avoid mandatory dependency.

        soup = BeautifulSoup(html, "html.parser")
        title_node = soup.select_one("h3.name")
        prize_node = soup.select_one("span.reward")
        if not title_node or not prize_node:
            logger.debug("Skipping incomplete raffle card: %s", html)
            return None
        ticket_node = soup.select_one("span.remaining")
        price_node = soup.select_one("span.price")
        deadline_node = soup.select_one("time.deadline")
        url_node = soup.select_one("a.details")
        return RaffleEntry(
            title=title_node.get_text(strip=True),
            prize=prize_node.get_text(strip=True),
            ticket_count=self._parse_optional_int(ticket_node),
            price=self._parse_optional_float(price_node),
            deadline=self._parse_optional_deadline(deadline_node),
            url=url_node["href"] if url_node else self.url,
        )

    def _parse_optional_int(self, node) -> int | None:
        if not node:
            return None
        try:
            return int(node.get_text(strip=True).split()[0])
        except ValueError:
            logger.debug("Failed to parse integer from %s", node)
            return None

    def _parse_optional_float(self, node) -> float | None:
        if not node:
            return None
        text = node.get_text(strip=True).replace("$", "").replace(",", "")
        try:
            return float(text)
        except ValueError:
            logger.debug("Failed to parse float from %s", node)
            return None

    def _parse_optional_deadline(self, node) -> datetime | None:
        if not node:
            return None
        raw = node.get("datetime") or node.get_text(strip=True)
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            logger.debug("Failed to parse deadline from %s", raw)
            return None
