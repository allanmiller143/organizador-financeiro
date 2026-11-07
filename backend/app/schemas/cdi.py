from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CdiQuery(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date_from: date | None = Field(default=None, alias="from")
    date_to: date | None = Field(default=None, alias="to")

    @model_validator(mode="after")
    def check_range(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("'from' não pode ser depois de 'to'")
        return self


class CdiRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reference_date: date
    daily_rate: Decimal