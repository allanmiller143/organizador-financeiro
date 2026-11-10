import { ArrowDownLeft, ArrowUpRight, GripVertical, Pencil, RotateCcw, Trash2 } from 'lucide-react'
import { useState } from 'react'

import type { Transaction } from '../../api/types'
import { formatDate, formatMoney } from '../../lib/format'
import type { HistoryEntry } from './types'

type TransactionListProps = {
  entries: HistoryEntry[]
  onDelete: (transaction: Transaction) => void
  onEdit: (transaction: Transaction) => void
  onReorder: (kind: 'transaction' | 'reapplication', occurredOn: string, ids: string[]) => void
  disabled: boolean // true enquanto algo está sendo apagado
}

export function TransactionList({ entries, onDelete, onEdit, onReorder, disabled }: TransactionListProps) {
  const [draggedId, setDraggedId] = useState<string | null>(null)

  function reorderAt(targetId: string) {
    if (!draggedId || draggedId === targetId) return
    const dragged = entries.find((entry) => entry.id === draggedId)
    const target = entries.find((entry) => entry.id === targetId)
    // A ordem do cálculo depende de todos os lançamentos do dia, não apenas
    // de depósitos ou apenas de saques. Reaplicações continuam sendo uma
    // lista separada, mas depósitos e retiradas precisam poder ser misturados.
    if (!dragged || !target || dragged.type !== target.type) return
    if (dragged.occurred_on !== target.occurred_on) return
    const sameDay = entries.filter((entry) =>
      entry.type === dragged.type && entry.occurred_on === target.occurred_on,
    )
    const ids = sameDay
      .map((entry) => entry.type === 'transaction' ? entry.transaction.id : entry.reapplication.source_transaction_id)
      .filter((id): id is string => id !== null)
    const draggedKey = dragged.type === 'transaction' ? dragged.transaction.id : dragged.reapplication.source_transaction_id
    const targetKey = target.type === 'transaction' ? target.transaction.id : target.reapplication.source_transaction_id
    if (!draggedKey || !targetKey) return
    const from = ids.indexOf(draggedKey)
    const to = ids.indexOf(targetKey)
    if (from < 0 || to < 0) return
    ids.splice(from, 1)
    ids.splice(to, 0, draggedKey)
    onReorder(dragged.type, target.occurred_on, ids)
    setDraggedId(null)
  }

  return (
    <ul className="-mx-2 space-y-0.5">
      {entries.map((entry) => {
        if (entry.type === 'reapplication') {
          const event = entry.reapplication
          return (
            <li
              key={entry.id}
              draggable={!disabled && event.source_transaction_id !== null}
              onDragStart={() => setDraggedId(entry.id)}
              onDragOver={(dragEvent) => {
                if (draggedId && draggedId !== entry.id) dragEvent.preventDefault()
              }}
              onDrop={() => reorderAt(entry.id)}
              onDragEnd={() => setDraggedId(null)}
              className="flex items-center gap-3 rounded-xl px-2 py-2.5 transition hover:bg-slate-50"
            >
              <span className="cursor-grab text-slate-300" title="Arraste para reordenar nesta data">
                <GripVertical size={16} />
              </span>
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-indigo-50 text-indigo-600">
                <RotateCcw size={18} />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-900">Reaplicação automática</p>
                <p className="text-xs leading-relaxed text-slate-500">
                  {formatDate(event.occurred_on)} · Vencimento de 2 anos · Rendeu{' '}
                  {formatMoney(event.gross_yield)} · IR {formatMoney(event.tax_paid)}
                </p>
              </div>
              <span className="shrink-0 text-right">
                <span className="block text-sm font-semibold tabular-nums text-slate-500">
                  {formatMoney(event.amount)}
                </span>
                <span className="block text-xs text-slate-400">reaplicado, não é aporte</span>
              </span>
            </li>
          )
        }

        const transaction = entry.transaction
        const isDeposit = transaction.kind === 'DEPOSIT'
        const Icon = isDeposit ? ArrowDownLeft : ArrowUpRight

        return (
          <li
            key={entry.id}
            draggable={!disabled}
            onDragStart={() => setDraggedId(entry.id)}
            onDragOver={(event) => {
              if (draggedId && entry.transaction.occurred_on === entries.find((item) => item.id === draggedId)?.occurred_on) {
                event.preventDefault()
              }
            }}
            onDrop={() => reorderAt(entry.id)}
            onDragEnd={() => setDraggedId(null)}
            className="flex items-center gap-3 rounded-xl px-2 py-2.5 transition hover:bg-slate-50"
          >
            <span className="cursor-grab text-slate-300" title="Arraste para reordenar neste dia">
              <GripVertical size={16} />
            </span>
            <span
              className={`grid h-10 w-10 shrink-0 place-items-center rounded-full ${
                isDeposit ? 'bg-teal-50 text-teal-600' : 'bg-rose-50 text-rose-500'
              }`}
            >
              <Icon size={18} />
            </span>

            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-slate-900">
                {isDeposit ? 'Aporte' : 'Retirada'}
              </p>
              <p className="truncate text-xs text-slate-500">
                {formatDate(transaction.occurred_on)}
                {transaction.note ? ` · ${transaction.note}` : ''}
              </p>
            </div>

            <span
              className={`text-sm font-semibold tabular-nums ${
                isDeposit ? 'text-teal-700' : 'text-slate-700'
              }`}
            >
              {isDeposit ? '+' : '−'} {formatMoney(transaction.amount)}
            </span>

            <button
              onClick={() => onEdit(transaction)}
              disabled={disabled}
              aria-label={isDeposit ? 'Editar aporte' : 'Editar retirada'}
              title={isDeposit ? 'Editar aporte' : 'Editar retirada'}
              className="grid h-9 w-9 shrink-0 cursor-pointer place-items-center rounded-lg text-slate-400 transition hover:bg-teal-50 hover:text-teal-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Pencil size={16} />
            </button>
            <button
              onClick={() => onDelete(transaction)}
              disabled={disabled}
              aria-label="Apagar lançamento"
              title="Apagar"
              className="grid h-9 w-9 shrink-0 cursor-pointer place-items-center rounded-lg text-slate-400 transition hover:bg-red-50 hover:text-red-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Trash2 size={16} />
            </button>
          </li>
        )
      })}
    </ul>
  )
}
