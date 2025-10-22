import asyncio
from pathlib import Path

from scrapers.playwright_fetcher import PlaywrightFetcher, PlaywrightFetcherConfig
from scrapers.raffle_api import RaffleAPIScraper


class DummyRaffleScraper(RaffleAPIScraper):
    def __init__(self, html: str, responses, fetcher: PlaywrightFetcher):
        super().__init__("https://example.com", playwright_fetcher=fetcher)
        self._html = html
        self._responses = responses

    def fetch_html(self, *, timeout: float = 15.0):  # type: ignore[override]
        return self._html

    def fetch_json(self, endpoint: str, *, timeout: float = 15.0):  # type: ignore[override]
        if isinstance(self._responses, Exception):
            raise self._responses
        return self._responses


def test_raffle_scraper_uses_json_endpoint(tmp_path: Path) -> None:
    async def runner() -> None:
        async def noop_fetch(url, wait_for_selector, headers):
            return ""

        config = PlaywrightFetcherConfig(cache_dir=tmp_path)
        fetcher = PlaywrightFetcher(config=config, fetch_impl=noop_fetch)
        scraper = DummyRaffleScraper(
            '<div data-endpoint="/raffles/api"></div>',
            {"tickets": "10", "deadline": "2024-01-01T00:00:00Z"},
            fetcher,
        )

        result = await scraper.run_async()
        assert result.tickets_remaining == 10
        assert result.deadline.isoformat() == "2024-01-01T00:00:00+00:00"

    asyncio.run(runner())


def test_raffle_scraper_falls_back_to_playwright(tmp_path: Path) -> None:
    async def runner() -> None:
        async def fake_playwright_fetch(url, wait_for_selector, headers):
            return (
                '<div data-raffle-json>{"tickets": 5, "deadline": "2024-02-01T00:00:00Z"}</div>'
            )

        config = PlaywrightFetcherConfig(cache_dir=tmp_path)
        fetcher = PlaywrightFetcher(config=config, fetch_impl=fake_playwright_fetch)
        scraper = DummyRaffleScraper("<html></html>", RuntimeError("boom"), fetcher)

        result = await scraper.run_async()
        assert result.tickets_remaining == 5
        assert result.deadline.isoformat() == "2024-02-01T00:00:00+00:00"

    asyncio.run(runner())
