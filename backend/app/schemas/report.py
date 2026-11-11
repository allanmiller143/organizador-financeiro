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
    deposited_total: Decimal
    locked_balance: Decimal
    iof_paid: Decimal
    iof_estimated: Decimal


class ReapplicationOut(BaseModel):
    occurred_on: date
    gross_yield: Decimal
    tax_paid: Decimal
    amount: Decimal
    source_transaction_id: uuid.UUID | None


class MonthlyYield(BaseModel):
    month: str
    yield_amount: Decimal
    net_yield_amount: Decimal
    gross_balance: Decimal
    net_balance: Decimal
    invested: Decimal
    reapplications: list[ReapplicationOut]


class MonthlyYieldsOut(BaseModel):
    account_id: uuid.UUID
    as_of: date
    months: list[MonthlyYield]


class DepositWithdrawalOut(BaseModel):
    occurred_on: date
    amount: Decimal
    gross_yield: Decimal
    income_tax: Decimal
    iof: Decimal
    net_amount: Decimal


class DepositDetailOut(BaseModel):
    deposited_on: date
    product: str
    applied_amount: Decimal
    principal_remaining: Decimal
    partial_withdrawals: Decimal
    gross_yield: Decimal
    income_tax: Decimal
    iof: Decimal
    iof_estimated: Decimal
    withdrawals: list[DepositWithdrawalOut]
    gross_balance: Decimal
    net_balance: Decimal
    maturity_on: date
    locked: bool
    term_months: int
    cdi_percent: Decimal


class DepositDetailsOut(BaseModel):
    account_id: uuid.UUID
    as_of: date
    deposits: list[DepositDetailOut]

class DashboardTotals(BaseModel):
    gross_balance: Decimal
    invested: Decimal
    gross_yield: Decimal
    tax_estimated: Decimal
    net_balance: Decimal
    tax_paid: Decimal
    deposited_total: Decimal
    locked_balance: Decimal
    iof_paid: Decimal
    iof_estimated: Decimal


class DashboardAccount(BaseModel):
    account_id: uuid.UUID
    name: str
    institution: str
    goal_amount: Decimal | None
    share_percent: Decimal
    gross_balance: Decimal
    net_balance: Decimal
    gross_yield: Decimal


class DashboardOut(BaseModel):
    as_of: date | None
    totals: DashboardTotals
    accounts: list[DashboardAccount]    
