import { Link } from 'react-router-dom'
import { ArrowRight, ChevronRight, PiggyBank } from 'lucide-react'

import { formatMoney, formatPercent } from '../../lib/format'
import { SplitBar } from './SplitBar'
import { accountColor } from './helpers'
import type { Account } from './types'

export function AccountsCard({ accounts }: { accounts: Account[] }) {
  return (
    <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-slate-900">
          Suas caixinhas
          {accounts.length > 0 && (
            <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 align-middle text-xs font-medium text-slate-600">
              {accounts.length}
            </span>
          )}
        </h2>
        {accounts.length > 0 && (
          <Link
            to="/caixinhas"
            className="group inline-flex items-center gap-1 text-sm font-medium text-teal-700 transition hover:text-teal-800"
          >
            Gerenciar
            <ArrowRight size={16} className="transition-transform group-hover:translate-x-0.5" />
          </Link>
        )}
      </div>

      {/* Vazio */}
      {accounts.length === 0 ? (
        <div className="mt-6 flex flex-col items-center gap-3 py-6 text-center">
          <span className="grid h-12 w-12 place-items-center rounded-full bg-teal-50 text-teal-600">
            <PiggyBank size={24} />
          </span>
          <p className="text-sm text-slate-500">Você ainda não tem caixinhas.</p>
          <Link
            to="/caixinhas"
            className="rounded-xl bg-teal-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-teal-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2"
          >
            Cadastrar a primeira
          </Link>
        </div>
      ) : (
        <>
          {/* Barra de distribuição: um pedaço por caixinha */}
          <SplitBar
            className="mt-5"
            segments={accounts.map((account, index) => ({
              percent: Number(account.share_percent),
              className: accountColor(index),
              title: `${account.name}: ${formatPercent(account.share_percent)}`,
            }))}
          />

          <ul className="-mx-3 mt-4 space-y-1">
            {accounts.map((account, index) => (
              <li key={account.account_id}>
                <Link
                  to={`/caixinhas/${account.account_id}`}
                  className="group flex items-center gap-3 rounded-xl px-3 py-3 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500"
                >
                  <span className={`h-3 w-3 shrink-0 rounded-full ${accountColor(index)}`} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-slate-900">{account.name}</p>
                    <p className="text-xs text-slate-500">{account.institution}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium tabular-nums text-slate-900">
                      {formatMoney(account.gross_balance)}
                    </p>
                    <p className="text-xs text-slate-500">
                      {formatPercent(account.share_percent)} do total
                    </p>
                  </div>
                  <ChevronRight
                    size={18}
                    className="shrink-0 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-teal-600"
                  />
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}