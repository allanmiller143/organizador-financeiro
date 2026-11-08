import { useMemo, useState } from 'react'
import { ChevronDown, History, Plus, Receipt } from 'lucide-react'

import { describeError } from '../../lib/errors'
import { Button } from '../Button'
import { InsightCard } from '../dashboard/InsightCard'
import { ErrorMessage } from '../ErrorMessage'
import { LoadingState } from '../LoadingState'
import type { Transaction } from '../../api/types'
import type {
  DeleteTransactionMutation,
  HistoryEntry,
  MonthlyQuery,
  TransactionsQuery,
  UpdateTransactionMutation,
} from './types'
import { EditTransactionDialog } from './EditTransactionDialog'
import { TransactionList } from './TransactionList'

const PREVIEW_COUNT = 3 // quantos lançamentos aparecem sem expandir
type HistoryFilter = 'all' | 'deposit' | 'withdrawal' | 'reapplication'

type HistoryCardProps = {
  transactions: TransactionsQuery
  monthly: MonthlyQuery
  deleteTransaction: DeleteTransactionMutation
  updateTransaction: UpdateTransactionMutation
  openedOn: string
  onNew: () => void
}

export function HistoryCard({
  transactions,
  monthly,
  deleteTransaction,
  updateTransaction,
  openedOn,
  onNew,
}: HistoryCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [filter, setFilter] = useState<HistoryFilter>('all')
  const [editingDeposit, setEditingDeposit] = useState<Transaction | null>(null)

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
          id: `reapplication-${monthIndex}-${eventIndex}`,
        })),
    )
    return [...transactionEntries, ...reapplicationEntries].sort((a, b) =>
      b.occurred_on.localeCompare(a.occurred_on),
    )
  }, [transactions.data, monthly.data])

  const deposits = (transactions.data ?? []).filter((item) => item.kind === 'DEPOSIT').length
  const withdrawals = (transactions.data ?? []).filter((item) => item.kind === 'WITHDRAWAL').length
  const reapplications = entries.filter((entry) => entry.type === 'reapplication').length
  const filteredEntries = entries.filter((entry) => {
    if (filter === 'all') return true
    if (filter === 'reapplication') return entry.type === 'reapplication'
    return entry.type === 'transaction' && entry.transaction.kind === filter.toUpperCase()
  })
  const showAllFiltered = expanded || filter === 'reapplication'
  const visible = showAllFiltered ? filteredEntries : filteredEntries.slice(0, PREVIEW_COUNT)
  const canExpand = filter !== 'reapplication' && filteredEntries.length > PREVIEW_COUNT

  const subtitle =
    transactions.data === undefined
      ? 'Aportes, retiradas e reaplicações desta caixinha'
      : `${entries.length} ${entries.length === 1 ? 'lançamento' : 'lançamentos'}`

  return (
    <InsightCard
      icon={History}
      title="Histórico"
      subtitle={subtitle}
      action={
        entries.length > 0 ? (
          <button
            type="button"
            onClick={onNew}
            className="inline-flex shrink-0 cursor-pointer items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-teal-700 ring-1 ring-teal-200 transition hover:bg-teal-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500"
          >
            <Plus size={16} />
            Lançamento
          </button>
        ) : undefined
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
                <TransactionList
                  entries={visible}
                  disabled={deleteTransaction.isPending || updateTransaction.isPending}
                  onEdit={setEditingDeposit}
                  onDelete={(transaction) => {
                    if (window.confirm('Apagar este lançamento?')) {
                      deleteTransaction.mutate(transaction.id)
                    }
                  }}
                />
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
        openedOn={openedOn}
        updateTransaction={updateTransaction}
        onClose={() => setEditingDeposit(null)}
      />
    </InsightCard>
  )
}