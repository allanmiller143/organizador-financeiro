import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { formatMoney } from '../lib/format'

type BarsChartProps = {
  data: { label: string; value: number; reference?: number | null }[]
  gradientId: string // único por gráfico
  colors: [string, string] // do topo da barra até a base
  tooltipLabel: string
  referenceLabel?: string // se existir, desenha uma linha com os valores de "reference"
}

// Só para o eixo (ex.: "R$ 1,2 mil"). Os valores exatos aparecem no tooltip.
const compactMoney = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  notation: 'compact',
  maximumFractionDigits: 1,
})

export function BarsChart({
  data,
  gradientId,
  colors,
  tooltipLabel,
  referenceLabel,
}: BarsChartProps) {
  const showReference = Boolean(referenceLabel) && data.some((item) => item.reference != null)

  return (
    // O gráfico ocupa 100% do espaço do "pai", então o pai precisa ter altura (h-56).
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={colors[0]} />
              <stop offset="100%" stopColor={colors[1]} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            fontSize={12}
            tick={{ fill: '#64748b' }}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            fontSize={12}
            width={72}
            tick={{ fill: '#64748b' }}
            tickFormatter={(value) => compactMoney.format(Number(value))}
          />
          <Tooltip
            formatter={(value, name) => [formatMoney(String(value)), String(name)]}
            cursor={{ fill: '#f0fdfa' }}
            contentStyle={{
              borderRadius: 12,
              border: 'none',
              boxShadow: '0 10px 25px rgba(15, 23, 42, 0.15)',
              fontSize: 13,
            }}
          />
          {showReference && <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />}
          <Bar
            dataKey="value"
            name={tooltipLabel}
            fill={`url(#${gradientId})`}
            radius={[6, 6, 0, 0]}
            maxBarSize={40}
          />
          {showReference && (
            <Line
              dataKey="reference"
              name={referenceLabel}
              type="monotone"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
              connectNulls
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}