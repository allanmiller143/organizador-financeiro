from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.services.yield_engine import Flow, check_coverage, daily_yield_rate

CENT_TOLERANCE = Decimal("0.005")  # meio centavo: absorve diferenças de arredondamento
FULL_REDEMPTION_TOLERANCE = Decimal("0.06")  # saldo exibido pode diferir do cálculo subcentavo
IR_LOWEST_RATE_AGE_DAYS = 721  # a menor alíquota (15%) vale acima de 720 dias
ROLLOVER_AGE_MONTHS = 24
TERM_DAYS = {
    6: 182,
    12: 365,
    18: 548,
    24: 730,
}
MATURITY_DAYS = TERM_DAYS[ROLLOVER_AGE_MONTHS]  # todo aporte vence em 2 anos, trancado ou não
MAX_LOCK_TERM_MONTHS = ROLLOVER_AGE_MONTHS  # a trava nunca passa do vencimento


IOF_PERCENT_BY_DAY = {
    1: Decimal("0.96"), 2: Decimal("0.93"), 3: Decimal("0.90"), 4: Decimal("0.86"),
    5: Decimal("0.83"), 6: Decimal("0.80"), 7: Decimal("0.76"), 8: Decimal("0.73"),
    9: Decimal("0.70"), 10: Decimal("0.66"), 11: Decimal("0.63"), 12: Decimal("0.60"),
    13: Decimal("0.56"), 14: Decimal("0.53"), 15: Decimal("0.50"), 16: Decimal("0.46"),
    17: Decimal("0.43"), 18: Decimal("0.40"), 19: Decimal("0.36"), 20: Decimal("0.33"),
    21: Decimal("0.30"), 22: Decimal("0.26"), 23: Decimal("0.23"), 24: Decimal("0.20"),
    25: Decimal("0.16"), 26: Decimal("0.13"), 27: Decimal("0.10"), 28: Decimal("0.06"),
    29: Decimal("0.03"), 30: Decimal("0.00"),
}


def iof_rate(age_days: int) -> Decimal:
    """Fração do rendimento cobrada de IOF em um resgate, conforme os dias desde o aporte."""
    return IOF_PERCENT_BY_DAY.get(age_days, Decimal("0"))


class InsufficientBalanceError(Exception):
    """A retirada é maior que o saldo da caixinha naquele dia."""

    def __init__(self, day: date, shortfall: Decimal, locked_amount: Decimal = Decimal("0")):
        super().__init__(f"Saldo insuficiente em {day}: faltam {shortfall}")
        self.day = day
        self.shortfall = shortfall
        self.locked_amount = locked_amount  # quanto havia trancado (e por isso fora do saque)


@dataclass
class Lot:
    """Um aporte: a data em que entrou, o valor aplicado e o valor atual.

    - principal: base do imposto (o que já foi tributado vira novo principal);
    - invested: o que a pessoa realmente aplicou, nunca inclui rendimento nem reaplicação;
    - cdi_percent/term_months/locked: só valem enquanto a trava estiver ativa.
    """

    start: date
    principal: Decimal
    value: Decimal
    invested: Decimal
    cdi_percent: Decimal = Decimal("100.00")
    term_months: int = ROLLOVER_AGE_MONTHS
    locked: bool = False
    sequence: int = 0
    source_id: str | None = None
    reinvestment_order: int | None = None


@dataclass(frozen=True)
class TaxSummary:
    gross_balance: Decimal  # saldo bruto
    invested: Decimal  # parte do saldo que é dinheiro aportado
    gross_yield: Decimal  # rendimento ainda dentro da caixinha
    tax_estimated: Decimal  # IR + IOF se resgatasse tudo na data final
    net_balance: Decimal  # saldo bruto menos o imposto estimado (IR + IOF)
    tax_paid: Decimal  # IR + IOF já retidos nas retiradas feitas
    deposited_total: Decimal = Decimal("0")  # soma literal dos aportes cadastrados
    locked_balance: Decimal = Decimal("0")  # parte do saldo trancada (sem saque até o prazo)
    iof_paid: Decimal = Decimal("0")  # parte de tax_paid que foi IOF
    iof_estimated: Decimal = Decimal("0")  # parte de tax_estimated que seria IOF


@dataclass(frozen=True)
class Reinvestment:
    occurred_on: date
    gross_yield: Decimal
    tax_paid: Decimal
    amount: Decimal
    source_transaction_id: str | None = None


@dataclass(frozen=True)
class MonthlyBalance:
    month: str
    yield_amount: Decimal
    gross_balance: Decimal
    net_balance: Decimal
    tax_estimated: Decimal
    tax_paid: Decimal
    reapplications: list[Reinvestment]
    invested: Decimal = Decimal("0")  # valor aplicado no fim do mês


