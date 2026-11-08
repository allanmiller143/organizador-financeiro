import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import type { SimulationPoint } from '../api/types'
import { formatMoney, formatMoneyCompact, formatMonth } from '../lib/format'

type ProjectionChartProps = {
  months: SimulationPoint[]
}

export function ProjectionChart({ months }: ProjectionChartProps) {
  // O gráfico precisa de números: Number() aqui serve SÓ para desenhar as linhas.
  const data = months.map((point) => ({
    label: formatMonth(point.month),
    bruto: Number(point.gross_balance),
    liquido: Number(point.net_balance),
    aportado: Number(point.invested),
  }))

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          {/* minTickGap evita que os rótulos dos meses se amontoem em projeções longas */}
          <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={12} minTickGap={32} />
          <YAxis
            tickLine={false}
            axisLine={false}
            fontSize={12}
            width={84}
            tickFormatter={(value) => formatMoneyCompact(Number(value))}
          />
          <Tooltip formatter={(value, name) => [formatMoney(String(value)), String(name)]} />
          <Legend />
          <Line type="monotone" dataKey="bruto" name="Saldo bruto" stroke="#10b981" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="liquido" name="Saldo líquido" stroke="#0f172a" strokeWidth={2} dot={false} />
          <Line
            type="monotone"
            dataKey="aportado"
            name="Total aportado"
            stroke="#94a3b8"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}