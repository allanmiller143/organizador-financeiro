from datetime import date
from decimal import Decimal

from app.services.projection_engine import run_projection
from app.services.yield_engine import to_cents


def monthly_rate(expected_cdi_annual: Decimal, cdi_percent: Decimal) -> Decimal:
    """Taxa de um mês da caixinha, a partir do CDI anual esperado (juros compostos).

    Exemplo: CDI de 12% ao ano e caixinha de 100% -> cerca de 0,949% ao mês.
    """
    cdi_monthly = (1 + expected_cdi_annual / 100) ** (Decimal(1) / 12) - 1
    return cdi_monthly * cdi_percent / 100


def _add_months(day: date, months: int) -> date:
    index = day.year * 12 + (day.month - 1) + months
    return date(index // 12, index % 12 + 1, 1)


def simulate(params: dict) -> dict:
    result = run_projection(
        initial_amount=params["initial_amount"],
        monthly_deposit=params["monthly_deposit"],
        monthly_withdrawal=params["monthly_withdrawal"],
        withdrawal_start_month=params["withdrawal_start_month"],
        horizon_months=params["horizon_months"],
        monthly_rate=monthly_rate(params["expected_cdi_annual"], params["cdi_percent"]),
    )

    today = date.today()
    months = [
        {
            "month": _add_months(today, point.month).strftime("%Y-%m"),
            "gross_balance": to_cents(point.gross_balance),
            "net_balance": to_cents(point.net_balance),
            "invested": to_cents(point.invested),
        }
        for point in result.points
    ]

    last = result.points[-1]
    summary = {
        "gross_balance": to_cents(last.gross_balance),
        "net_balance": to_cents(last.net_balance),
        "invested": to_cents(last.invested),
        "gross_yield": to_cents(last.gross_balance - last.invested),
        "tax_estimated": to_cents(last.tax_estimated),
        "tax_paid": to_cents(last.tax_paid),
        "withdrawn": to_cents(last.withdrawn),
    }
    return {"summary": summary, "depleted_month": result.depleted_month, "months": months}