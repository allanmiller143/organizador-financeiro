import { ProjectionChart } from '../components/ProjectionChart'
import { SimulationForm } from '../components/SimulationForm'
import { StatCard } from '../components/StatCard'
import { useDashboard } from '../hooks/useDashboard'
import { useSimulation } from '../hooks/useSimulation'
import { noErrors, toFormErrors } from '../lib/errors'
import { formatDuration, formatMoney } from '../lib/format'

export default function ProjectionPage() {
  const dashboard = useDashboard() // só para o atalho "usar meu saldo atual"
  const simulation = useSimulation()

  // Estado derivado: os erros do formulário saem direto do erro da simulação.
  const errors = simulation.error ? toFormErrors(simulation.error) : noErrors
  const result = simulation.data

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Projeção</h1>
        <p className="mt-1 text-sm text-slate-500">
          Simule como o seu dinheiro pode crescer, com aportes e retiradas mensais.
        </p>
      </div>

      <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <SimulationForm
          onSubmit={(input) => simulation.mutate(input)}
          loading={simulation.isPending}
          errors={errors}
          currentBalance={dashboard.data?.totals.gross_balance}
        />
      </section>

      {result && (
        <>
          {/* Aviso: o dinheiro acabou antes do fim da simulação */}
          {result.depleted_month && (
            <p className="rounded-lg bg-amber-50 p-4 text-sm text-amber-800">
              Atenção: com essas retiradas, o dinheiro acaba no mês {result.depleted_month} (
              {formatDuration(result.depleted_month)} a partir de hoje).
            </p>
          )}

          <section className="space-y-4">
            <h2 className="text-lg font-semibold">Em {formatDuration(result.months.length)}</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Saldo bruto" value={formatMoney(result.summary.gross_balance)} />
              <StatCard
                label="Saldo líquido"
                value={formatMoney(result.summary.net_balance)}
                hint={`IR estimado: ${formatMoney(result.summary.tax_estimated)}`}
              />
              <StatCard label="Total aportado" value={formatMoney(result.summary.invested)} />
              <StatCard label="Rendimento bruto" value={formatMoney(result.summary.gross_yield)} />
              {Number(result.summary.withdrawn) > 0 && (
                <StatCard
                  label="Total retirado"
                  value={formatMoney(result.summary.withdrawn)}
                  hint={`IR pago nas retiradas: ${formatMoney(result.summary.tax_paid)}`}
                />
              )}
            </div>
          </section>

          <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <h2 className="mb-4 text-lg font-semibold">Evolução do patrimônio</h2>
            <ProjectionChart months={result.months} />
          </section>

          <p className="text-xs text-slate-500">
            Isto é uma estimativa. O CDI futuro é uma premissa sua, a conta é feita mês a mês, o
            valor inicial é tratado como dinheiro novo (o imposto incide só sobre o rendimento
            projetado) e o IOF não é considerado.
          </p>
        </>
      )}
    </div>
  )
}