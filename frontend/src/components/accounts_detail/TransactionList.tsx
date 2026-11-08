import { ArrowDownLeft, ArrowUpRight, Trash2 } from 'lucide-react'

import type { Transaction } from '../../api/types'
import { formatDate, formatMoney } from '../../lib/format'

type TransactionListProps = {
  transactions: Transaction[]
  onDelete: (transaction: Transaction) => void
  disabled: boolean // true enquanto algo está sendo apagado
}

export function TransactionList({ transactions, onDelete, disabled }: TransactionListProps) {
  return (
    <ul className="-mx-2 space-y-0.5">
      {transactions.map((transaction) => {
        const isDeposit = transaction.kind === 'DEPOSIT'
        const Icon = isDeposit ? ArrowDownLeft : ArrowUpRight

        return (
          <li
            key={transaction.id}
            className="flex items-center gap-3 rounded-xl px-2 py-2.5 transition hover:bg-slate-50"
          >
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