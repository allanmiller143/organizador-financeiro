import {
  ArrowDownLeft,
  BadgeInfo,
  CalendarRange,
  Coins,
  PiggyBank,
  TrendingUp,
  Wallet,
} from 'lucide-react'

import { ProjectionChart } from '../components/ProjectionChart'
import { SimulationForm } from '../components/SimulationForm'
import { StatCard } from '../components/StatCard'
import { useDashboard } from '../hooks/useDashboard'
import { useSimulation } from '../hooks/useSimulation'
import { noErrors, toFormErrors } from '../lib/errors'
import { formatDuration, formatMoney } from '../lib/format'

export default function ProjectionPage() {
  const dashboard = useDashboard()
  const simulation = useSimulation()
  const errors = simulation.error ? toFormErrors(simulation.error) : noErrors
  const result = simulation.data

  return (
    <div className="space-y-6">
      <header className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-sky-500 to-teal-600 p-6 text-white shadow-lg sm:p-8">
        <div className="pointer-events-none absolute -right-12 -top-20 h-64 w-64 rounded-full bg-white/10" />
        <div className="pointer-events-none absolute -bottom-28 right-28 h-56 w-56 rounded-full bg-white/10" />
        <div className="relative flex items-start justify-between gap-4">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-white/90 ring-1 ring-white/20">
              <TrendingUp size={14} /> Planejamento financeiro
            </span>
            <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">Projeção</h1>
            <p className="mt-2 max-w-xl text-sm leading-6 text-white/80 sm:text-base">
              Explore como aportes e retiradas podem mudar o seu patrimônio ao longo do tempo.
              Ajuste as premissas e compare cenários com clareza.
            </p>
          </div>
          <span className="hidden h-14 w-14 shrink-0 place-items-center rounded-2xl bg-white/15 text-white ring-1 ring-white/25 sm:grid">
            <CalendarRange size={25} />
          </span>
        </div>
      </header>

      <section className="overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-slate-200">
        <div className="border-b border-slate-100 px-5 py-4 sm:px-6">
          <h2 className="text-lg font-semibold text-slate-900">Monte seu cenário</h2>
          <p className="mt-1 text-sm text-slate-500">
            Informe valores mensais e uma hipótese para o CDI futuro.
          </p>
        </div>
        <div className="p-5 sm:p-6">
          <SimulationForm
            onSubmit={(input) => simulation.mutate(input)}
            loading={simulation.isPending}
            errors={errors}
            currentBalance={dashboard.data?.totals.gross_balance}
          />
        </div>
      </section>

      {result && (
        <>
          {result.depleted_month && (
            <div role="status" className="flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-900">
              <BadgeInfo size={19} className="mt-0.5 shrink-0 text-amber-700" />
              <p className="text-sm leading-6">
                Com essas retiradas, o saldo se esgota no mês {result.depleted_month} (
                {formatDuration(result.depleted_month)} a partir do início do cenário).
              </p>
            </div>
          )}

          <section className="space-y-4">
            <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-sm font-medium text-teal-700">Resultado estimado</p>
                <h2 className="mt-1 text-xl font-semibold text-slate-900">
                  Em {formatDuration(result.months.length)}
                </h2>
              </div>
              <span className="inline-flex w-fit items-center gap-2 rounded-full bg-teal-50 px-3 py-1.5 text-xs font-medium text-teal-800">
                <CalendarRange size={14} /> {result.months.length} meses simulados
              </span>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Saldo bruto" value={formatMoney(result.summary.gross_balance)} icon={Wallet} />
              <StatCard
                label="Saldo líquido"
                value={formatMoney(result.summary.net_balance)}
                hint={`IR estimado: ${formatMoney(result.summary.tax_estimated)}`}
                icon={Coins}
              />
              <StatCard label="Total aportado" value={formatMoney(result.summary.invested)} icon={PiggyBank} />
              <StatCard label="Rendimento bruto" value={formatMoney(result.summary.gross_yield)} icon={TrendingUp} />
              {Number(result.summary.withdrawn) > 0 && (
                <StatCard
                  label="Total retirado"
                  value={formatMoney(result.summary.withdrawn)}
                  hint={`IR pago nas retiradas: ${formatMoney(result.summary.tax_paid)}`}
                  icon={ArrowDownLeft}
                />
              )}
            </div>
          </section>

          <section className="overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-slate-200">
            <div className="border-b border-slate-100 px-5 py-4 sm:px-6">
              <h2 className="text-lg font-semibold text-slate-900">Evolução do patrimônio</h2>
              <p className="mt-1 text-sm text-slate-500">
                Compare o saldo bruto, o saldo líquido e o total aportado ao longo do cenário.
              </p>
            </div>
            <div className="p-3 sm:p-6">
              <ProjectionChart months={result.months} />
            </div>
          </section>

          <div className="flex gap-3 rounded-2xl bg-slate-100/80 p-4 text-slate-600">
            <BadgeInfo size={18} className="mt-0.5 shrink-0 text-slate-500" />
            <p className="text-xs leading-5">
              Esta é uma estimativa: o CDI futuro é uma premissa, a conta é feita mês a mês,
              o valor inicial é tratado como dinheiro novo (imposto somente sobre o rendimento
              projetado) e o IOF não é considerado.
            </p>
          </div>
        </>
      )}
    </div>
  )
}
