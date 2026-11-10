import uuid
from datetime import date

from sqlalchemy import func, select

from app.errors import AppError
from app.extensions import db
from app.models import Account, Transaction, TransactionKind
from app.services import account_service, report_service
from app.services.calendar_br import today_brazil
from app.services.tax_engine import MAX_LOCK_TERM_MONTHS
from app.services.tax_engine import lock_end_date, rollover_due_date


def _check_date(account: Account, occurred_on: date) -> None:
    if occurred_on > today_brazil():
        raise AppError("A data não pode estar no futuro.", 422, "date_in_future")
    if occurred_on < account.opened_on:
        raise AppError(
            "A data é anterior à abertura da caixinha.", 422, "date_before_opening"
        )


def _check_lock_rules(account: Account, term_months: int) -> None:
    """Dinheiro trancado só existe em caixinha de 100% do CDI e por até 24 meses."""
    if account.cdi_percent > 100:
        raise AppError(
            "Caixinhas que rendem mais de 100% do CDI não aceitam dinheiro trancado.",
            422,
            "lock_not_allowed",
        )
    if term_months > MAX_LOCK_TERM_MONTHS:
        raise AppError(
            f"O prazo da trava pode ter no máximo {MAX_LOCK_TERM_MONTHS} meses.",
            422,
            "lock_term_too_long",
        )


def _apply_rate_rules(account: Account, kind, locked: bool, term_months: int, target: dict) -> None:
    """Valida a trava; sem trava, o aporte rende o padrão da caixinha (e retirada nunca trava)."""
    if kind == TransactionKind.DEPOSIT and locked:
        _check_lock_rules(account, term_months)
        return
    target["locked"] = False
    target["cdi_percent"] = account.cdi_percent
    target["term_months"] = 24


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
    # Para lançamentos no mesmo dia, preserve a ordem de inserção aproximada
    # usada pelo histórico legado, em vez de inverter os lotes pelo UUID.
    stmt = stmt.order_by(
        Transaction.occurred_on.desc(),
        Transaction.sort_order.asc().nullslast(),
        Transaction.id.desc(),
    )
    return list(db.session.scalars(stmt))


def create_transaction(
    user_id: uuid.UUID, account_id: uuid.UUID, data: dict
) -> Transaction:
    account = account_service.get_account(user_id, account_id)
    _check_date(account, data["occurred_on"])
    _apply_rate_rules(
        account, data["kind"], data.get("locked", False), data.get("term_months", 24), data
    )

    # O lançamento mais recente do dia aparece no topo. Não use a ordem da
    # caixinha inteira: lançamentos de outras datas não devem interferir na
    # sequência visual/operacional deste dia. Usar um índice menor preserva
    # também a mesma prioridade no motor, que ordena sort_order crescente.
    current_min = db.session.scalar(
        select(func.min(Transaction.sort_order)).where(
            Transaction.account_id == account.id,
            Transaction.occurred_on == data["occurred_on"],
        )
    )
    transaction = Transaction(
        account_id=account.id,
        sort_order=(current_min - 1 if current_min is not None else 0),
        **data,
    )
    db.session.add(transaction)
    _commit_if_consistent(account)
    return transaction


def update_transaction(
    user_id: uuid.UUID, transaction_id: uuid.UUID, changes: dict
) -> Transaction:
    transaction = _get_transaction(user_id, transaction_id)
    if changes.get("occurred_on") is not None:
        _check_date(transaction.account, changes["occurred_on"])
    _apply_rate_rules(
        transaction.account,
        changes.get("kind", transaction.kind),
        changes.get("locked", transaction.locked),
        changes.get("term_months", transaction.term_months),
        changes,
    )

    for field, value in changes.items():
        setattr(transaction, field, value)
    _commit_if_consistent(transaction.account)
    return transaction


def reorder_transactions(
    user_id: uuid.UUID, account_id: uuid.UUID, transaction_ids: list[uuid.UUID]
) -> None:
    account_service.get_account(user_id, account_id)
    transactions = list(
        db.session.scalars(
            select(Transaction).where(
                Transaction.account_id == account_id,
                Transaction.id.in_(transaction_ids),
            )
        )
    )
    if len(transactions) != len(transaction_ids):
        raise AppError("Há lançamentos inválidos na ordem enviada.", 422, "invalid_order")
    days = {transaction.occurred_on for transaction in transactions}
    if len(days) != 1 or len(set(transaction_ids)) != len(transaction_ids):
        raise AppError(
            "Só é possível reordenar lançamentos do mesmo dia.", 422, "invalid_order"
        )
    by_id = {transaction.id: transaction for transaction in transactions}
    for index, transaction_id in enumerate(transaction_ids):
        by_id[transaction_id].sort_order = index
    _commit_if_consistent(by_id[transaction_ids[0]].account)


def reorder_reapplications(
    user_id: uuid.UUID, account_id: uuid.UUID, transaction_ids: list[uuid.UUID]
) -> None:
    """Persiste a ordem dos aportes que serão reaplicados na mesma data."""
    account = account_service.get_account(user_id, account_id)
    transactions = list(
        db.session.scalars(
            select(Transaction).where(
                Transaction.account_id == account_id,
                Transaction.id.in_(transaction_ids),
            )
        )
    )
    if len(transactions) != len(transaction_ids) or len(set(transaction_ids)) != len(transaction_ids):
        raise AppError("Há reaplicações inválidas na ordem enviada.", 422, "invalid_order")
    if any(transaction.kind != TransactionKind.DEPOSIT for transaction in transactions):
        raise AppError("Só aportes podem ser reordenados como reaplicações.", 422, "invalid_order")

    def due_date(transaction: Transaction) -> date:
        if transaction.locked:
            return lock_end_date(transaction.occurred_on, transaction.term_months)
        return rollover_due_date(transaction.occurred_on)

    dates = {due_date(transaction) for transaction in transactions}
    if len(dates) != 1:
        raise AppError(
            "Só é possível reordenar reaplicações que vencem no mesmo dia.",
            422,
            "invalid_order",
        )
    all_same_day = [
        transaction
        for transaction in db.session.scalars(
            select(Transaction).where(Transaction.account_id == account_id)
        )
        if transaction.kind == TransactionKind.DEPOSIT and due_date(transaction) == next(iter(dates))
    ]
    if {transaction.id for transaction in all_same_day} != set(transaction_ids):
        raise AppError(
            "Envie todas as reaplicações que vencem nessa data para reordená-las.",
            422,
            "invalid_order",
        )
    by_id = {transaction.id: transaction for transaction in transactions}
    for order, transaction_id in enumerate(transaction_ids):
        by_id[transaction_id].reinvestment_order = order
    _commit_if_consistent(account)


def delete_transaction(user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
    transaction = _get_transaction(user_id, transaction_id)
    account = transaction.account
    db.session.delete(transaction)
    _commit_if_consistent(account)
