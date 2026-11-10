import enum
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class TransactionKind(enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class Transaction(db.Model):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        Index("ix_transactions_account_date", "account_id", "occurred_on"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE")
    )
    kind: Mapped[TransactionKind] = mapped_column(
        Enum(TransactionKind, name="transaction_kind")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    occurred_on: Mapped[date] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(String(255))
    cdi_percent: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("100.00"), server_default="100.00"
    )
    term_months: Mapped[int] = mapped_column(Integer, default=24, server_default="24")
    locked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reinvestment_order: Mapped[int | None] = mapped_column(Integer, nullable=True)

    account: Mapped["Account"] = relationship(back_populates="transactions")
