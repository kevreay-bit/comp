"""Concrete scraper implementations for specific raffle sites."""

from .raffle_site_a import RaffleSiteAScraper
from .raffle_site_b import RaffleSiteBScraper

__all__ = ["RaffleSiteAScraper", "RaffleSiteBScraper"]
