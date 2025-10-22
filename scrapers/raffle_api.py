"""Scraper for custom raffle APIs that require JavaScript rendering."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional

from .base import Scraper, ScraperResult
from .playwright_fetcher import PlaywrightFetcher
from .utils import discover_json_endpoints

logger = logging.getLogger(__name__)


class RaffleAPIScraper(Scraper):
    """Scrape bespoke raffle APIs that expose data after JS execution."""

    def __init__(
        self,
        url: str,
        *,
        wait_for_selector: str = "[data-raffle]",
        playwright_fetcher: Optional[PlaywrightFetcher] = None,
    ) -> None:
        super().__init__(url)
        self.wait_for_selector = wait_for_selector
        self.playwright_fetcher = playwright_fetcher or PlaywrightFetcher()

    def run(self) -> ScraperResult:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.run_async())
        raise RuntimeError(
            "RaffleAPIScraper.run() cannot be invoked while an event loop is running; "
            "use run_async() instead."
        )

    async def run_async(self) -> ScraperResult:
        html = self.fetch_html()
        endpoints = discover_json_endpoints(html, self.url)
        for endpoint in endpoints:
            try:
                payload = self.fetch_json(endpoint)
            except Exception as exc:
                logger.debug("Failed JSON endpoint %s: %s", endpoint, exc)
                continue
            result = self._parse_payload(payload)
            if result:
                return result

        logger.debug("Falling back to Playwright for %s", self.url)
        rendered = await self.playwright_fetcher.fetch(
            self.url, wait_for_selector=self.wait_for_selector, use_cache=True
        )
        return self._parse_rendered_html(rendered)

    def _parse_payload(self, payload: Any) -> Optional[ScraperResult]:
        if isinstance(payload, dict):
            if "tickets" in payload and "deadline" in payload:
                return ScraperResult(
                    tickets_remaining=_safe_int(payload.get("tickets")),
                    deadline=_parse_datetime(payload.get("deadline")),
                    metadata=payload,
                )
        if isinstance(payload, list):
            for entry in payload:
                result = self._parse_payload(entry)
                if result:
                    return result
        return None

    def _parse_rendered_html(self, html: str) -> ScraperResult:
        data = self._extract_json_from_html(html)
        if data:
            result = self._parse_payload(data)
            if result:
                return result
        logger.warning("Unable to locate raffle data for %s", self.url)
        return ScraperResult(tickets_remaining=None, deadline=None, metadata={})

    def _extract_json_from_html(self, html: str) -> Optional[Any]:
        try:
            marker = "data-raffle-json"
            start = html.index(marker)
            start = html.index("{", start)
            end = html.index("</", start)
            snippet = html[start:end]
            return json.loads(snippet)
        except (ValueError, json.JSONDecodeError):
            logger.debug("Failed to parse embedded JSON for %s", self.url)
            return None


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _safe_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
