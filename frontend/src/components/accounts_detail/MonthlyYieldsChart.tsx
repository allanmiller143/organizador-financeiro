import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import type { MonthlyYield } from '../../api/types'
import { formatMoney, formatMonth } from '../../lib/format'

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
          <defs>
            <linearGradient id="yieldBar" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#38bdf8" />
              <stop offset="100%" stopColor="#14b8a6" />
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
            width={88}
            tick={{ fill: '#64748b' }}
            tickFormatter={(value) => formatMoney(String(value))}
          />
          <Tooltip
            formatter={(value) => [formatMoney(String(value)), 'Rendimento']}
            cursor={{ fill: '#f0fdfa' }}
            contentStyle={{
              borderRadius: 12,
              border: 'none',
              boxShadow: '0 10px 25px rgba(15, 23, 42, 0.15)',
              fontSize: 13,
            }}
          />
          <Bar dataKey="value" fill="url(#yieldBar)" radius={[6, 6, 0, 0]} maxBarSize={40} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}