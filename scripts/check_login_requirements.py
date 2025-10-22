"""CLI utility that checks ticket availability endpoints for authentication."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Iterable

from requests.exceptions import RequestException

from scrapers import ScraperSession, load_site_configs

LOGGER = logging.getLogger(__name__)


def _determine_requirement(status_code: int) -> str:
    if status_code in (401, 403):
        return "login_required"
    if status_code >= 500:
        return "server_error"
    if status_code >= 400:
        return "client_error"
    return "accessible"


def check_sites(config_path: Path) -> Dict[str, str]:
    """Inspect ticket availability endpoints defined in ``config_path``."""

    results: Dict[str, str] = {}
    for site in load_site_configs(config_path):
        session = ScraperSession(site.login)
        try:
            response = session.request("GET", site.availability_url)
        except RequestException as exc:
            LOGGER.error("Failed to reach %s: %s", site.name, exc)
            results[site.name] = "unreachable"
        else:
            results[site.name] = _determine_requirement(response.status_code)
        finally:
            session.close()
    return results


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config",
        type=Path,
        help="Path to the JSON configuration containing site definitions.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path to write the results as JSON.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Increase logging verbosity.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    try:
        results = check_sites(args.config)
    except json.JSONDecodeError as exc:
        LOGGER.error("Invalid JSON in %s: %s", args.config, exc)
        return 1

    if args.json_output:
        args.json_output.write_text(json.dumps(results, indent=2, sort_keys=True))
    for name, status in results.items():
        print(f"{name}: {status}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
