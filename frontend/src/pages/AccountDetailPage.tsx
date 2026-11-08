import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

import { AccountHeader } from '../components/accounts_detail/AccountHeader'
import { ErrorMessage } from '../components/ErrorMessage'
import { LoadingState } from '../components/LoadingState'
import { useAccount, useAccountSummary, useMonthlyYields } from '../hooks/useAccounts'
import {
  useDeleteTransaction,
  useTransactions,
  useUpdateTransaction,
} from '../hooks/useTransactions'
import { describeError } from '../lib/errors'
import { SummaryCards } from '../components/accounts_detail/SummaryCards'
import { HistoryCard } from '../components/accounts_detail/HistoryCard'
import { NewTransactionDialog } from '../components/accounts_detail/NewTransactionDialog'
import { AccountCharts } from '../components/accounts_detail/AccountCharts'

export default function AccountDetailPage() {
  // Lê a parte variável do endereço: /caixinhas/:accountId
  const { accountId = '' } = useParams()

  const account = useAccount(accountId)
  const summary = useAccountSummary(accountId)
  const monthly = useMonthlyYields(accountId)
  const transactions = useTransactions(accountId)
  const deleteTransaction = useDeleteTransaction(accountId)
  const updateTransaction = useUpdateTransaction(accountId)
  const [showTransactionForm, setShowTransactionForm] = useState(false)

  // Carregando ou não encontrada: a página nem chega a mostrar o resto.
  if (account.isPending) {
    return <LoadingState message="Carregando..." />
  }
  if (account.isError) {
    return (
      <div className="space-y-4">
        <ErrorMessage message={describeError(account.error)} />
        <Link
          to="/caixinhas"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-teal-700 transition hover:text-teal-800"
        >
          <ArrowLeft size={16} />
          Voltar às caixinhas
        </Link>
      </div>
    )
  }

  const data = account.data

  return (
    <div className="space-y-6">
      <AccountHeader
        account={data}
        summary={summary}
        onNewTransaction={() => setShowTransactionForm(true)}
      />

      <SummaryCards summary={summary} />

      <AccountCharts monthly={monthly} />

      <HistoryCard
        transactions={transactions}
        monthly={monthly}
        deleteTransaction={deleteTransaction}
        updateTransaction={updateTransaction}
        openedOn={data.opened_on}
        onNew={() => setShowTransactionForm(true)}
      />

      <NewTransactionDialog
        open={showTransactionForm}
        onClose={() => setShowTransactionForm(false)}
        accountId={accountId}
        openedOn={data.opened_on}
        transactionCount={transactions.data?.length}
      />
    </div>
  )
}