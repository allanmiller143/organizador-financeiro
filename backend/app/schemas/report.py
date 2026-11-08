import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class SummaryOut(BaseModel):
    account_id: uuid.UUID
    as_of: date
    gross_balance: Decimal
    invested: Decimal
    gross_yield: Decimal
    tax_estimated: Decimal
    net_balance: Decimal
    tax_paid: Decimal


class MonthlyYield(BaseModel):
    month: str
    yield_amount: Decimal


class MonthlyYieldsOut(BaseModel):
    account_id: uuid.UUID
    as_of: date
    months: list[MonthlyYield]

class DashboardTotals(BaseModel):
    gross_balance: Decimal
    invested: Decimal
    gross_yield: Decimal
    tax_estimated: Decimal
    net_balance: Decimal
    tax_paid: Decimal


class DashboardAccount(BaseModel):
    account_id: uuid.UUID
    name: str
    institution: str
    share_percent: Decimal
    gross_balance: Decimal
    net_balance: Decimal
    gross_yield: Decimal


class DashboardOut(BaseModel):
    as_of: date | None
    totals: DashboardTotals
    accounts: list[DashboardAccount]    