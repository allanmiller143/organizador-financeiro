import uuid
from datetime import date

from sqlalchemy import select

from app.errors import AppError
from app.extensions import db
from app.models import Account, Transaction
from app.services import account_service, report_service


def _check_date(account: Account, occurred_on: date) -> None:
    if occurred_on > date.today():
        raise AppError("A data não pode estar no futuro.", 422, "date_in_future")
    if occurred_on < account.opened_on:
        raise AppError(
            "A data é anterior à abertura da caixinha.", 422, "date_before_opening"
        )


def _commit_if_consistent(account: Account) -> None:
    """Confere se o histórico continua válido (sem saldo negativo) antes de gravar."""
    try:
        report_service.ensure_consistent_history(account)
    except AppError:
        db.session.rollback()
        raise
    db.session.commit()


def _get_transaction(user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction:
    transaction = db.session.scalar(
        select(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .where(Transaction.id == transaction_id, Account.user_id == user_id)
    )
    if transaction is None:
        raise AppError("Transação não encontrada.", 404, "transaction_not_found")
    return transaction


def list_transactions(
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    kind=None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[Transaction]:
    account_service.get_account(user_id, account_id)  # a caixinha é do usuário?

    stmt = select(Transaction).where(Transaction.account_id == account_id)
    if kind is not None:
        stmt = stmt.where(Transaction.kind == kind)
    if date_from is not None:
        stmt = stmt.where(Transaction.occurred_on >= date_from)
    if date_to is not None:
        stmt = stmt.where(Transaction.occurred_on <= date_to)
    stmt = stmt.order_by(Transaction.occurred_on.desc(), Transaction.id)
    return list(db.session.scalars(stmt))


def create_transaction(
    user_id: uuid.UUID, account_id: uuid.UUID, data: dict
) -> Transaction:
    account = account_service.get_account(user_id, account_id)
    _check_date(account, data["occurred_on"])

    transaction = Transaction(account_id=account.id, **data)
    db.session.add(transaction)
    _commit_if_consistent(account)
    return transaction


def update_transaction(
    user_id: uuid.UUID, transaction_id: uuid.UUID, changes: dict
) -> Transaction:
    transaction = _get_transaction(user_id, transaction_id)
    if changes.get("occurred_on") is not None:
        _check_date(transaction.account, changes["occurred_on"])

    for field, value in changes.items():
        setattr(transaction, field, value)
    _commit_if_consistent(transaction.account)
    return transaction


def delete_transaction(user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
    transaction = _get_transaction(user_id, transaction_id)
    account = transaction.account
    db.session.delete(transaction)
    _commit_if_consistent(account)