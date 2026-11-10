import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import TransactionKind


class TransactionIn(BaseModel):
    kind: TransactionKind
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    occurred_on: date
    note: str | None = Field(default=None, max_length=255)
    cdi_percent: Decimal = Field(default=Decimal("100.00"), ge=0, le=1000, decimal_places=2)
    term_months: int = Field(default=24, ge=1, le=120)
    locked: bool = False


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: TransactionKind | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    occurred_on: date | None = None
    note: str | None = Field(default=None, max_length=255)
    cdi_percent: Decimal | None = Field(default=None, ge=0, le=1000, decimal_places=2)
    term_months: int | None = Field(default=None, ge=1, le=120)
    locked: bool | None = None

    @field_validator("kind", "amount", "occurred_on", "cdi_percent", "term_months", "locked")
    @classmethod
    def not_null(cls, value):
        if value is None:
            raise ValueError("não pode ser nulo")
        return value


class TransactionFilters(BaseModel):
    kind: TransactionKind | None = None
    date_from: date | None = None
    date_to: date | None = None

    @model_validator(mode="after")
    def check_range(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from não pode ser depois de date_to")
        return self


class TransactionOrderIn(BaseModel):
    transaction_ids: list[uuid.UUID] = Field(min_length=1)


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    kind: TransactionKind
    amount: Decimal
    occurred_on: date
    note: str | None
    cdi_percent: Decimal
    term_months: int
    locked: bool
    sort_order: int | None
