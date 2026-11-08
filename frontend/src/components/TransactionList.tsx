import type { Transaction } from '../api/types'
import { formatDate, formatMoney } from '../lib/format'

type TransactionListProps = {
  transactions: Transaction[]
  onDelete: (transaction: Transaction) => void
  disabled: boolean // true enquanto algo está sendo apagado
}

export function TransactionList({ transactions, onDelete, disabled }: TransactionListProps) {
  return (
    <ul className="divide-y divide-slate-100">
      {transactions.map((transaction) => {
        const isDeposit = transaction.kind === 'DEPOSIT'
        return (
          <li key={transaction.id} className="flex items-center justify-between gap-4 py-3">
            <div>
              <p className="text-sm font-medium">{isDeposit ? 'Aporte' : 'Retirada'}</p>
              <p className="text-xs text-slate-500">
                {formatDate(transaction.occurred_on)}
                {transaction.note ? ` · ${transaction.note}` : ''}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <span
                className={`text-sm font-medium tabular-nums ${
                  isDeposit ? 'text-emerald-700' : 'text-slate-700'
                }`}
              >
                {isDeposit ? '+' : '−'} {formatMoney(transaction.amount)}
              </span>
              <button
                onClick={() => onDelete(transaction)}
                disabled={disabled}
                className="text-xs text-red-600 hover:text-red-800 disabled:opacity-50"
              >
                Apagar
              </button>
            </div>
          </li>
        )
      })}
    </ul>
  )
}