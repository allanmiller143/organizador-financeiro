import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Projection(db.Model):
    __tablename__ = "projections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    horizon_months: Mapped[int] = mapped_column(Integer)
    monthly_deposit: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    expected_cdi_annual: Mapped[Decimal] = mapped_column(Numeric(6, 2))