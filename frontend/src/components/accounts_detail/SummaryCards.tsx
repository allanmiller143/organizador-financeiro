import { ArrowDownLeft, Landmark, Lock, TrendingUp, Wallet } from 'lucide-react'

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
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((item) => (
          <div
            key={item}
            className="h-28 animate-pulse rounded-2xl bg-white shadow-sm ring-1 ring-slate-200"
          />
        ))}
      </div>
    )
  }

  const data = summary.data
  if (!data) {
    return <ErrorMessage message="O resumo da caixinha ainda não está disponível. Tente atualizar a página." />
  }
  const taxPaid = Number(data.tax_paid)
  const locked = Number(data.locked_balance)

  return (
    <div className="space-y-3">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Wallet}
          label="Valor aplicado"
          value={formatMoney(data.invested)}
          hint="O que você colocou e ainda está aqui, sem rendimento nem reaplicações"
        />
        <StatCard
          icon={ArrowDownLeft}
          label="Total depositado"
          value={formatMoney(data.deposited_total)}
          hint="Soma de todos os seus aportes"
        />
        <StatCard
          icon={TrendingUp}
          label="Rendimento"
          value={formatMoney(data.gross_yield)}
          hint={`${yieldPercentLabel(data.invested, data.gross_yield)} sobre o valor aplicado${
            taxPaid > 0 ? ` · IR + IOF já pagos: ${formatMoney(data.tax_paid)}` : ''
          }`}
        />
        <StatCard
          icon={Landmark}
          label="IR + IOF estimados"
          value={formatMoney(data.tax_estimated)}
          hint={Number(data.iof_estimated) > 0 ? `Inclui ${formatMoney(data.iof_estimated)} de IOF (resgate em até 30 dias)` : undefined}
        />
      </div>

      {locked > 0 && (
        <p className="flex items-center gap-2 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800 ring-1 ring-amber-200">
          <Lock size={16} className="shrink-0" />
          {formatMoney(data.locked_balance)} estão trancados e só podem ser retirados quando o prazo
          de cada aporte acabar.
        </p>
      )}
    </div>
  )
}
