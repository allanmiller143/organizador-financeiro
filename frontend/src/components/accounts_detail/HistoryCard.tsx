import { useMemo, useState } from 'react'
import { ChevronDown, Download, History, Plus, Receipt } from 'lucide-react'

import { describeError } from '../../lib/errors'
import { formatDate, formatMoney } from '../../lib/format'
import { Button } from '../Button'
import { InsightCard } from '../dashboard/InsightCard'
import { ErrorMessage } from '../ErrorMessage'
import { LoadingState } from '../LoadingState'
import type { Transaction } from '../../api/types'
import type {
  DeleteTransactionMutation,
  HistoryEntry,
  MonthlyQuery,
  ReorderTransactionsMutation,
  ReorderReapplicationsMutation,
  TransactionsQuery,
  UpdateTransactionMutation,
} from './types'
import { EditTransactionDialog } from './EditTransactionDialog'
import { TransactionList } from './TransactionList'
import { ConfirmDialog } from '../ConfirmDialog'
import { accountsApi } from '../../api/accounts'

const PREVIEW_COUNT = 3 // quantos lançamentos aparecem sem expandir
type HistoryFilter = 'all' | 'deposit' | 'withdrawal' | 'reapplication'

const MONTH_NAMES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

function formatHistoryDateHeading(iso: string) {
  const [year, month, day] = iso.split('-')
  return `${day} ${MONTH_NAMES[Number(month) - 1]} ${year}`
}

type HistoryCardProps = {
  accountId: string
  transactions: TransactionsQuery
  monthly: MonthlyQuery
  deleteTransaction: DeleteTransactionMutation
  updateTransaction: UpdateTransactionMutation
  reorderTransactions: ReorderTransactionsMutation
  reorderReapplications: ReorderReapplicationsMutation
  accountCdiPercent: string
  openedOn: string
  onNew: () => void
}