def ir_rate(age_days: int) -> Decimal:
    """Alíquota regressiva do IR conforme os dias corridos desde o aporte."""
    if age_days <= 180:
        return Decimal("0.225")
    if age_days <= 360:
        return Decimal("0.20")
    if age_days <= 720:
        return Decimal("0.175")
    return Decimal("0.15")


def redemption_taxes(yield_out: Decimal, age_days: int) -> tuple[Decimal, Decimal]:
    """(IR, IOF) de um resgate, dado o rendimento resgatado e a idade do lote em dias.

    O IOF incide primeiro sobre o rendimento; o IR incide sobre o que sobra:
    IR = (rendimento - IOF) x alíquota.
    """
    yield_out = max(yield_out, Decimal("0"))
    iof = yield_out * iof_rate(age_days)
    ir = (yield_out - iof) * ir_rate(age_days)
    return ir, iof


def withdrawal_cost(value: Decimal, principal: Decimal, age_days: int) -> Decimal:
    """Imposto (IR + IOF) por real sacado de um lote com esse valor, principal e idade.

    É o critério que o Nubank usa para escolher de qual depósito sai uma retirada
    parcial: o IOF é cobrado primeiro sobre o rendimento e o IR incide sobre o que sobra.
    """
    if value <= 0:
        return Decimal("0")
    yield_share = max(value - principal, Decimal("0")) / value
    iof = iof_rate(age_days)
    return yield_share * (iof + (1 - iof) * ir_rate(age_days))


def withdrawal_sort_cost(value: Decimal, principal: Decimal, age_days: int) -> Decimal:
    """Normaliza resíduos subcentavários antes de desempatar lotes equivalentes."""
    return withdrawal_cost(value, principal, age_days).quantize(
        Decimal("0.000000000001"), rounding=ROUND_HALF_UP
    )


def gross_redemption_for_net(net_amount: Decimal, value: Decimal, principal: Decimal, age_days: int) -> Decimal:
    """Converte o valor líquido pedido no saque para o valor bruto do lote."""
    cost = withdrawal_cost(value, principal, age_days)
    if cost >= 1:
        return value
    return net_amount / (Decimal("1") - cost)


def _withdraw(
    lots: list[Lot], amount: Decimal, day: date, sequence: int | None = None
) -> tuple[Decimal, Decimal]:
    """Retira primeiro do lote com menor custo de imposto por real líquido recebido.

    Não é FIFO nem LIFO: confirmado com uma caixinha real do Nubank, em que uma
    retirada de lote novo (IOF alto) saiu do depósito mais novo, e retiradas
    posteriores saíram do mais antigo (IOF já baixo). O custo é calculado sobre o valor
    atual do lote (principal restante + rendimento); o resgate bruto é convertido a
    partir do valor líquido pedido antes de aplicar IR e IOF.
    Devolve (IR, IOF) retidos.
    Lotes trancados ficam fora da seleção até o fim da trava. A sequência manual
    desempata aportes no mesmo dia.
    """
    remaining = amount
    ir_total = Decimal("0")
    iof_total = Decimal("0")
    candidates = sorted(
        [
            lot
            for lot in lots
            if lot.start <= day
            and not lock_is_active(lot, day)
            # Um aporte feito depois da retirada no mesmo dia ainda não existia
            # para aquele resgate, embora possa render no próprio dia.
            and not (
                sequence is not None
                and lot.start == day
                and lot.sequence > sequence
            )
        ],
        key=lambda lot: (
            withdrawal_sort_cost(lot.value, lot.principal, (day - lot.start).days),
            -lot.start.toordinal(),
            -lot.value,
            -lot.sequence,
        ),
    )
    for lot in candidates:
        if remaining <= CENT_TOLERANCE:
            break
        age_days = (day - lot.start).days
        cost = withdrawal_cost(lot.value, lot.principal, age_days)
        full_net = lot.value * (Decimal("1") - cost)
        close_displayed_lot = remaining + FULL_REDEMPTION_TOLERANCE >= full_net
        if close_displayed_lot:
            # Calcula o bruto para o líquido pedido, mas descarta o resíduo
            # subcentavo exibido como lote zerado. Assim não contabilizamos
            # como saque um valor maior que o usuário efetivamente recebeu.
            take = min(
                gross_redemption_for_net(remaining, lot.value, lot.principal, age_days),
                lot.value,
            )
        else:
            take = min(gross_redemption_for_net(remaining, lot.value, lot.principal, age_days), lot.value)
        principal_out = lot.principal * (take / lot.value)
        invested_out = lot.invested * (take / lot.value)
        yield_out = take - principal_out
        ir, iof = redemption_taxes(yield_out, age_days)
        net_taken = take - ir - iof
        ir_total += ir
        iof_total += iof
        lot.principal -= principal_out
        lot.invested -= invested_out
        lot.value -= take
        remaining -= net_taken
        if close_displayed_lot:
            lot.principal = Decimal("0")
            lot.invested = Decimal("0")
            lot.value = Decimal("0")

    if remaining > CENT_TOLERANCE:
        locked_amount = sum(
            (lot.value for lot in lots if lock_is_active(lot, day)), Decimal("0")
        )
        raise InsufficientBalanceError(day, remaining, locked_amount)

    lots[:] = [lot for lot in lots if lot.value > CENT_TOLERANCE]  # descarta lotes zerados
    return ir_total, iof_total


