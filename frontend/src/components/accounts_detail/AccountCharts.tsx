import { BarChart3, TrendingUp } from 'lucide-react'

import { describeError } from '../../lib/errors'
import { formatMonth } from '../../lib/format'
import type { MonthlyQuery, MonthPoint } from './types'
import { BarsCard, type BarPoint } from '../BarsCard'

// O backend manda valores como texto. Number() aqui serve SÓ para desenhar as barras.
function toNumber(value?: string | null): number | null {
  return value == null ? null : Number(value)
}

export function AccountCharts({ monthly }: { monthly: MonthlyQuery }) {
  const months: MonthPoint[] = monthly.data?.months ?? []

  const yieldPoints: BarPoint[] = months.map((month) => ({
    label: formatMonth(month.month),
    gross: toNumber(month.yield_amount),
    net: toNumber(month.net_yield_amount),
  }))

  const balancePoints: BarPoint[] = months.map((month) => ({
    label: formatMonth(month.month),
    gross: toNumber(month.gross_balance),
    net: toNumber(month.net_balance),
    reference: toNumber(month.invested),
  }))

  const loading = monthly.isPending
  const error = monthly.isError ? describeError(monthly.error) : undefined

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <BarsCard
        icon={TrendingUp}
        title="Rendimento por mês"
        subtitle="Quanto a caixinha rendeu em cada mês"
        points={yieldPoints}
        loading={loading}
        error={error}
        emptyMessage="Ainda sem rendimento. Registre um aporte com uma data anterior ao último CDI para ver as barras."
        gradientId="yieldBars"
        colors={['#38bdf8', '#14b8a6']}
        tooltipLabel="Rendimento"
      />
      <BarsCard
        icon={BarChart3}
        title="Valor total"
        subtitle="Quanto a caixinha valia no fim de cada mês, com o valor aplicado em linha"
        points={balancePoints}
        loading={loading}
        error={error}
        emptyMessage="A evolução do saldo aparecerá aqui quando houver movimentações."
        gradientId="balanceBars"
        colors={['#818cf8', '#38bdf8']}
        tooltipLabel="Saldo"
        referenceLabel="Valor aplicado"
      />
    </div>
  )
}