import asyncio
from pathlib import Path

from scrapers.playwright_fetcher import PlaywrightFetcher, PlaywrightFetcherConfig


def test_playwright_fetcher_caches_results(tmp_path: Path) -> None:
    async def runner() -> None:
        calls = 0

        async def fake_fetch(url: str, wait_for_selector, headers):
            nonlocal calls
            calls += 1
            await asyncio.sleep(0)
            return f"content for {url}"

        config = PlaywrightFetcherConfig(cache_dir=tmp_path, ttl_seconds=60)
        fetcher = PlaywrightFetcher(config=config, fetch_impl=fake_fetch)

        first = await fetcher.fetch("https://example.com", wait_for_selector=".raffle")
        second = await fetcher.fetch("https://example.com", wait_for_selector=".raffle")

        assert first == second
        assert calls == 1

    asyncio.run(runner())


def test_playwright_fetcher_respects_rate_limit(tmp_path: Path) -> None:
    async def runner() -> None:
        timestamps = []

        async def fake_fetch(url: str, wait_for_selector, headers):
            timestamps.append(asyncio.get_event_loop().time())
            return "ok"

        config = PlaywrightFetcherConfig(
            cache_dir=tmp_path, ttl_seconds=0, min_interval_seconds=0.2, max_concurrent=1
        )
        fetcher = PlaywrightFetcher(config=config, fetch_impl=fake_fetch)

        await fetcher.fetch("https://example.com/1", use_cache=False)
        await fetcher.fetch("https://example.com/2", use_cache=False)

        assert len(timestamps) == 2
        assert timestamps[1] - timestamps[0] >= 0.19

    asyncio.run(runner())
