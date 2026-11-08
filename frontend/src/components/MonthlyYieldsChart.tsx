import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import type { MonthlyYield } from '../api/types'
import { formatMoney, formatMonth } from '../lib/format'

type MonthlyYieldsChartProps = {
  months: MonthlyYield[]
}

export function MonthlyYieldsChart({ months }: MonthlyYieldsChartProps) {
  // O gráfico precisa de números: Number() aqui serve SÓ para desenhar as barras.
  const data = months.map((item) => ({
    label: formatMonth(item.month),
    value: Number(item.yield_amount),
  }))

  return (
    // O gráfico ocupa 100% do espaço do "pai", então o pai precisa ter altura (h-64).
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={12} />
          <YAxis
            tickLine={false}
            axisLine={false}
            fontSize={12}
            width={88}
            tickFormatter={(value) => formatMoney(String(value))}
          />
          <Tooltip
            formatter={(value) => [formatMoney(String(value)), 'Rendimento']}
            cursor={{ fill: '#f1f5f9' }}
          />
          <Bar dataKey="value" fill="#10b981" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}