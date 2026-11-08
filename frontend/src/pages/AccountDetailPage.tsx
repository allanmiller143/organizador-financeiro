import { Link, useParams } from 'react-router-dom'

import { StatCard } from '../components/StatCard'
import { TransactionForm } from '../components/TransactionForm'
import { TransactionList } from '../components/TransactionList'
import { useAccount, useAccountSummary } from '../hooks/useAccounts'
import { useDeleteTransaction, useTransactions } from '../hooks/useTransactions'
import { describeError } from '../lib/errors'
import { formatCdi, formatDate, formatMoney } from '../lib/format'

export default function AccountDetailPage() {
  // Lê a parte variável do endereço: /caixinhas/:accountId
  const { accountId = '' } = useParams()

  const account = useAccount(accountId)
  const summary = useAccountSummary(accountId)
  const transactions = useTransactions(accountId)
  const deleteTransaction = useDeleteTransaction(accountId)

  // Carregando ou não encontrada: a página nem chega a mostrar o resto.
  if (account.isPending) {
    return <p className="text-slate-500">Carregando...</p>
  }
  if (account.isError) {
    return (
      <div className="space-y-3">
        <p className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
          {describeError(account.error)}
        </p>
        <Link to="/caixinhas" className="text-sm font-medium text-emerald-700 hover:underline">
          ← Voltar às caixinhas
        </Link>
      </div>
    )
  }

  const data = account.data

  return (
    <div className="space-y-8">
      <div>
        <Link to="/caixinhas" className="text-sm text-slate-500 hover:text-slate-900">
          ← Caixinhas
        </Link>
        <h1 className="mt-2 text-2xl font-semibold">{data.name}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {data.institution} · {formatCdi(data.cdi_percent)} · aberta em {formatDate(data.opened_on)}
        </p>
      </div>

      {/* RESUMO: o resultado do motor de cálculo do backend */}
      <section className="space-y-3">
        {summary.isPending && <p className="text-slate-500">Calculando o resumo...</p>}
        {summary.isError && (
          <p className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
            {describeError(summary.error)}
          </p>
        )}
        {summary.data && (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Saldo bruto" value={formatMoney(summary.data.gross_balance)} />
              <StatCard
                label="Saldo líquido"
                value={formatMoney(summary.data.net_balance)}
                hint={`IR estimado: ${formatMoney(summary.data.tax_estimated)}`}
              />
              <StatCard label="Total aportado" value={formatMoney(summary.data.invested)} />
              <StatCard label="Rendimento bruto" value={formatMoney(summary.data.gross_yield)} />
            </div>
            <p className="text-xs text-slate-500">
              Valores calculados até {formatDate(summary.data.as_of)}.
            </p>
          </>
        )}
      </section>

      {/* NOVO LANÇAMENTO */}
      <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="mb-4 text-lg font-semibold">Novo lançamento</h2>
        <TransactionForm accountId={accountId} openedOn={data.opened_on} />
      </section>

      {/* HISTÓRICO */}
      <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold">Histórico</h2>

        {deleteTransaction.isError && (
          <p className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            {describeError(deleteTransaction.error)}
          </p>
        )}

        {transactions.isPending && <p className="mt-4 text-slate-500">Carregando...</p>}
        {transactions.isError && (
          <p className="mt-4 text-sm text-red-700">{describeError(transactions.error)}</p>
        )}
        {transactions.data && transactions.data.length === 0 && (
          <p className="mt-4 text-sm text-slate-500">
            Nenhum lançamento ainda. Registre o primeiro aporte acima.
          </p>
        )}
        {transactions.data && transactions.data.length > 0 && (
          <div className="mt-2">
            <TransactionList
              transactions={transactions.data}
              disabled={deleteTransaction.isPending}
              onDelete={(transaction) => {
                if (window.confirm('Apagar este lançamento?')) {
                  deleteTransaction.mutate(transaction.id)
                }
              }}
            />
          </div>
        )}
      </section>
    </div>
  )
}