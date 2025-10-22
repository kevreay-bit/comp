"""Scraper implementation for Shopify-based raffles."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urljoin

from .base import Scraper, ScraperResult
from .utils import discover_json_endpoints, iter_json_candidates

logger = logging.getLogger(__name__)


class ShopifyScraper(Scraper):
    """Scrape Shopify storefronts for raffle metadata."""

    collection_slugs: Iterable[str] = ("draws", "raffles", "products")

    def __init__(self, url: str, *, wait_for_selector: Optional[str] = None) -> None:
        super().__init__(url)
        self.wait_for_selector = wait_for_selector

    def run(self) -> ScraperResult:
        html = self.fetch_html()
        endpoints = discover_json_endpoints(html, self.url)
        endpoints.extend(iter_json_candidates(self.url, self.collection_slugs))
        logger.debug("Discovered %d candidate endpoints for %s", len(endpoints), self.url)

        for endpoint in endpoints:
            try:
                payload = self.fetch_json(endpoint)
            except Exception as exc:  # pragma: no cover - network failures handled upstream
                logger.debug("Failed to fetch JSON from %s: %s", endpoint, exc)
                continue
            result = self._parse_payload(payload)
            if result:
                return result

        logger.warning("No raffle data found for %s", self.url)
        return ScraperResult(tickets_remaining=None, deadline=None, metadata={})

    def _parse_payload(self, payload: Any) -> Optional[ScraperResult]:
        logger.debug("Parsing Shopify payload for %s", self.url)
        products = self._extract_products(payload)
        for product in products:
            remaining = self._extract_tickets(product)
            deadline = self._extract_deadline(product)
            if remaining is not None or deadline is not None:
                return ScraperResult(
                    tickets_remaining=remaining,
                    deadline=deadline,
                    metadata={"product": product},
                )
        return None

    def _extract_products(self, payload: Any) -> Iterable[Dict[str, Any]]:
        if isinstance(payload, dict):
            if "products" in payload and isinstance(payload["products"], list):
                return payload["products"]
            if "product" in payload and isinstance(payload["product"], dict):
                return [payload["product"]]
        return []

    def _extract_tickets(self, product: Dict[str, Any]) -> Optional[int]:
        inventory = product.get("variants") or []
        total = 0
        has_inventory = False
        for variant in inventory:
            inventory_quantity = variant.get("inventory_quantity")
            if isinstance(inventory_quantity, int):
                total += max(inventory_quantity, 0)
                has_inventory = True
        if has_inventory:
            return total
        return product.get("tickets_remaining")

    def _extract_deadline(self, product: Dict[str, Any]) -> Optional[datetime]:
        deadline = product.get("raffle_deadline") or product.get("deadline")
        if isinstance(deadline, str):
            try:
                return datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            except ValueError:
                logger.debug("Unable to parse deadline %s for %s", deadline, self.url)
        return None

    def raffle_url(self, product_handle: str) -> str:
        return urljoin(self.url, f"/products/{product_handle}")
