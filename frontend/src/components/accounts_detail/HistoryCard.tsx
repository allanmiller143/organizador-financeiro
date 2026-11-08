import { useMemo, useState } from 'react'
import { ChevronDown, History, Plus, Receipt } from 'lucide-react'

import { describeError } from '../../lib/errors'
import { Button } from '../Button'
import { InsightCard } from '../dashboard/InsightCard'
import { ErrorMessage } from '../ErrorMessage'
import { LoadingState } from '../LoadingState'
import type { DeleteTransactionMutation, TransactionsQuery } from './types'
import { TransactionList } from './TransactionList'

const PREVIEW_COUNT = 3 // quantos lançamentos aparecem sem expandir

type HistoryCardProps = {
  transactions: TransactionsQuery
  deleteTransaction: DeleteTransactionMutation
  onNew: () => void
}

export function HistoryCard({ transactions, deleteTransaction, onNew }: HistoryCardProps) {
  const [expanded, setExpanded] = useState(false)

  // Mais recentes primeiro (só para exibir: "AAAA-MM-DD" ordena como texto).
  const list = useMemo(
    () =>
      [...(transactions.data ?? [])].sort((a, b) => b.occurred_on.localeCompare(a.occurred_on)),
    [transactions.data],
  )

  const deposits = list.filter((item) => item.kind === 'DEPOSIT').length
  const withdrawals = list.length - deposits
  const visible = expanded ? list : list.slice(0, PREVIEW_COUNT)
  const canExpand = list.length > PREVIEW_COUNT

  const subtitle =
    transactions.data === undefined
      ? 'Aportes e retiradas desta caixinha'
      : `${list.length} ${list.length === 1 ? 'lançamento' : 'lançamentos'}`

  return (
    <InsightCard
      icon={History}
      title="Histórico"
      subtitle={subtitle}
      action={
        list.length > 0 ? (
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

        {/* Vazio */}
        {transactions.data && list.length === 0 && (
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
        {list.length > 0 && (
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
            </div>

            {/* Expandido: a lista rola dentro do cartão, para não ficar enorme */}
            <div className={`-mx-2 px-2 ${expanded ? 'max-h-96 overflow-y-auto' : ''}`}>
              <TransactionList
                transactions={visible}
                disabled={deleteTransaction.isPending}
                onDelete={(transaction) => {
                  if (window.confirm('Apagar este lançamento?')) {
                    deleteTransaction.mutate(transaction.id)
                  }
                }}
              />
            </div>

            {canExpand && (
              <button
                type="button"
                onClick={() => setExpanded((value) => !value)}
                aria-expanded={expanded}
                className="mt-3 flex w-full cursor-pointer items-center justify-center gap-1.5 rounded-xl py-2 text-sm font-medium text-teal-700 transition hover:bg-teal-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500"
              >
                {expanded ? 'Mostrar menos' : `Ver todos os ${list.length} lançamentos`}
                <ChevronDown
                  size={16}
                  className={`transition-transform ${expanded ? 'rotate-180' : ''}`}
                />
              </button>
            )}
          </>
        )}
      </div>
    </InsightCard>
  )
}