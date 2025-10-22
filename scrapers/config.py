"""Loading configuration for ticket site scrapers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .session import EmailPasswordLoginConfig, TokenLoginConfig


@dataclass
class SiteConfig:
    """Configuration describing how to access a ticket site."""

    name: str
    availability_url: str
    login: Optional[object] = None
    notes: Optional[str] = None

    def requires_credentials(self) -> bool:
        """Return ``True`` when login details are provided for the site."""

        return self.login is not None


def _parse_login_config(raw: Dict[str, Any]) -> object:
    login_type = raw.get("type")
    if login_type == "email_password":
        return EmailPasswordLoginConfig(
            login_url=raw["login_url"],
            email_env=raw["email_env"],
            password_env=raw["password_env"],
            email_field=raw.get("email_field", "email"),
            password_field=raw.get("password_field", "password"),
            extra_payload=raw.get("extra_payload", {}),
        )
    if login_type == "token":
        return TokenLoginConfig(
            token_env=raw["token_env"],
            header_name=raw.get("header_name", "Authorization"),
            header_prefix=raw.get("header_prefix", "Bearer "),
        )
    raise ValueError(f"Unsupported login type: {login_type!r}")


def load_site_configs(path: Path) -> List[SiteConfig]:
    """Load site configuration definitions from ``path``.

    The file is expected to contain a JSON object with a top-level ``sites`` list.
    Each entry should include the site ``name`` and ``availability_url`` and may
    optionally describe ``login`` requirements.  Login details are stored in
    environment variables and are *not* persisted to disk.
    """

    data = json.loads(path.read_text())
    sites: Iterable[Dict[str, Any]] = data.get("sites", [])
    parsed: List[SiteConfig] = []
    for entry in sites:
        login_config: Optional[object] = None
        if "login" in entry and entry["login"]:
            login_config = _parse_login_config(entry["login"])
        parsed.append(
            SiteConfig(
                name=entry["name"],
                availability_url=entry["availability_url"],
                login=login_config,
                notes=entry.get("notes"),
            )
        )
    return parsed
