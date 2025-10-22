from datetime import datetime, timezone

import pytest

from scraper.utils import normalize_ticket_metrics, parse_countdown_text


def test_parse_countdown_text_absolute():
    result = parse_countdown_text("Draw ends 2024-05-12 20:00")
    assert result.startswith("2024-05-12T20:00")


def test_parse_countdown_text_relative():
    now = datetime(2024, 5, 1, tzinfo=timezone.utc)
    result = parse_countdown_text("Ends in 2 days 3 hours", now=now)
    assert result == datetime(2024, 5, 3, 3, tzinfo=timezone.utc).isoformat()


def test_normalize_ticket_metrics_infers_missing():
    metrics = normalize_ticket_metrics(total=500, sold=None, remaining=150)
    assert metrics.sold == 350
    assert metrics.total == 500
    assert metrics.remaining == 150
    assert metrics.sold_ratio == pytest.approx(0.7)