export function HistoryCard({
  accountId,
  transactions,
  monthly,
  deleteTransaction,
  updateTransaction,
  reorderTransactions,
  reorderReapplications,
  accountCdiPercent,
  openedOn,
  onNew,
}: HistoryCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [filter, setFilter] = useState<HistoryFilter>('all')
  const [editingDeposit, setEditingDeposit] = useState<Transaction | null>(null)
  const [transactionToDelete, setTransactionToDelete] = useState<Transaction | null>(null)
  const [isExporting, setIsExporting] = useState(false)

  const entries = useMemo<HistoryEntry[]>(() => {
    const transactionEntries: HistoryEntry[] = (transactions.data ?? []).map((transaction) => ({
      type: 'transaction',
      transaction,
      occurred_on: transaction.occurred_on,
      id: `transaction-${transaction.id}`,
    }))
    const reapplicationEntries: HistoryEntry[] = (monthly.data?.months ?? []).flatMap(
      (month, monthIndex) =>
        (month.reapplications ?? []).map((reapplication, eventIndex) => ({
          type: 'reapplication' as const,
          reapplication,
          occurred_on: reapplication.occurred_on,
          id: `reapplication-${reapplication.source_transaction_id ?? `${monthIndex}-${eventIndex}`}-${reapplication.occurred_on}`,
        })),
    )
    return [...transactionEntries, ...reapplicationEntries].sort((a, b) => {
      const byDate = b.occurred_on.localeCompare(a.occurred_on)
      if (byDate !== 0) return byDate
      if (a.type === 'transaction' && b.type === 'transaction') {
        const aOrder = a.transaction.sort_order ?? Number.MAX_SAFE_INTEGER
        const bOrder = b.transaction.sort_order ?? Number.MAX_SAFE_INTEGER
        // sort_order é a ordem operacional persistida e vale tanto para a
        // tela quanto para o motor e para o CSV.
        return aOrder - bOrder
      }
      return 0
    })
  }, [transactions.data, monthly.data])

  const deposits = (transactions.data ?? []).filter((item) => item.kind === 'DEPOSIT').length
  const withdrawals = (transactions.data ?? []).filter((item) => item.kind === 'WITHDRAWAL').length
  const reapplications = entries.filter((entry) => entry.type === 'reapplication').length
  const filteredEntries = entries.filter((entry) => {
    if (filter === 'all') return true
    if (filter === 'reapplication') return entry.type === 'reapplication'
    return entry.type === 'transaction' && entry.transaction.kind === filter.toUpperCase()
  })
  function handleReorder(kind: 'transaction' | 'reapplication', occurredOn: string, visibleIds: string[]) {
    if (kind === 'reapplication') {
      const allIds = (monthly.data?.months ?? [])
        .flatMap((month) => month.reapplications ?? [])
        .filter((reapplication) => reapplication.occurred_on === occurredOn)
        .map((reapplication) => reapplication.source_transaction_id)
        .filter((id): id is string => id !== null)
      const reordered = [...visibleIds, ...allIds.filter((id) => !visibleIds.includes(id))]
      reorderReapplications.mutate(reordered)
      return
    }
    const allIds = (transactions.data ?? [])
      .filter((transaction) => transaction.occurred_on === occurredOn)
      .map((transaction) => transaction.id)
    const visualOrder = [...visibleIds, ...allIds.filter((id) => !visibleIds.includes(id))]
    reorderTransactions.mutate(visualOrder)
  }
  const showAllFiltered = expanded || filter === 'reapplication'
  const visible = showAllFiltered ? filteredEntries : filteredEntries.slice(0, PREVIEW_COUNT)
  const visibleGroups = visible.reduce<Array<{ date: string; entries: HistoryEntry[] }>>((groups, entry) => {
    const current = groups[groups.length - 1]
    if (current?.date === entry.occurred_on) {
      current.entries.push(entry)
    } else {
      groups.push({ date: entry.occurred_on, entries: [entry] })
    }
    return groups
  }, [])
  const canExpand = filter !== 'reapplication' && filteredEntries.length > PREVIEW_COUNT

  // Reaplicação não é lançamento seu: só aportes e retiradas entram na contagem.
  const launches = deposits + withdrawals
  const subtitle =
    transactions.data === undefined
      ? 'Aportes, retiradas e reaplicações desta caixinha'
      : `${launches} ${launches === 1 ? 'lançamento' : 'lançamentos'}`

  return (
    <InsightCard
      icon={History}
      title="Histórico"
      subtitle={subtitle}
      action={
        <div className="flex flex-wrap items-center justify-end gap-2">
          {entries.length > 0 && <button type="button" onClick={onNew} className="inline-flex shrink-0 cursor-pointer items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-teal-700 ring-1 ring-teal-200 transition hover:bg-teal-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500"><Plus size={16} />Lançamento</button>}
          <button type="button" disabled={isExporting} onClick={async () => { setIsExporting(true); try { const blob = await accountsApi.historyCsv(accountId); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = 'historico-movimentacoes-caixinha.csv'; link.click(); URL.revokeObjectURL(url) } finally { setIsExporting(false) } }} className="inline-flex shrink-0 cursor-pointer items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-50 disabled:cursor-wait disabled:opacity-60"><Download size={16} />{isExporting ? 'Gerando...' : 'Exportar histórico'}</button>
        </div>
      }
    >
      <div className="mt-4">
        {deleteTransaction.isError && (
          <div className="mb-3">
            <ErrorMessage message={describeError(deleteTransaction.error)} />
          </div>
        )}

        {transactions.isPending && <LoadingState message="Carregando..." />}

        {transactions.isError && <ErrorMessage message={describeError(transactions.error)} />}
        {monthly.isError && (
          <div className="mb-3">
            <ErrorMessage
              message={`Não foi possível carregar as reaplicações: ${describeError(monthly.error)}`}
            />
          </div>
        )}

        {/* Vazio */}
        {transactions.data && entries.length === 0 && (
          <div className="flex flex-col items-center gap-3 py-8 text-center">
            <span className="grid h-12 w-12 place-items-center rounded-full bg-teal-50 text-teal-600">
              <Receipt size={24} />
            </span>
            <p className="text-sm text-slate-500">Nenhum lançamento ainda.</p>
            <Button variant="primary" onClick={onNew}>
              Registrar o primeiro aporte
            </Button>
          </div>
        )}

        {/* Com dados: resumo + lista expansível */}
        {entries.length > 0 && (
          <>
            <div className="mb-3 flex flex-wrap gap-2">
              {deposits > 0 && (
                <span className="rounded-full bg-teal-50 px-2.5 py-1 text-xs font-medium text-teal-700">
                  {deposits} {deposits === 1 ? 'aporte' : 'aportes'}
                </span>
              )}
              {withdrawals > 0 && (
                <span className="rounded-full bg-rose-50 px-2.5 py-1 text-xs font-medium text-rose-600">
                  {withdrawals} {withdrawals === 1 ? 'retirada' : 'retiradas'}
                </span>
              )}
              {reapplications > 0 && (
                <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700">
                  {reapplications} {reapplications === 1 ? 'reaplicação' : 'reaplicações'}
                </span>
              )}
            </div>

            <label className="mb-3 flex items-center gap-2 text-sm text-slate-600">
              <span>Mostrar</span>
              <select
                aria-label="Filtrar histórico"
                value={filter}
                onChange={(event) => {
                  setFilter(event.target.value as HistoryFilter)
                  setExpanded(event.target.value === 'reapplication')
                }}
                className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
              >
                <option value="all">Tudo</option>
                <option value="deposit">Aportes</option>
                <option value="withdrawal">Retiradas</option>
                <option value="reapplication">Reaplicações</option>
              </select>
            </label>

            {/* Expandido: a lista rola dentro do cartão, para não ficar enorme */}
            {filteredEntries.length === 0 ? (
              monthly.isPending && filter === 'reapplication' ? (
                <LoadingState message="Buscando reaplicações..." />
              ) : (
                <p className="py-6 text-center text-sm text-slate-500">
                  Nenhum item neste filtro.
                </p>
              )
            ) : (
              <div
                className={`-mx-2 px-2 ${
                  showAllFiltered ? 'max-h-96 overflow-y-auto' : ''
                }`}
              >
                <div className="space-y-4">
                  {visibleGroups.map((group) => (
                    <section key={group.date} aria-label={`Lançamentos de ${formatDate(group.date)}`}>
                      <div className="mb-1 flex items-center gap-3 px-2">
                        <span className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">
                          {formatHistoryDateHeading(group.date)}
                        </span>
                        <span className="h-px flex-1 bg-slate-100" />
                      </div>
                      <TransactionList
                        entries={group.entries}
                        disabled={deleteTransaction.isPending || updateTransaction.isPending}
                        onEdit={setEditingDeposit}
                        onReorder={handleReorder}
                        onDelete={setTransactionToDelete}
                      />
                    </section>
                  ))}
                </div>
              </div>
            )}

            {canExpand && (
              <button
                type="button"
                onClick={() => setExpanded((value) => !value)}
                aria-expanded={expanded}
                className="mt-3 flex w-full cursor-pointer items-center justify-center gap-1.5 rounded-xl py-2 text-sm font-medium text-teal-700 transition hover:bg-teal-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500"
              >
                {expanded ? 'Mostrar menos' : `Ver todos os ${filteredEntries.length} lançamentos`}
                <ChevronDown
                  size={16}
                  className={`transition-transform ${expanded ? 'rotate-180' : ''}`}
                />
              </button>
            )}
          </>
        )}
      </div>
      <EditTransactionDialog
        transaction={editingDeposit}
        accountCdiPercent={accountCdiPercent}
        openedOn={openedOn}
        updateTransaction={updateTransaction}
        onClose={() => setEditingDeposit(null)}
      />
      <ConfirmDialog
        open={transactionToDelete !== null}
        title="Excluir lançamento?"
        message={transactionToDelete ? `O ${transactionToDelete.kind === 'DEPOSIT' ? 'aporte' : 'saque'} de ${formatMoney(transactionToDelete.amount)} será removido do histórico e os cálculos serão refeitos.` : ''}
        loading={deleteTransaction.isPending}
        onClose={() => setTransactionToDelete(null)}
        onConfirm={() => {
          if (!transactionToDelete) return
          deleteTransaction.mutate(transactionToDelete.id, { onSettled: () => setTransactionToDelete(null) })
        }}
      />
    </InsightCard>
  )
}
