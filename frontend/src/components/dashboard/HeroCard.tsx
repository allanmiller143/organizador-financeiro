import { Link } from 'react-router-dom'
import { Plus, TrendingUp } from 'lucide-react'

import { formatDate, formatMoney } from '../../lib/format'
import { greeting, summarize } from './helpers'
import type { DashboardData } from './types'

type HeroCardProps = {
  totals: DashboardData['totals']
  asOf: DashboardData['as_of']
  userName?: string
}

export function HeroCard({ totals, asOf, userName }: HeroCardProps) {
  const { yieldLabel } = summarize(totals)
  const firstName = userName?.trim().split(/\s+/)[0] ?? ''

  return (
    <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-sky-500 to-teal-600 p-6 text-white shadow-lg sm:p-8">
      <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-white/10" />
      <div className="pointer-events-none absolute -bottom-24 right-24 h-56 w-56 rounded-full bg-white/10" />

      <div className="relative space-y-6">
        <p className="text-sm text-white/80">
          {greeting()}
          {firstName && `, ${firstName}`}
        </p>

        <div className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end">
          <div>
            <p className="text-sm text-white/80">
              Saldo bruto <span className="text-white/60">· antes do IR</span>
            </p>
            <p className="mt-1 text-4xl font-semibold tabular-nums sm:text-5xl">
              {formatMoney(totals.gross_balance)}
            </p>
          </div>

          <div className="rounded-2xl bg-white/15 px-5 py-4 ring-1 ring-white/30">
            <p className="text-sm text-white/80">
              Saldo líquido <span className="text-white/60">· após o IR</span>
            </p>
            <p className="mt-1 text-2xl font-semibold tabular-nums sm:text-3xl">
              {formatMoney(totals.net_balance)}
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded-full bg-white/20 px-2.5 py-1 text-xs font-medium">
              <TrendingUp size={14} />
              {yieldLabel} de rendimento
            </span>
            {asOf && (
              <span className="text-xs text-white/70">Atualizado até {formatDate(asOf)}</span>
            )}
          </div>

          <div className="flex flex-wrap gap-2">
            <Link
              to="/caixinhas"
              className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-teal-700 shadow-sm transition hover:bg-teal-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-teal-600"
            >
              <Plus size={16} />
              Nova caixinha
            </Link>
            <Link
              to="/projecao"
              className="inline-flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2.5 text-sm font-semibold text-white ring-1 ring-white/40 transition hover:bg-white/25 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
            >
              <TrendingUp size={16} />
              Ver projeção
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}