import { Link } from 'react-router-dom'
import { Archive, ChevronRight, PiggyBank, Trash2 } from 'lucide-react'

import type { Account } from '../../api/types'
import { formatCdi, formatDate, formatMoney } from '../../lib/format'

type AccountRowProps = {
  account: Account
  balance?: string // o saldo bruto, se já foi calculado
  onDelete: () => void
  disabled: boolean
}

export function AccountRow({ account, balance, onDelete, disabled }: AccountRowProps) {
  const Icon = account.is_active ? PiggyBank : Archive

  return (
    <li className="flex items-center gap-1 p-2">
      <Link
        to={`/caixinhas/${account.id}`}
        className="group flex min-w-0 flex-1 items-center gap-4 rounded-xl p-3 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500"
      >
        <span
          className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${
            account.is_active ? 'bg-teal-50 text-teal-600' : 'bg-slate-100 text-slate-500'
          }`}
        >
          <Icon size={20} />
        </span>

        <div className="min-w-0 flex-1">
          <p className="truncate font-medium text-slate-900">{account.name}</p>
          <div className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-slate-500">
            <span>{account.institution}</span>
            <span className="rounded-full bg-sky-50 px-2 py-0.5 font-medium text-sky-700">
              {formatCdi(account.cdi_percent)}
            </span>
            <span>aberta em {formatDate(account.opened_on)}</span>
          </div>
        </div>

        {account.is_active ? (
          <span className="font-semibold tabular-nums text-slate-900">
            {balance ? formatMoney(balance) : '—'}
          </span>
        ) : (
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
            Arquivada
          </span>
        )}

        <ChevronRight
          size={18}
          className="shrink-0 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-teal-600"
        />
      </Link>

      <button
        onClick={onDelete}
        disabled={disabled}
        aria-label={`Apagar a caixinha ${account.name}`}
        title="Apagar"
        className="grid h-10 w-10 shrink-0 cursor-pointer place-items-center rounded-xl text-slate-400 transition hover:bg-red-50 hover:text-red-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Trash2 size={18} />
      </button>
    </li>
  )
}