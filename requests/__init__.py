"""Minimal requests-like interface for fetching HTTP resources."""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from typing import Dict, Optional

__all__ = ["Session", "Response", "HTTPError"]


class HTTPError(RuntimeError):
    pass


@dataclass
class Response:
    url: str
    status_code: int
    _content: bytes

    @property
    def text(self) -> str:
        return self._content.decode("utf-8", errors="replace")

    def raise_for_status(self) -> None:
        if not (200 <= self.status_code < 400):
            raise HTTPError(f"Request to {self.url} failed with status {self.status_code}")


class Session:
    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> Response:
        request = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            status = resp.getcode()
            content = resp.read()
        return Response(url=url, status_code=status, _content=content)
