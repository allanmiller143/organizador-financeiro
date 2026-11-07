from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class CdiRate(db.Model):
    __tablename__ = "cdi_rates"

    reference_date: Mapped[date] = mapped_column(Date, primary_key=True)
    daily_rate: Mapped[Decimal] = mapped_column(Numeric(12, 8))  # % ao dia