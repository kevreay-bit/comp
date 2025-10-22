"""Scraper package exposing base classes and common utilities."""

from .models import RaffleEntry
from .pipeline import raffle_queue
from .base import BaseScraper

__all__ = ["BaseScraper", "RaffleEntry", "raffle_queue"]
