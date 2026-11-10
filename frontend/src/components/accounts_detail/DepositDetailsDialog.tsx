import { useMemo, useState, type ReactNode } from 'react'
import {
  ArrowDownToLine,
  CalendarDays,
  ChevronDown,
  CircleDollarSign,
  Download,
  Layers3,
  LockKeyhole,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react'
import { Drawer } from '../Drawer'
import { formatDate, formatMoney } from '../../lib/format'
import type { DepositDetail, DepositDetails } from '../../api/types'
import { accountsApi } from '../../api/accounts'

type DepositDetailsDialogProps = {
  open: boolean
  onClose: () => void
  details: DepositDetails | undefined
  isPending: boolean
  isError: boolean
}
type DepositFilter = 'all' | 'withdrawals' | 'locked'

export function DepositDetailsDialog({ open, onClose, details, isPending, isError }: DepositDetailsDialogProps) {
  const [filter, setFilter] = useState<DepositFilter>('all')
  const [expandedWithdrawals, setExpandedWithdrawals] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)
  const deposits = useMemo(() => [...(details?.deposits ?? [])].reverse(), [details?.deposits])
  const visibleDeposits = deposits.filter((deposit) => filter === 'withdrawals' ? deposit.withdrawals.length > 0 : filter === 'locked' ? deposit.locked : true)
  const totals = useMemo(() => deposits.reduce((total, deposit) => ({
    balance: total.balance + Number(deposit.gross_balance),
    yield: total.yield + Number(deposit.gross_yield),
    withdrawals: total.withdrawals + Number(deposit.partial_withdrawals),
    taxes: total.taxes + Number(deposit.income_tax) + Number(deposit.iof) + Number(deposit.iof_estimated),
  }), { balance: 0, yield: 0, withdrawals: 0, taxes: 0 }), [deposits])

  return (
    <Drawer open={open} onClose={onClose} title="Detalhes dos depósitos" subtitle={details ? `Atualizado até ${formatDate(details.as_of)} · ${deposits.length} lotes ativos` : 'Composição individual dos lotes'} icon={Layers3}>
      {isPending && <p className="rounded-2xl bg-white p-5 text-sm text-slate-500 ring-1 ring-slate-200">Calculando cada depósito...</p>}
      {isError && <p className="rounded-2xl bg-rose-50 p-5 text-sm text-rose-700 ring-1 ring-rose-200">Não foi possível carregar os detalhes.</p>}
      {!isPending && !isError && deposits.length === 0 && <p className="rounded-2xl bg-white p-5 text-sm text-slate-500 ring-1 ring-slate-200">Ainda não há depósitos para detalhar.</p>}
      {!isPending && !isError && deposits.length > 0 && (
        <div className="space-y-5">
          <section className="grid grid-cols-2 gap-3 sm:grid-cols-4" aria-label="Resumo dos depósitos">
            <SummaryMetric icon={CircleDollarSign} label="Saldo bruto" value={formatMoney(String(totals.balance))} tone="teal" />
            <SummaryMetric icon={TrendingUp} label="Rendimento bruto" value={formatMoney(String(totals.yield))} tone="indigo" />
            <SummaryMetric icon={ArrowDownToLine} label="Saques" value={formatMoney(String(totals.withdrawals))} tone="rose" />
            <SummaryMetric icon={ShieldCheck} label="IR + IOF para resgate hoje" value={formatMoney(String(totals.taxes))} tone="amber" />
          </section>
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-white p-3 ring-1 ring-slate-200">
            <div><p className="text-sm font-semibold text-slate-900">Lotes ativos</p><p className="text-xs text-slate-500">Cada aporte aparece separado, como no Nubank.</p></div>
            <button type="button" disabled={isExporting || !details?.account_id} onClick={async () => { if (!details?.account_id) return; setIsExporting(true); try { const blob = await accountsApi.depositDetailsCsv(details.account_id); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = 'detalhes-depositos-caixinha.csv'; link.click(); URL.revokeObjectURL(url) } finally { setIsExporting(false) } }} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:border-teal-300 hover:text-teal-700 disabled:cursor-wait disabled:opacity-60"><Download size={15} /> {isExporting ? 'Gerando CSV...' : 'Exportar detalhes'}</button>
            <div className="flex gap-1 rounded-xl bg-slate-100 p-1" role="tablist" aria-label="Filtrar depósitos">
              <FilterButton active={filter === 'all'} onClick={() => setFilter('all')}>Todos ({deposits.length})</FilterButton>
              <FilterButton active={filter === 'withdrawals'} onClick={() => setFilter('withdrawals')}>Com saques</FilterButton>
              <FilterButton active={filter === 'locked'} onClick={() => setFilter('locked')}>Trancados</FilterButton>
            </div>
          </div>
          {visibleDeposits.length === 0 ? <p className="rounded-2xl bg-white p-5 text-center text-sm text-slate-500 ring-1 ring-slate-200">Nenhum depósito corresponde a este filtro.</p> : <div className="space-y-4">{visibleDeposits.map((deposit, index) => { const key = `${deposit.deposited_on}-${deposit.applied_amount}-${index}`; const showWithdrawals = expandedWithdrawals === key; return <DepositCard key={key} deposit={deposit} number={deposits.length - deposits.indexOf(deposit)} showWithdrawals={showWithdrawals} onToggleWithdrawals={() => setExpandedWithdrawals(showWithdrawals ? null : key)} /> })}</div>}
        </div>
      )}
    </Drawer>
  )
}

