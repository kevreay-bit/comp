"""Helpers for Playwright-backed scraping with caching and rate limiting."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, Dict, Optional

logger = logging.getLogger(__name__)

FetchImplementation = Callable[[str, Optional[str], Optional[Dict[str, str]]], Awaitable[str]]


@dataclass
class PlaywrightFetcherConfig:
    cache_dir: Path
    ttl_seconds: int = 900
    max_concurrent: int = 2
    min_interval_seconds: float = 2.0
    wait_timeout_ms: int = 5000


class PlaywrightFetcher:
    """Encapsulates Playwright usage with caching and rate limiting."""

    def __init__(
        self,
        config: Optional[PlaywrightFetcherConfig] = None,
        *,
        fetch_impl: Optional[FetchImplementation] = None,
    ) -> None:
        config = config or PlaywrightFetcherConfig(cache_dir=Path(".cache/playwright"))
        self.config = config
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        self._fetch_impl = fetch_impl or self._default_fetch_impl
        self._semaphore = asyncio.Semaphore(config.max_concurrent)
        self._rate_lock = asyncio.Lock()
        self._url_locks: Dict[str, asyncio.Lock] = {}
        self._last_fetch = 0.0

    async def fetch(
        self,
        url: str,
        *,
        wait_for_selector: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        use_cache: bool = True,
    ) -> str:
        """Fetch a fully rendered page using Playwright."""

        cache_path = self._cache_path(url, wait_for_selector)
        if use_cache:
            cached = self._read_cache(cache_path)
            if cached is not None:
                logger.debug("Returning cached Playwright result for %s", url)
                return cached

        lock = self._url_locks.setdefault(url, asyncio.Lock())
        async with lock:
            # Re-check cache once lock is acquired.
            if use_cache:
                cached = self._read_cache(cache_path)
                if cached is not None:
                    logger.debug("Returning cached Playwright result for %s after lock", url)
                    return cached

            async with self._semaphore:
                await self._respect_interval()
                html = await self._fetch_impl(url, wait_for_selector, headers)

            if use_cache:
                self._write_cache(cache_path, html)
            return html

    async def _respect_interval(self) -> None:
        async with self._rate_lock:
            now = time.monotonic()
            elapsed = now - self._last_fetch
            wait_for = self.config.min_interval_seconds - elapsed
            if wait_for > 0:
                logger.debug("Sleeping %.2fs to respect Playwright rate limit", wait_for)
                await asyncio.sleep(wait_for)
            self._last_fetch = time.monotonic()

    def _cache_path(self, url: str, wait_for_selector: Optional[str]) -> Path:
        key = f"{url}|{wait_for_selector or ''}"
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.config.cache_dir / f"{digest}.json"

    def _read_cache(self, path: Path) -> Optional[str]:
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            logger.warning("Corrupted Playwright cache at %s", path)
            return None
        age = time.time() - payload.get("timestamp", 0)
        if age > self.config.ttl_seconds:
            logger.debug("Ignoring expired cache entry %s", path)
            return None
        return payload.get("content")

    def _write_cache(self, path: Path, content: str) -> None:
        payload = {"timestamp": time.time(), "content": content}
        path.write_text(json.dumps(payload))

    async def _default_fetch_impl(
        self,
        url: str,
        wait_for_selector: Optional[str],
        headers: Optional[Dict[str, str]],
    ) -> str:
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:  # pragma: no cover - imported lazily in production
            raise RuntimeError(
                "Playwright is required for dynamic scraping but is not installed."
            ) from exc

        async with async_playwright() as p:  # pragma: no cover - exercised in production
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            if headers:
                await page.set_extra_http_headers(headers)
            await page.goto(url, wait_until="networkidle")
            if wait_for_selector:
                await page.wait_for_selector(
                    wait_for_selector, timeout=self.config.wait_timeout_ms
                )
            content = await page.content()
            await browser.close()
            return content
