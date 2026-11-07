from datetime import date, datetime, timedelta
from decimal import Decimal

import requests
from flask import current_app
from sqlalchemy import func, select

from app.errors import AppError
from app.extensions import db
from app.models import Account, CdiRate

BCB_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
WINDOW_DAYS = 365 * 5  # o Banco Central limita o tamanho da janela de consulta


def fetch_cdi_series(start: date, end: date) -> list[tuple[date, Decimal]]:
    """Baixa o CDI diário (em % ao dia) entre duas datas."""
    params = {
        "formato": "json",
        "dataInicial": start.strftime("%d/%m/%Y"),
        "dataFinal": end.strftime("%d/%m/%Y"),
    }
    try:
        response = requests.get(BCB_URL, params=params, timeout=30)
        response.raise_for_status()
        rows = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise AppError(
            "Não foi possível consultar o Banco Central.", 502, "cdi_source_unavailable"
        ) from exc

    return [
        (datetime.strptime(row["data"], "%d/%m/%Y").date(), Decimal(row["valor"]))
        for row in rows
    ]


def _default_start() -> date:
    last = db.session.scalar(select(func.max(CdiRate.reference_date)))
    if last is not None:
        return last + timedelta(days=1)
    first_account = db.session.scalar(select(func.min(Account.opened_on)))
    return first_account or date(date.today().year - 1, 1, 1)


def _store_missing(rows: list[tuple[date, Decimal]]) -> int:
    if not rows:
        return 0
    dates = [day for day, _ in rows]
    existing = set(
        db.session.scalars(
            select(CdiRate.reference_date).where(CdiRate.reference_date.in_(dates))
        )
    )
    new_rates = [
        CdiRate(reference_date=day, daily_rate=value)
        for day, value in rows
        if day not in existing
    ]
    db.session.add_all(new_rates)
    db.session.commit()
    return len(new_rates)


def sync_cdi(start: date | None = None, end: date | None = None) -> int:
    """Grava no banco os dias de CDI que ainda faltam. Pode rodar quantas vezes quiser."""
    end = end or date.today()
    start = start or _default_start()

    inserted = 0
    window_start = start
    while window_start <= end:
        window_end = min(window_start + timedelta(days=WINDOW_DAYS), end)
        inserted += _store_missing(fetch_cdi_series(window_start, window_end))
        window_start = window_end + timedelta(days=1)

    current_app.logger.info("CDI sincronizado: %s novos dias (%s a %s)", inserted, start, end)
    return inserted


def list_rates(date_from: date | None = None, date_to: date | None = None) -> list[CdiRate]:
    date_to = date_to or date.today()
    date_from = date_from or date_to - timedelta(days=90)
    stmt = (
        select(CdiRate)
        .where(CdiRate.reference_date >= date_from, CdiRate.reference_date <= date_to)
        .order_by(CdiRate.reference_date)
    )
    return list(db.session.scalars(stmt))