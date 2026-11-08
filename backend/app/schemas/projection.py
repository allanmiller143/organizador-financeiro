from decimal import Decimal

from pydantic import BaseModel, Field


class SimulationIn(BaseModel):
    initial_amount: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    monthly_deposit: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    monthly_withdrawal: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    withdrawal_start_month: int = Field(default=1, ge=1, le=600)
    horizon_months: int = Field(ge=1, le=600)  # no máximo 50 anos
    expected_cdi_annual: Decimal = Field(gt=0, le=100, max_digits=5, decimal_places=2)
    cdi_percent: Decimal = Field(default=Decimal("100"), gt=0, le=500, max_digits=5, decimal_places=2)


class ProjectionPoint(BaseModel):
    month: str  # "2027-03"
    gross_balance: Decimal
    net_balance: Decimal
    invested: Decimal


class ProjectionSummary(BaseModel):
    gross_balance: Decimal
    net_balance: Decimal
    invested: Decimal
    gross_yield: Decimal
    tax_estimated: Decimal
    tax_paid: Decimal
    withdrawn: Decimal


class SimulationOut(BaseModel):
    summary: ProjectionSummary
    depleted_month: int | None
    months: list[ProjectionPoint]