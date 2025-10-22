"""Site-specific raffle scrapers."""

from .base import Scraper, ScraperResult
from .playwright_fetcher import PlaywrightFetcher, PlaywrightFetcherConfig
from .raffle_api import RaffleAPIScraper
from .shopify import ShopifyScraper
from .utils import discover_json_endpoints

__all__ = [
    "Scraper",
    "ScraperResult",
    "PlaywrightFetcher",
    "PlaywrightFetcherConfig",
    "ShopifyScraper",
    "RaffleAPIScraper",
    "discover_json_endpoints",
]
