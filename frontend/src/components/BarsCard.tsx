import { useState } from 'react'
import type { LucideIcon } from 'lucide-react'
import { BarChart3 } from 'lucide-react'

import { BarsChart } from './BarsChart'
import { InsightCard } from './dashboard/InsightCard'
import { ErrorMessage } from './ErrorMessage'
import { LoadingState } from './LoadingState'
import { BasisSwitch, type Basis } from './accounts_detail/BasisSwitch'

// Um ponto do gráfico. null = o backend não mandou esse valor.
export type BarPoint = {
  label: string
  gross: number | null
  net: number | null
  reference?: number | null // linha de comparação (ex.: valor aplicado)
}

type BarsCardProps = {
  icon: LucideIcon
  title: string
  subtitle: string
  points: BarPoint[]
  loading: boolean
  error?: string
  emptyMessage: string
  gradientId: string
  colors: [string, string]
  tooltipLabel: string
  referenceLabel?: string
}

export function BarsCard({
  icon,
  title,
  subtitle,
  points,
  loading,
  error,
  emptyMessage,
  gradientId,
  colors,
  tooltipLabel,
  referenceLabel,
}: BarsCardProps) {
  const [basis, setBasis] = useState<Basis>('gross')

  // O alternador só faz sentido se existir valor líquido.
  const hasNet = points.some((point) => point.net !== null)
  const activeBasis: Basis = basis === 'net' && hasNet ? 'net' : 'gross'

  const data = points.map((point) => ({
    label: point.label,
    value: point[activeBasis] ?? 0,
    reference: point.reference ?? null,
  }))
  const hasData = data.some((item) => item.value > 0)

  const label =
    activeBasis === 'net' ? `${tooltipLabel} líquido` : hasNet ? `${tooltipLabel} bruto` : tooltipLabel

  return (
    <InsightCard
      icon={icon}
      title={title}
      subtitle={subtitle}
      action={hasNet ? <BasisSwitch value={activeBasis} onChange={setBasis} /> : undefined}
    >
      <div className="mt-5">
        {loading && <LoadingState message="Calculando..." />}

        {error && <ErrorMessage message={error} />}

        {!loading && !error && !hasData && (
          <div className="flex flex-col items-center gap-3 py-8 text-center">
            <span className="grid h-12 w-12 place-items-center rounded-full bg-teal-50 text-teal-600">
              <BarChart3 size={24} />
            </span>
            <p className="max-w-xs text-sm text-slate-500">{emptyMessage}</p>
          </div>
        )}

        {!loading && !error && hasData && (
          <BarsChart
            data={data}
            gradientId={gradientId}
            colors={colors}
            tooltipLabel={label}
            referenceLabel={referenceLabel}
          />
        )}
      </div>
    </InsightCard>
  )
}