def rollover_due_date(start: date) -> date:
    """Vencimento de qualquer aporte: 2 anos (730 dias) depois, como no produto Nubank."""
    return start + timedelta(days=MATURITY_DAYS)


def lock_end_date(start: date, term_months: int) -> date:
    """Dia em que a trava de um aporte trancado termina."""
    days = TERM_DAYS.get(term_months, round(365 * term_months / 12))
    return start + timedelta(days=days)


def lock_is_active(lot: "Lot", day: date) -> bool:
    """O dinheiro ainda está trancado (não pode ser sacado) neste dia?"""
    return lot.locked and day < lock_end_date(lot.start, lot.term_months)


def rate_percent(lot: "Lot", day: date, base_percent: Decimal) -> Decimal:
    """% do CDI que o lote rende no dia.

    Trancado: a taxa maior da trava, até o último dia dela. Depois disso (ou sem trava),
    o lote volta a ser um aporte normal e rende o padrão da caixinha.
    """
    if lot.locked and day <= lock_end_date(lot.start, lot.term_months):
        return lot.cdi_percent
    return base_percent


def settle_matured_lot(
    principal: Decimal, value: Decimal, age_days: int = IR_LOWEST_RATE_AGE_DAYS
) -> tuple[Decimal, Decimal]:
    """Calcula o IR do vencimento usando a idade real do investimento."""
    taxable_yield = max(value - principal, Decimal("0"))
    tax = (taxable_yield * ir_rate(age_days)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    reinvested = (value - tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return tax, reinvested


def _rollover_matured_lots(
    lots: list[Lot], day: date, base_percent: Decimal = Decimal("100.00")
) -> tuple[Decimal, list[Reinvestment]]:
    """Reinveste lotes no vencimento aplicável, descontando o IR do rendimento.

    Um aporte normal vence em dois anos. Um aporte travado é encerrado e
    reaplicado no fim da própria trava (6, 12, 18 ou 24 meses). O dinheiro
    reaplicado volta como lote normal, sem trava, rendendo o padrão da caixinha.
    O valor aplicado continua sendo o principal originalmente depositado; o
    rendimento reaplicado não vira um novo aporte literal.
    """
    tax_paid = Decimal("0")
    reapplications = []
    remaining_lots = []
    due_lots = []
    for lot in lots:
        due_date = lock_end_date(lot.start, lot.term_months) if lot.locked else rollover_due_date(lot.start)
        if day < due_date:
            remaining_lots.append(lot)
            continue
        due_lots.append(lot)

    due_lots.sort(
        key=lambda lot: (
            lot.reinvestment_order if lot.reinvestment_order is not None else lot.sequence,
            lot.sequence,
        )
    )
    for lot in due_lots:

        tax, reinvested = settle_matured_lot(
            lot.principal, lot.value, (day - lot.start).days
        )
        tax_paid += tax
        reapplications.append(
            Reinvestment(
                occurred_on=day,
                gross_yield=lot.value - lot.principal,
                tax_paid=tax,
                amount=reinvested,
                source_transaction_id=lot.source_id,
            )
        )
        if reinvested > CENT_TOLERANCE:
            remaining_lots.append(
                Lot(
                    start=day,
                    principal=reinvested,
                    value=reinvested,
                    invested=lot.invested,
                    cdi_percent=base_percent,
                    term_months=ROLLOVER_AGE_MONTHS,
                    locked=False,
                    source_id=lot.source_id,
                    reinvestment_order=lot.reinvestment_order,
                )
            )

    lots[:] = remaining_lots
    return tax_paid, reapplications


def _summarize_lots(
    lots: list[Lot],
    day: date,
    tax_paid: Decimal,
    deposited_total: Decimal = Decimal("0"),
    iof_paid: Decimal = Decimal("0"),
) -> TaxSummary:
    gross = sum((lot.value for lot in lots), Decimal("0"))
    invested = sum((lot.invested for lot in lots), Decimal("0"))
    estimated_ir = Decimal("0")
    estimated_iof = Decimal("0")
    for lot in lots:
        ir, iof = redemption_taxes(lot.value - lot.principal, (day - lot.start).days)
        estimated_ir += ir
        estimated_iof += iof
    estimated = estimated_ir + estimated_iof
    locked = sum((lot.value for lot in lots if lock_is_active(lot, day)), Decimal("0"))
    return TaxSummary(
        locked_balance=locked,
        gross_balance=gross,
        invested=invested,
        gross_yield=gross - invested,
        tax_estimated=estimated,
        net_balance=gross - estimated,
        tax_paid=tax_paid,
        deposited_total=deposited_total,
        iof_paid=iof_paid,
        iof_estimated=estimated_iof,
    )


def _simulate_lots(
    flows: list[Flow],
    rates: dict[date, Decimal],
    cdi_percent: Decimal,
    start: date,
    end: date,
    include_monthly_balances: bool,
) -> tuple[TaxSummary, list[MonthlyBalance]]:
    """Percorre os dias de start a end com lotes e devolve o resumo com imposto."""
    check_coverage(rates, start, end)

    flows_by_day: dict[date, list[Flow]] = defaultdict(list)
    for flow in flows:
        flows_by_day[flow.day].append(flow)
    for day_flows in flows_by_day.values():
        day_flows.sort(key=lambda flow: flow.sequence)

    lots: list[Lot] = []
    tax_paid = Decimal("0")
    iof_paid = Decimal("0")
    deposited_total = Decimal("0")
    monthly_balances: list[MonthlyBalance] = []
    monthly_yields: dict[tuple[int, int], Decimal] = defaultdict(Decimal)
    monthly_reapplications: dict[tuple[int, int], list[Reinvestment]] = defaultdict(list)
    day = start
    while day <= end:
        # O aporte entra antes do ciclo do próprio dia. A retirada é processada
        # antes do crédito do CDI, e o saldo que permanece segue para o rendimento.
        for flow in flows_by_day.get(day, []):
            if flow.amount >= 0:
                deposited_total += flow.amount
                lots.append(
                    Lot(
                        start=day,
                        principal=flow.amount,
                        value=flow.amount,
                        invested=flow.amount,
                        cdi_percent=flow.cdi_percent,
                        term_months=flow.term_months,
                        locked=flow.locked,
                        sequence=flow.sequence,
                        source_id=flow.source_id,
                        reinvestment_order=flow.reinvestment_order,
                    )
                )

        # O Nubank fecha o resgate antes do crédito do rendimento daquele dia.
        # Assim, um aporte rende no próprio dia, mas o valor retirado naquele dia
        # não recebe o CDI desse mesmo dia; o saldo que permanece recebe.
        for flow in flows_by_day.get(day, []):
            if flow.amount < 0:
                ir, iof = _withdraw(lots, -flow.amount, day, flow.sequence)
                tax_paid += ir + iof
                iof_paid += iof

        earned = Decimal("0")
        if day in rates:  # só o saldo após os resgates recebe o CDI do dia
            for lot in lots:
                lot_rate = daily_yield_rate(rates[day], rate_percent(lot, day, cdi_percent))
                earned += lot.value * lot_rate
                lot.value *= 1 + lot_rate
        monthly_yields[(day.year, day.month)] += earned
        rollover_tax, reapplications = _rollover_matured_lots(lots, day, cdi_percent)
        tax_paid += rollover_tax
        monthly_reapplications[(day.year, day.month)].extend(reapplications)
        if include_monthly_balances and (
            day == end or day.month != (day + timedelta(days=1)).month
        ):
            summary = _summarize_lots(lots, day, tax_paid, deposited_total, iof_paid)
            monthly_balances.append(
                MonthlyBalance(
                    month=f"{day.year}-{day.month:02d}",
                    yield_amount=monthly_yields[(day.year, day.month)],
                    gross_balance=summary.gross_balance,
                    net_balance=summary.net_balance,
                    tax_estimated=summary.tax_estimated,
                    tax_paid=summary.tax_paid,
                    reapplications=monthly_reapplications[(day.year, day.month)],
                    invested=summary.invested,
                )
            )
        day += timedelta(days=1)

    return _summarize_lots(lots, end, tax_paid, deposited_total, iof_paid), monthly_balances


def simulate_lots(
    flows: list[Flow],
    rates: dict[date, Decimal],
    cdi_percent: Decimal,
    start: date,
    end: date,
) -> TaxSummary:
    return _simulate_lots(flows, rates, cdi_percent, start, end, False)[0]


def monthly_lot_balances(
    flows: list[Flow],
    rates: dict[date, Decimal],
    cdi_percent: Decimal,
    start: date,
    end: date,
) -> list[MonthlyBalance]:
    return _simulate_lots(flows, rates, cdi_percent, start, end, True)[1]
