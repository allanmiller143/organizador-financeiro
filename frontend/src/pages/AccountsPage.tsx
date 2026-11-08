import { useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError } from '../api/client'
import type { Account } from '../api/types'
import { AccountForm } from '../components/AccountForm'
import { Button } from '../components/Button'
import { useAccounts, useDeleteAccount } from '../hooks/useAccounts'
import { useDashboard } from '../hooks/useDashboard'
import { formatCdi, formatDate, formatMoney } from '../lib/format'

type AccountRowProps = {
  account: Account
  balance?: string // o saldo bruto, se já foi calculado
  onDelete: () => void
  disabled: boolean
}

// Uma linha da lista. Fica neste arquivo porque só esta página a usa.
function AccountRow({ account, balance, onDelete, disabled }: AccountRowProps) {
  return (
    <li className="flex items-center justify-between gap-4 p-5">
      <div>
        <Link to={`/caixinhas/${account.id}`} className="font-medium hover:underline">
          {account.name}
        </Link>
        <p className="text-xs text-slate-500">
          {account.institution} · {formatCdi(account.cdi_percent)} · aberta em{' '}
          {formatDate(account.opened_on)}
        </p>
      </div>
      <div className="flex items-center gap-4">
        {account.is_active && (
          <span className="font-medium tabular-nums">{balance ? formatMoney(balance) : '—'}</span>
        )}
        <button
          onClick={onDelete}
          disabled={disabled}
          className="text-sm text-red-600 hover:text-red-800 disabled:opacity-50"
        >
          Apagar
        </button>
      </div>
    </li>
  )
}

export default function AccountsPage() {
  const { data: accounts, isPending, isError, error } = useAccounts()
  const dashboard = useDashboard() // de onde vem o saldo de cada caixinha
  const deleteAccount = useDeleteAccount()
  const [showForm, setShowForm] = useState(false)

  // Um "dicionário": id da caixinha -> saldo bruto.
  const balances = new Map(dashboard.data?.accounts.map((a) => [a.account_id, a.gross_balance]))

  function handleDelete(account: Account) {
    const confirmed = window.confirm(
      `Apagar a caixinha "${account.name}"? Todas as transações dela também serão apagadas.`,
    )
    if (confirmed) deleteAccount.mutate(account.id)
  }

  const active = accounts?.filter((a) => a.is_active) ?? []
  const archived = accounts?.filter((a) => !a.is_active) ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Caixinhas</h1>
        {!showForm && <Button onClick={() => setShowForm(true)}>Nova caixinha</Button>}
      </div>

      {showForm && (
        <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <h2 className="mb-4 text-lg font-semibold">Nova caixinha</h2>
          <AccountForm onDone={() => setShowForm(false)} onCancel={() => setShowForm(false)} />
        </section>
      )}

      {deleteAccount.isError && (
        <p className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
          Não foi possível apagar a caixinha. Tente de novo.
        </p>
      )}

      {/* ESTADO 1: carregando */}
      {isPending && <p className="text-slate-500">Carregando suas caixinhas...</p>}

      {/* ESTADO 2: erro */}
      {isError && (
        <p className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
          {error instanceof ApiError ? error.message : 'Não foi possível conectar ao servidor.'}
        </p>
      )}

      {/* ESTADO 3: vazio */}
      {accounts && accounts.length === 0 && !showForm && (
        <p className="rounded-2xl bg-white p-6 text-sm text-slate-500 shadow-sm ring-1 ring-slate-200">
          Você ainda não tem caixinhas. Clique em "Nova caixinha" para cadastrar a primeira.
        </p>
      )}

      {/* ESTADO 4: com dados */}
      {active.length > 0 && (
        <ul className="divide-y divide-slate-100 rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
          {active.map((account) => (
            <AccountRow
              key={account.id}
              account={account}
              balance={balances.get(account.id)}
              onDelete={() => handleDelete(account)}
              disabled={deleteAccount.isPending}
            />
          ))}
        </ul>
      )}

      {archived.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-500">Arquivadas</h2>
          <ul className="divide-y divide-slate-100 rounded-2xl bg-white opacity-75 shadow-sm ring-1 ring-slate-200">
            {archived.map((account) => (
              <AccountRow
                key={account.id}
                account={account}
                onDelete={() => handleDelete(account)}
                disabled={deleteAccount.isPending}
              />
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}