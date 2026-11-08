import { BarChart3 } from 'lucide-react'

import { describeError } from '../../lib/errors'
import { InsightCard } from '../dashboard/InsightCard'
import { ErrorMessage } from '../ErrorMessage'
import { LoadingState } from '../LoadingState'
import { MonthlyYieldsChart } from './MonthlyYieldsChart'
import type { MonthlyQuery } from './types'

export function YieldChartCard({ monthly }: { monthly: MonthlyQuery }) {
  // Só desenhamos o gráfico se algum mês rendeu algo.
  const hasYield = monthly.data?.months.some((month) => Number(month.yield_amount) > 0) ?? false

  return (
    <InsightCard
      icon={BarChart3}
      title="Rendimento por mês"
      subtitle="Quanto a caixinha rendeu em cada mês"
    >
      <div className="mt-5">
        {monthly.isPending && <LoadingState message="Calculando..." />}

        {monthly.isError && <ErrorMessage message={describeError(monthly.error)} />}

        {monthly.data && !hasYield && (
          <div className="flex flex-col items-center gap-3 py-8 text-center">
            <span className="grid h-12 w-12 place-items-center rounded-full bg-teal-50 text-teal-600">
              <BarChart3 size={24} />
            </span>
            <p className="max-w-sm text-sm text-slate-500">
              Ainda sem rendimento. Registre um aporte com uma data anterior ao último CDI para ver
              as barras.
            </p>
          </div>
        )}

        {monthly.data && hasYield && <MonthlyYieldsChart months={monthly.data.months} />}
      </div>
    </InsightCard>
  )
}