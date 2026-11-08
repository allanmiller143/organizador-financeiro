import { Wallet } from 'lucide-react'

import { formatMoney } from '../../lib/format'
import { InsightCard } from './InsightCard'
import { SplitBar } from './SplitBar'
import { summarize } from './helpers'
import type { Totals } from './types'

export function InvestedYieldCard({ totals }: { totals: Totals }) {
  const { yieldLabel, investedShare, yieldShare } = summarize(totals)

  return (
    <InsightCard
      icon={Wallet}
      title="Investido e ganho"
      subtitle="O que saiu do seu bolso e o que já rendeu"
    >
      <SplitBar
        className="mt-5"
        segments={[
          {
            percent: investedShare,
            className: 'bg-sky-400',
            title: `Aportado: ${investedShare.toFixed(1)}%`,
          },
          {
            percent: yieldShare,
            className: 'bg-teal-500',
            title: `Rendimento: ${yieldShare.toFixed(1)}%`,
          },
        ]}
      />

      <dl className="mt-5 space-y-3 text-sm">
        <div className="flex items-center justify-between gap-4">
          <dt className="flex items-center gap-2 text-slate-600">
            <span className="h-2.5 w-2.5 rounded-full bg-sky-400" />
            Você aportou
          </dt>
          <dd className="font-medium tabular-nums text-slate-900">{formatMoney(totals.invested)}</dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="flex items-center gap-2 text-slate-600">
            <span className="h-2.5 w-2.5 rounded-full bg-teal-500" />
            Rendimento bruto
          </dt>
          <dd className="font-medium tabular-nums text-teal-700">
            + {formatMoney(totals.gross_yield)}
            <span className="ml-2 text-xs font-normal text-slate-500">{yieldLabel}</span>
          </dd>
        </div>
      </dl>
    </InsightCard>
  )
}