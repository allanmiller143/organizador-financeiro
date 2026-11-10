import { useState } from 'react'

import { ApiError } from '../api/client'
import type { Account } from '../api/types'
import { AccountsHeader } from '../components/accounts/AccountsHeader'
import { AccountsSection } from '../components/accounts/AccountsSection'
import { EmptyAccounts } from '../components/accounts/EmptyAccounts'
import { NewAccountDialog } from '../components/accounts/NewAccountDialog'
import { ErrorMessage } from '../components/ErrorMessage'
import { LoadingState } from '../components/LoadingState'
import { useAccounts, useDeleteAccount } from '../hooks/useAccounts'
import { useDashboard } from '../hooks/useDashboard'
import { AccountRow } from '../components/accounts/AccountRow'
import { ConfirmDialog } from '../components/ConfirmDialog'

export default function AccountsPage() {
  const { data: accounts, isPending, isError, error } = useAccounts()
  const dashboard = useDashboard() // de onde vem o saldo de cada caixinha
  const deleteAccount = useDeleteAccount()
  const [showForm, setShowForm] = useState(false)
  const [accountToDelete, setAccountToDelete] = useState<Account | null>(null)

  // Um "dicionário": id da caixinha -> saldo bruto.
  const balances = new Map(dashboard.data?.accounts.map((a) => [a.account_id, a.gross_balance]))

  function handleDelete(account: Account) {
    setAccountToDelete(account)
  }

  const active = accounts?.filter((a) => a.is_active) ?? []
  const archived = accounts?.filter((a) => !a.is_active) ?? []

  return (
    <div className="space-y-6">
      {accounts && (
        <AccountsHeader
          activeCount={active.length}
          archivedCount={archived.length}
          onNew={() => setShowForm(true)}
        />
      )}

      {deleteAccount.isError && (
        <ErrorMessage message="Não foi possível apagar a caixinha. Tente de novo." />
      )}

      {/* ESTADO 1: carregando */}
      {isPending && <LoadingState message="Carregando suas caixinhas..." />}

      {/* ESTADO 2: erro */}
      {isError && (
        <ErrorMessage
          message={
            error instanceof ApiError ? error.message : 'Não foi possível conectar ao servidor.'
          }
        />
      )}

      {/* ESTADO 3: vazio */}
      {accounts && accounts.length === 0 && <EmptyAccounts onCreate={() => setShowForm(true)} />}

      {/* ESTADO 4: com dados */}
      {active.length > 0 && (
        <AccountsSection>
          {active.map((account) => (
            <AccountRow
              key={account.id}
              account={account}
              balance={balances.get(account.id)}
              onDelete={() => handleDelete(account)}
              disabled={deleteAccount.isPending}
            />
          ))}
        </AccountsSection>
      )}

      {archived.length > 0 && (
        <AccountsSection title="Arquivadas" muted>
          {archived.map((account) => (
            <AccountRow
              key={account.id}
              account={account}
              onDelete={() => handleDelete(account)}
              disabled={deleteAccount.isPending}
            />
          ))}
        </AccountsSection>
      )}

      <NewAccountDialog open={showForm} onClose={() => setShowForm(false)} />
      <ConfirmDialog
        open={accountToDelete !== null}
        title="Excluir caixinha?"
        message={accountToDelete ? `A caixinha “${accountToDelete.name}” e todas as transações dela serão apagadas permanentemente.` : ''}
        loading={deleteAccount.isPending}
        onClose={() => setAccountToDelete(null)}
        onConfirm={() => {
          if (!accountToDelete) return
          deleteAccount.mutate(accountToDelete.id, { onSettled: () => setAccountToDelete(null) })
        }}
      />
    </div>
  )
}
