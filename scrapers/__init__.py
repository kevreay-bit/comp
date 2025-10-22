"""Scraper discovery utilities."""
from __future__ import annotations

import importlib
import pkgutil
from typing import List

from .base import BaseScraper


def discover() -> List[BaseScraper]:
    """Instantiate all scraper implementations within the package."""

    scrapers: List[BaseScraper] = []
    package = __name__
    for module_info in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
        if module_info.ispkg:
            continue
        if module_info.name in {"base"}:
            continue
        module = importlib.import_module(f"{package}.{module_info.name}")
        candidates = []
        if hasattr(module, "SCRAPER"):
            candidates.append(getattr(module, "SCRAPER"))
        if hasattr(module, "get_scraper"):
            candidates.append(getattr(module, "get_scraper"))
        if hasattr(module, "Scraper"):
            candidates.append(getattr(module, "Scraper"))
        scraper_instance = None
        for candidate in candidates:
            obj = candidate() if callable(candidate) and not isinstance(candidate, BaseScraper) else candidate
            if isinstance(obj, BaseScraper):
                scraper_instance = obj
                break
        if scraper_instance is None:
            for attribute in dir(module):
                attr = getattr(module, attribute)
                if isinstance(attr, BaseScraper):
                    scraper_instance = attr
                    break
        if scraper_instance is not None:
            scrapers.append(scraper_instance)
    return scrapers


__all__ = ["discover", "BaseScraper"]
