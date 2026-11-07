import uuid

from sqlalchemy import select

from app.errors import AppError
from app.extensions import db
from app.models import Account


def list_accounts(user_id: uuid.UUID) -> list[Account]:
    stmt = select(Account).where(Account.user_id == user_id).order_by(Account.name)
    return list(db.session.scalars(stmt))


def get_account(user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
    account = db.session.scalar(
        select(Account).where(Account.id == account_id, Account.user_id == user_id)
    )
    if account is None:
        raise AppError("Caixinha não encontrada.", 404, "account_not_found")
    return account


def create_account(user_id: uuid.UUID, data: dict) -> Account:
    account = Account(user_id=user_id, **data)
    db.session.add(account)
    db.session.commit()
    return account


def update_account(user_id: uuid.UUID, account_id: uuid.UUID, changes: dict) -> Account:
    account = get_account(user_id, account_id)
    for field, value in changes.items():
        setattr(account, field, value)
    db.session.commit()
    return account


def delete_account(user_id: uuid.UUID, account_id: uuid.UUID) -> None:
    account = get_account(user_id, account_id)
    db.session.delete(account)
    db.session.commit()