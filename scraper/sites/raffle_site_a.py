"""Scraper for the fictional "Raffle Site A" using requests + BeautifulSoup."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable, List

from bs4 import BeautifulSoup  # type: ignore

from ..base import BaseScraper
from ..models import RaffleEntry

logger = logging.getLogger(__name__)


class RaffleSiteAScraper(BaseScraper):
    """Scrape paginated raffle listings rendered on the server."""

    base_url = "https://raffle-site-a.example.com/raffles"
    pagination_param = "page"
    max_pages = 10

    def __init__(self, *, max_pages: int | None = None) -> None:
        super().__init__()
        if max_pages is not None:
            self.max_pages = max_pages

    def fetch(self) -> List[str]:
        payloads: List[str] = []
        for page in range(1, self.max_pages + 1):
            url = f"{self.base_url}?{self.pagination_param}={page}"
            logger.debug("Fetching %s", url)
            response = self.request_with_retry(url)
            payloads.append(response.text)
            if not self._has_next_page(response):
                break
        return payloads

    def parse(self, payload: List[str]) -> Iterable[RaffleEntry]:
        for html in payload:
            soup = BeautifulSoup(html, "html.parser")
            for card in soup.select("div.raffle-card"):
                try:
                    entry = self._parse_card(card)
                    logger.debug("Parsed entry: %s", entry)
                    yield entry
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("Failed to parse card: %s", exc, exc_info=True)

    # Internal helpers -------------------------------------------------
    def _has_next_page(self, response) -> bool:
        soup = self.soup_from_response(response)
        next_button = soup.select_one("a.pagination-next")
        return bool(next_button and "disabled" not in next_button.get("class", []))

    def _parse_card(self, card: BeautifulSoup) -> RaffleEntry:
        title = card.select_one("h2.title").get_text(strip=True)
        prize = card.select_one("p.prize").get_text(strip=True)
        ticket_count = self._parse_int(card.select_one("span.tickets"))
        price = self._parse_price(card.select_one("span.price"))
        deadline = self._parse_deadline(card.select_one("time.deadline"))
        url = card.select_one("a.cta")['href']  # type: ignore[index]
        return RaffleEntry(
            title=title,
            prize=prize,
            ticket_count=ticket_count,
            price=price,
            deadline=deadline,
            url=url,
        )

    def _parse_int(self, node) -> int | None:
        if not node:
            return None
        try:
            return int(node.get_text(strip=True).replace(",", ""))
        except ValueError:
            logger.debug("Unable to parse int from %s", node)
            return None

    def _parse_price(self, node) -> float | None:
        if not node:
            return None
        text = node.get_text(strip=True).replace("$", "").replace(",", "")
        try:
            return float(text)
        except ValueError:
            logger.debug("Unable to parse price from %s", node)
            return None

    def _parse_deadline(self, node) -> datetime | None:
        if not node:
            return None
        date_text = node.get("datetime") or node.get_text(strip=True)
        try:
            return datetime.fromisoformat(date_text)
        except ValueError:
            logger.debug("Unable to parse datetime from %s", date_text)
            return None
