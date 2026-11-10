"""Calendário de dias úteis do Brasil e CDI sintético por data.

O CDI só rende em dia útil: sábados, domingos e feriados nacionais ficam de fora.
A tabela de CDI real (Banco Central) já vem só com dias úteis; este módulo serve para
gerar uma tabela de CDI a partir de uma taxa anual (testes, simulações e projeções).
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

BUSINESS_DAYS_PER_YEAR = 252
BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


def today_brazil() -> date:
    """Data civil usada pelo Nubank e pelo usuário, no fuso de Brasília."""
    return datetime.now(BRAZIL_TZ).date()


def easter(year: int) -> date:
    """Domingo de Páscoa (algoritmo gregoriano anônimo)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def brazil_holidays(year: int) -> set[date]:
    """Feriados nacionais e de fechamento bancário (calendário ANBIMA/B3)."""
    easter_day = easter(year)
    holidays = {
        date(year, 1, 1),  # Confraternização Universal
        easter_day - timedelta(days=48),  # Segunda de Carnaval
        easter_day - timedelta(days=47),  # Terça de Carnaval
        easter_day - timedelta(days=2),  # Sexta-feira Santa
        date(year, 4, 21),  # Tiradentes
        date(year, 5, 1),  # Dia do Trabalho
        easter_day + timedelta(days=60),  # Corpus Christi
        date(year, 9, 7),  # Independência
        date(year, 10, 12),  # Nossa Senhora Aparecida
        date(year, 11, 2),  # Finados
        date(year, 11, 15),  # Proclamação da República
        date(year, 12, 25),  # Natal
    }
    if year >= 2024:
        holidays.add(date(year, 11, 20))  # Consciência Negra (nacional desde 2024)
    return holidays


def is_business_day(day: date) -> bool:
    return day.weekday() < 5 and day not in brazil_holidays(day.year)


def next_business_day(day: date) -> date:
    """Primeiro dia útil estritamente depois de 'day'."""
    day += timedelta(days=1)
    while not is_business_day(day):
        day += timedelta(days=1)
    return day


def daily_rate_from_annual(annual_percent: Decimal) -> Decimal:
    """CDI diário (em % ao dia) equivalente a uma taxa anual, base 252 dias úteis."""
    factor = (Decimal(1) + annual_percent / 100) ** (Decimal(1) / BUSINESS_DAYS_PER_YEAR)
    return (factor - 1) * 100


def build_cdi_rates(start: date, end: date, annual_percent: Decimal) -> dict[date, Decimal]:
    """CDI diário (% ao dia) para cada dia útil de start a end, a partir de uma taxa anual."""
    daily = daily_rate_from_annual(annual_percent)
    rates: dict[date, Decimal] = {}
    day = start
    while day <= end:
        if is_business_day(day):
            rates[day] = daily
        day += timedelta(days=1)
    return rates
