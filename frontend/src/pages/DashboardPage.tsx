import { ApiError } from '../api/client'
import { StatCard } from '../components/StatCard'
import { useDashboard } from '../hooks/useDashboard'
import { formatDate, formatMoney, formatPercent } from '../lib/format'

// Transforma o erro técnico numa frase que ajuda a pessoa.
function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === 'cdi_not_synced' || error.code === 'cdi_incomplete') {
      return 'Os dados do CDI ainda não estão completos. Rode "flask --app wsgi sync-cdi" no backend e recarregue a página.'
    }
    return error.message
  }
  return 'Não foi possível conectar ao servidor.'
}

export default function DashboardPage() {
  const { data, isPending, isError, error } = useDashboard()

  // ESTADO 1: carregando
  if (isPending) {
    return <p className="text-slate-500">Carregando seus números...</p>
  }

  // ESTADO 2: deu erro
  if (isError) {
    return <p className="rounded-lg bg-red-50 p-4 text-sm text-red-700">{errorMessage(error)}</p>
  }

  const { totals, accounts, as_of } = data

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Visão geral</h1>
        {as_of && (
          <p className="mt-1 text-sm text-slate-500">
            Valores calculados até {formatDate(as_of)}.
          </p>
        )}
      </div>

      {/* Os quatro cartões de número */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Saldo bruto" value={formatMoney(totals.gross_balance)} />
        <StatCard
          label="Saldo líquido"
          value={formatMoney(totals.net_balance)}
          hint={`IR estimado: ${formatMoney(totals.tax_estimated)}`}
        />
        <StatCard label="Total aportado" value={formatMoney(totals.invested)} />
        <StatCard label="Rendimento bruto" value={formatMoney(totals.gross_yield)} />
      </div>

      {/* A lista de caixinhas */}
      <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold">Suas caixinhas</h2>

        {/* ESTADO 3: vazio */}
        {accounts.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">
            Você ainda não tem caixinhas. Na próxima etapa vamos criar a tela para cadastrá-las.
          </p>
        ) : (
          /* ESTADO 4: com dados */
          <ul className="mt-4 divide-y divide-slate-100">
            {accounts.map((account) => (
              <li key={account.account_id} className="py-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-medium">{account.name}</p>
                    <p className="text-xs text-slate-500">{account.institution}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium tabular-nums">{formatMoney(account.gross_balance)}</p>
                    <p className="text-xs text-slate-500">
                      {formatPercent(account.share_percent)} do total
                    </p>
                  </div>
                </div>

                {/* A barrinha: o fundo cinza é 100%, a verde é a participação da caixinha */}
                <div className="mt-3 h-2 rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-emerald-500"
                    style={{ width: `${Number(account.share_percent)}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}