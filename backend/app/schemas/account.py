import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AccountIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    institution: str = Field(min_length=1, max_length=120)
    cdi_percent: Decimal = Field(gt=0, le=500, max_digits=5, decimal_places=2)
    opened_on: date


class AccountUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    institution: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None

    @field_validator("name", "institution", "is_active")
    @classmethod
    def not_null(cls, value):
        if value is None:
            raise ValueError("não pode ser nulo")
        return value


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    institution: str
    cdi_percent: Decimal
    opened_on: date
    is_active: bool