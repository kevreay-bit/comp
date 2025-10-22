"""Simple pipeline utilities for storing scraper output."""

from __future__ import annotations

from queue import Queue
from threading import Lock
from typing import Iterable

from .models import RaffleEntry


class _RaffleQueue:
    """Thread-safe queue wrapper for raffle entries."""

    def __init__(self) -> None:
        self._queue: Queue[RaffleEntry] = Queue()
        self._lock = Lock()

    def push(self, entry: RaffleEntry) -> None:
        with self._lock:
            self._queue.put(entry)

    def extend(self, entries: Iterable[RaffleEntry]) -> None:
        for entry in entries:
            self.push(entry)

    def pop(self) -> RaffleEntry:
        return self._queue.get()

    def size(self) -> int:
        return self._queue.qsize()


raffle_queue = _RaffleQueue()

__all__ = ["raffle_queue"]
