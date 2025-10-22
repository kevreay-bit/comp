"""Simple in-memory caching utilities with TTL support."""
from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass
class CacheEntry:
    data: Any
    etag: str
    expires_at: float


class SimpleTTLCache:
    """A minimal thread-safe TTL cache for request responses."""

    def __init__(self, ttl_seconds: int = 30) -> None:
        self._ttl = ttl_seconds
        self._store: Dict[Tuple[Any, ...], CacheEntry] = {}
        self._lock = threading.Lock()

    def _is_expired(self, entry: CacheEntry) -> bool:
        return entry.expires_at < time.time()

    def get(self, key: Tuple[Any, ...]) -> CacheEntry | None:
        with self._lock:
            entry = self._store.get(key)
            if entry and self._is_expired(entry):
                del self._store[key]
                return None
            return entry

    def set(self, key: Tuple[Any, ...], data: Any) -> CacheEntry:
        payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
        etag = hashlib.sha1(payload.encode("utf-8")).hexdigest()
        entry = CacheEntry(data=data, etag=etag, expires_at=time.time() + self._ttl)
        with self._lock:
            self._store[key] = entry
        return entry


cache = SimpleTTLCache(ttl_seconds=60)
