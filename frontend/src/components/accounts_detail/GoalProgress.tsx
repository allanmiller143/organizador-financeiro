import { useState } from 'react'
import { Clock3 } from 'lucide-react'

import { accountsApi } from '../../api/accounts'
import type { GoalForecast } from '../../api/types'
import { formatDate, formatMoney } from '../../lib/format'

function durationLabel(months: number) {
  if (months < 12) return `${months} ${months === 1 ? 'mês' : 'meses'}`
  const years = Math.floor(months / 12)
  const remaining = months % 12
  return `${years} ${years === 1 ? 'ano' : 'anos'}${remaining ? ` e ${remaining} ${remaining === 1 ? 'mês' : 'meses'}` : ''}`
}

// Fallback: se o backend não mandar a data, estima a partir dos meses.
function fallbackDate(months: number) {
  const date = new Date()
  date.setMonth(date.getMonth() + months)
  return date.toLocaleDateString('pt-BR')
}

function forecastLabel(forecast: GoalForecast) {
  if (forecast.status === 'reached') return 'Meta já alcançada.'
  if (forecast.status === 'no_balance') return 'Sem saldo atual, não há prazo estimável sem novos aportes.'
  if (forecast.status === 'no_growth') return 'Não foi possível estimar crescimento com o CDI recente.'
  const months = forecast.months ?? 0
  const date = forecast.projected_date ? formatDate(forecast.projected_date) : fallbackDate(months)
  return `Estimativa: cerca de ${durationLabel(months)} (por volta de ${date}).`
}

export function GoalProgress({
  accountId,
  goalAmount,
  netBalance
}: {
  accountId: string
  goalAmount: string
  netBalance: string
}) {
  const [forecast, setForecast] = useState<GoalForecast | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const goal = Number(goalAmount)
  const balance = Number(netBalance)
  const percent = goal > 0 ? Math.min((balance / goal) * 100, 100) : 0

  async function estimate() {
    setLoading(true)
    setError('')
    try {
      setForecast(await accountsApi.goalForecast(accountId))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Não foi possível estimar o prazo agora.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className=" py-3 text-white">
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <span className="font-semibold">Meta: {formatMoney(goalAmount)}</span>
        <span className="tabular-nums text-white/90">
          {percent.toFixed(0)}% · {formatMoney(netBalance)}
        </span>
      </div>
      <div
        className="mt-2 h-2.5 overflow-hidden rounded-full bg-white/25"
        role="progressbar"
        aria-label={`Progresso da meta: ${percent.toFixed(0)} por cento`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(percent)}
      >
        <div
          className="h-full rounded-full bg-white shadow-sm transition-[width] duration-500"
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <button
          type="button"
          onClick={estimate}
          disabled={loading}
          className="inline-flex cursor-pointer items-center gap-1.5 rounded-xl bg-white/15 px-3 py-1.5 text-xs font-semibold text-white ring-1 ring-white/40 transition hover:bg-white/25 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Clock3 size={14} />
          {loading ? 'Calculando…' : 'Em quanto tempo?'}
        </button>
        {forecast && <span className="text-xs text-white/80">Estimativa após impostos</span>}
      </div>
      {forecast && (
        <p className="mt-2 text-xs leading-relaxed text-white/90" role="status">
          {forecastLabel(forecast)}{' '}
          {forecast.status === 'projected' &&
            'Usa a média recente do CDI, sem novos aportes/retiradas.'}
        </p>
      )}
      {error && (
        <p className="mt-2 rounded-lg bg-white/90 px-2 py-1 text-xs text-red-700" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}