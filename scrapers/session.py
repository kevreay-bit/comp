"""Session helpers that take care of authentication."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, Optional

import requests
from requests import Response
from requests.exceptions import RequestException

LOGGER = logging.getLogger(__name__)


@dataclass
class EmailPasswordLoginConfig:
    """Settings required to authenticate with a form-based login."""

    login_url: str
    email_env: str
    password_env: str
    email_field: str = "email"
    password_field: str = "password"
    extra_payload: Dict[str, str] = field(default_factory=dict)


@dataclass
class TokenLoginConfig:
    """Settings required for token based authentication."""

    token_env: str
    header_name: str = "Authorization"
    header_prefix: str = "Bearer "


class ScraperSession:
    """Wrapper around :class:`requests.Session` with optional login support."""

    def __init__(self, login_config: Optional[object] = None) -> None:
        self._session = requests.Session()
        self._login_config = login_config
        self._authenticated = False
        self._login_attempted = False

    @property
    def session(self) -> requests.Session:
        return self._session

    def close(self) -> None:
        self._session.close()

    def _login_with_email_password(self, config: EmailPasswordLoginConfig) -> bool:
        email = os.getenv(config.email_env)
        password = os.getenv(config.password_env)
        if not email or not password:
            LOGGER.warning(
                "Missing credentials for %s (expected %s/%s)."
                " Proceeding without authentication.",
                config.login_url,
                config.email_env,
                config.password_env,
            )
            return False

        payload = dict(config.extra_payload)
        payload.update({config.email_field: email, config.password_field: password})

        try:
            response = self._session.post(config.login_url, data=payload, timeout=15)
            response.raise_for_status()
        except RequestException as exc:
            LOGGER.error("Login request to %s failed: %s", config.login_url, exc)
            return False

        LOGGER.info("Authenticated against %s using email/password flow.", config.login_url)
        return True

    def _login_with_token(self, config: TokenLoginConfig) -> bool:
        token = os.getenv(config.token_env)
        if not token:
            LOGGER.warning(
                "Missing token for header %s (expected %s). Proceeding anonymously.",
                config.header_name,
                config.token_env,
            )
            return False

        header_value = f"{config.header_prefix}{token}" if config.header_prefix else token
        self._session.headers[config.header_name] = header_value
        LOGGER.info("Configured %s header for token authentication.", config.header_name)
        return True

    def ensure_authenticated(self) -> bool:
        """Authenticate the session if a login configuration was supplied."""

        if self._login_config is None:
            return False
        if self._login_attempted:
            return self._authenticated

        self._login_attempted = True
        if isinstance(self._login_config, EmailPasswordLoginConfig):
            self._authenticated = self._login_with_email_password(self._login_config)
        elif isinstance(self._login_config, TokenLoginConfig):
            self._authenticated = self._login_with_token(self._login_config)
        else:
            LOGGER.error("Unsupported login configuration: %r", self._login_config)
            self._authenticated = False
        return self._authenticated

    def request(self, method: str, url: str, **kwargs) -> Response:
        """Perform a request using the underlying session.

        Authentication is attempted exactly once when a login configuration has
        been provided.  Failures are logged but the request still goes through so
        that callers can implement their own fallback behaviour.
        """

        self.ensure_authenticated()
        try:
            response = self._session.request(method, url, timeout=kwargs.pop("timeout", 15), **kwargs)
            return response
        except RequestException as exc:
            LOGGER.error("Request to %s failed: %s", url, exc)
            raise
