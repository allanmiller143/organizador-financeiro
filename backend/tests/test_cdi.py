from datetime import date
from decimal import Decimal

import pytest
import requests

from app.errors import AppError
from app.extensions import db
from app.models import CdiRate
from app.services import cdi_service

RATES = {
    date(2025, 1, 2): Decimal("0.055131"),
    date(2025, 1, 3): Decimal("0.055131"),
    date(2025, 1, 6): Decimal("0.055131"),
}


@pytest.fixture()
def fake_bcb(monkeypatch):
    calls = []

    def fake(start, end):
        calls.append((start, end))
        return [(day, value) for day, value in RATES.items() if start <= day <= end]

    monkeypatch.setattr(cdi_service, "fetch_cdi_series", fake)
    return calls


def count_rates():
    return db.session.query(CdiRate).count()


def test_sync_stores_rates(app, fake_bcb):
    inserted = cdi_service.sync_cdi(start=date(2025, 1, 2), end=date(2025, 1, 10))

    assert inserted == 3
    assert count_rates() == 3


def test_sync_twice_does_not_duplicate(app, fake_bcb):
    cdi_service.sync_cdi(start=date(2025, 1, 2), end=date(2025, 1, 10))

    inserted = cdi_service.sync_cdi(start=date(2025, 1, 2), end=date(2025, 1, 10))

    assert inserted == 0
    assert count_rates() == 3


def test_sync_continues_after_last_stored_date(app, fake_bcb):
    cdi_service.sync_cdi(start=date(2025, 1, 2), end=date(2025, 1, 3))

    inserted = cdi_service.sync_cdi(end=date(2025, 1, 10))

    assert fake_bcb[-1][0] == date(2025, 1, 4)
    assert inserted == 1
    assert count_rates() == 3


def test_source_down_raises_app_error(app, monkeypatch):
    def boom(*args, **kwargs):
        raise requests.ConnectionError("sem rede")

    monkeypatch.setattr(cdi_service.requests, "get", boom)

    with pytest.raises(AppError) as error:
        cdi_service.fetch_cdi_series(date(2025, 1, 2), date(2025, 1, 3))

    assert error.value.code == "cdi_source_unavailable"


def test_list_cdi_requires_token(client):
    response = client.get("/api/cdi")

    assert response.status_code == 401


def test_list_cdi_returns_rates_in_order(client, auth_headers, fake_bcb):
    cdi_service.sync_cdi(start=date(2025, 1, 2), end=date(2025, 1, 10))

    response = client.get("/api/cdi?from=2025-01-01&to=2025-01-31", headers=auth_headers)

    assert response.status_code == 200
    rates = response.get_json()["rates"]
    assert [r["reference_date"] for r in rates] == ["2025-01-02", "2025-01-03", "2025-01-06"]
    assert Decimal(rates[0]["daily_rate"]) == Decimal("0.055131")


def test_list_cdi_invalid_range_returns_422(client, auth_headers):
    response = client.get("/api/cdi?from=2025-02-01&to=2025-01-01", headers=auth_headers)

    assert response.status_code == 422

def test_ensure_covers_downloads_the_missing_early_period(app, fake_bcb):
    app.config["CDI_AUTO_SYNC"] = True
    cdi_service.sync_cdi(start=date(2025, 1, 6), end=date(2025, 1, 6))  # só 06/01 gravado

    cdi_service.ensure_covers(date(2024, 12, 20))

    assert fake_bcb[-1] == (date(2024, 12, 20), date(2025, 1, 5))  # só o buraco
    assert count_rates() == 3  # 06/01 + 02/01 e 03/01 que faltavam


def test_ensure_covers_does_nothing_when_already_covered(app, fake_bcb):
    app.config["CDI_AUTO_SYNC"] = True
    cdi_service.sync_cdi(start=date(2025, 1, 2), end=date(2025, 1, 10))
    calls_before = len(fake_bcb)

    cdi_service.ensure_covers(date(2025, 1, 2))

    assert len(fake_bcb) == calls_before


def test_ensure_covers_is_off_when_auto_sync_is_disabled(app, fake_bcb):
    cdi_service.sync_cdi(start=date(2025, 1, 6), end=date(2025, 1, 6))
    calls_before = len(fake_bcb)

    cdi_service.ensure_covers(date(2024, 12, 20))  # CDI_AUTO_SYNC é False nos testes

    assert len(fake_bcb) == calls_before