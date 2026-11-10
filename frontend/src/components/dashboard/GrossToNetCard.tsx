import { Landmark } from 'lucide-react'

import { formatMoney } from '../../lib/format'
import { InsightCard } from './InsightCard'
import { SplitBar } from './SplitBar'
import { money, summarize } from './helpers'
import type { Totals } from './types'

export function GrossToNetCard({ totals }: { totals: Totals }) {
  const { netYield, netShare, taxShare } = summarize(totals)

  return (
    <InsightCard
      icon={Landmark}
      title="Do bruto ao líquido"
      subtitle="Quanto o imposto leva do seu saldo"
    >
      <SplitBar
        className="mt-5"
        segments={[
          {
            percent: netShare,
            className: 'bg-teal-500',
            title: `Líquido: ${netShare.toFixed(1)}%`,
          },
          {
            percent: taxShare,
            className: 'bg-rose-300',
            title: `IR: ${taxShare.toFixed(1)}%`,
          },
        ]}
      />

      <dl className="mt-5 space-y-3 text-sm">
        <div className="flex items-center justify-between gap-4">
          <dt className="text-slate-600">Saldo bruto</dt>
          <dd className="font-medium tabular-nums text-slate-900">
            {formatMoney(totals.gross_balance)}
          </dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="flex items-center gap-2 text-slate-600">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-300" />
            IR + IOF estimados
          </dt>
          <dd className="font-medium tabular-nums text-rose-600">
            − {formatMoney(totals.tax_estimated)}
          </dd>
        </div>
        <div className="flex items-center justify-between gap-4 border-t border-slate-100 pt-3">
          <dt className="flex items-center gap-2 font-medium text-slate-900">
            <span className="h-2.5 w-2.5 rounded-full bg-teal-500" />
            Saldo líquido
          </dt>
          <dd className="font-semibold tabular-nums text-slate-900">
            {formatMoney(totals.net_balance)}
          </dd>
        </div>
      </dl>

      <p className="mt-4 rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-600">
        Descontado o IR, o seu ganho real é de{' '}
        <span className="font-semibold text-slate-900">{money(netYield)}</span>.
      </p>
    </InsightCard>
  )
}