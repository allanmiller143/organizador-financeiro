import { Landmark, TrendingUp, Wallet } from 'lucide-react'

import { describeError } from '../../lib/errors'
import { formatMoney } from '../../lib/format'
import { ErrorMessage } from '../ErrorMessage'
import { StatCard } from '../StatCard'
import { yieldPercentLabel } from './helpers'
import type { SummaryQuery } from './types'

export function SummaryCards({ summary }: { summary: SummaryQuery }) {
  if (summary.isError) {
    return <ErrorMessage message={describeError(summary.error)} />
  }

  if (summary.isPending) {
    return (
      <div className="grid gap-4 sm:grid-cols-3">
        {[0, 1, 2].map((item) => (
          <div
            key={item}
            className="h-28 animate-pulse rounded-2xl bg-white shadow-sm ring-1 ring-slate-200"
          />
        ))}
      </div>
    )
  }

  const data = summary.data

  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <StatCard icon={Wallet} label="Total aportado" value={formatMoney(data.invested)} />
      <StatCard
        icon={TrendingUp}
        label="Rendimento bruto"
        value={formatMoney(data.gross_yield)}
        hint={`${yieldPercentLabel(data.invested, data.gross_yield)} sobre o aportado`}
      />
      <StatCard icon={Landmark} label="IR estimado" value={formatMoney(data.tax_estimated)} />
    </div>
  )
}