function DepositCard({ deposit, number, showWithdrawals, onToggleWithdrawals }: { deposit: DepositDetail; number: number; showWithdrawals: boolean; onToggleWithdrawals: () => void }) {
  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white p-4 sm:p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-teal-50 text-teal-700 ring-1 ring-teal-100"><Layers3 size={19} /></span><div><p className="text-[11px] font-bold uppercase tracking-[0.14em] text-slate-400">Lote {number}</p><p className="mt-0.5 text-base font-bold text-slate-900">{formatDate(deposit.deposited_on)}</p><p className="mt-0.5 text-xs text-slate-500">Aportado: <strong className="text-slate-700">{formatMoney(deposit.applied_amount)}</strong></p></div></div>
          <div className="flex items-center gap-2"><span className="rounded-full bg-teal-50 px-2.5 py-1 text-xs font-semibold text-teal-700">{deposit.cdi_percent}% CDI</span>{deposit.locked ? <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700"><LockKeyhole size={13} /> Trancado</span> : <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">Liquidez</span>}</div>
        </div>
        <div className="mt-4 rounded-xl bg-slate-900 px-4 py-3 text-white sm:flex sm:items-end sm:justify-between sm:gap-4"><div><p className="text-[11px] font-medium uppercase tracking-[0.12em] text-white/60">Saldo atual bruto</p><p className="mt-1 text-2xl font-bold tracking-tight tabular-nums">{formatMoney(deposit.gross_balance)}</p></div><div className="mt-2 text-left sm:mt-0 sm:text-right"><p className="text-[11px] text-white/60">Saldo líquido estimado</p><p className="mt-0.5 text-sm font-semibold tabular-nums text-emerald-300">{formatMoney(deposit.net_balance)}</p></div></div>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-4 p-4 sm:grid-cols-5 sm:p-5"><Metric label="Rendimento bruto" value={formatMoney(deposit.gross_yield)} accent="text-indigo-700" /><Metric label="Principal restante" value={formatMoney(deposit.principal_remaining)} /><Metric label="Saques parciais" value={formatMoney(deposit.partial_withdrawals)} accent={Number(deposit.partial_withdrawals) > 0 ? 'text-rose-700' : undefined} /><Metric label="IR" value={formatMoney(deposit.income_tax)} accent="text-amber-700" /><Metric label="IOF pago / hoje" value={`${formatMoney(deposit.iof)} / ${formatMoney(deposit.iof_estimated)}`} accent="text-amber-700" /></div>
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 px-4 py-3 text-xs text-slate-500 sm:px-5"><span className="inline-flex items-center gap-1.5"><CalendarDays size={14} /> Vence em {formatDate(deposit.maturity_on)}</span><span>{deposit.product}</span></div>
      {deposit.withdrawals.length > 0 && <div className="border-t border-slate-100"><button type="button" onClick={onToggleWithdrawals} className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm font-semibold text-slate-700 transition hover:bg-slate-50 sm:px-5"><span>{deposit.withdrawals.length} {deposit.withdrawals.length === 1 ? 'saque detalhado' : 'saques detalhados'}</span><ChevronDown size={17} className={`text-slate-400 transition-transform ${showWithdrawals ? 'rotate-180' : ''}`} /></button>{showWithdrawals && <div className="border-t border-slate-100 bg-slate-50 px-4 py-2 sm:px-5">{deposit.withdrawals.map((withdrawal, withdrawalIndex) => <div key={`${withdrawal.occurred_on}-${withdrawal.amount}-${withdrawalIndex}`} className="grid gap-2 border-b border-slate-200 py-3 text-xs last:border-0 sm:grid-cols-[1fr_auto] sm:items-center"><div><p className="font-semibold text-slate-800">{formatDate(withdrawal.occurred_on)} · {formatMoney(withdrawal.amount)}</p><p className="mt-0.5 text-slate-500">Rendimento resgatado: {formatMoney(withdrawal.gross_yield)}</p></div><div className="tabular-nums text-slate-500 sm:text-right">IR {formatMoney(withdrawal.income_tax)} · IOF {formatMoney(withdrawal.iof)}<br /><strong className="text-slate-700">Líquido {formatMoney(withdrawal.net_amount)}</strong></div></div>)}</div>}</div>}
    </article>
  )
}

function SummaryMetric({ icon: Icon, label, value, tone }: { icon: typeof CircleDollarSign; label: string; value: string; tone: 'teal' | 'indigo' | 'rose' | 'amber' }) {
  const colors = { teal: 'bg-teal-50 text-teal-700', indigo: 'bg-indigo-50 text-indigo-700', rose: 'bg-rose-50 text-rose-700', amber: 'bg-amber-50 text-amber-700' }
  return <div className="rounded-2xl bg-white p-3 ring-1 ring-slate-200"><span className={`mb-2 grid h-7 w-7 place-items-center rounded-lg ${colors[tone]}`}><Icon size={15} /></span><p className="text-[11px] text-slate-500">{label}</p><p className="mt-0.5 truncate text-sm font-bold tabular-nums text-slate-900">{value}</p></div>
}
function FilterButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return <button type="button" role="tab" aria-selected={active} onClick={onClick} className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold transition ${active ? 'bg-white text-teal-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>{children}</button>
}
function Metric({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return <div><p className="text-[11px] text-slate-500">{label}</p><p className={`mt-1 text-sm font-bold tabular-nums ${accent ?? 'text-slate-800'}`}>{value}</p></div>
}
