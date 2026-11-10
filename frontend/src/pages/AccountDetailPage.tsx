import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Layers3 } from 'lucide-react'

import { AccountHeader } from '../components/accounts_detail/AccountHeader'
import { ErrorMessage } from '../components/ErrorMessage'
import { LoadingState } from '../components/LoadingState'
import { useAccount, useAccountSummary, useDepositDetails, useMonthlyYields } from '../hooks/useAccounts'
import {
  useDeleteTransaction,
  useTransactions,
  useUpdateTransaction,
  useReorderTransactions,
  useReorderReapplications,
} from '../hooks/useTransactions'
import { describeError } from '../lib/errors'
import { SummaryCards } from '../components/accounts_detail/SummaryCards'
import { HistoryCard } from '../components/accounts_detail/HistoryCard'
import { NewTransactionDialog } from '../components/accounts_detail/NewTransactionDialog'
import { AccountCharts } from '../components/accounts_detail/AccountCharts'
import { DepositDetailsDialog } from '../components/accounts_detail/DepositDetailsDialog'

export default function AccountDetailPage() {
  // Lê a parte variável do endereço: /caixinhas/:accountId
  const { accountId = '' } = useParams()

  const account = useAccount(accountId)
  const summary = useAccountSummary(accountId)
  const monthly = useMonthlyYields(accountId)
  const [showDepositDetails, setShowDepositDetails] = useState(false)
  const depositDetails = useDepositDetails(accountId, showDepositDetails)
  const transactions = useTransactions(accountId)
  const deleteTransaction = useDeleteTransaction(accountId)
  const updateTransaction = useUpdateTransaction(accountId)
  const reorderTransactions = useReorderTransactions(accountId)
  const reorderReapplications = useReorderReapplications(accountId)
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

      <button
        type="button"
        onClick={() => setShowDepositDetails(true)}
        className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm ring-1 ring-slate-200 transition hover:bg-slate-50"
      >
        <Layers3 size={17} />
        Detalhes dos depósitos
      </button>

      <AccountCharts monthly={monthly} />

      <HistoryCard
        accountId={accountId}
        transactions={transactions}
        monthly={monthly}
        deleteTransaction={deleteTransaction}
        updateTransaction={updateTransaction}
        reorderTransactions={reorderTransactions}
        reorderReapplications={reorderReapplications}
        accountCdiPercent={data.cdi_percent}
        openedOn={data.opened_on}
        onNew={() => setShowTransactionForm(true)}
      />

      <NewTransactionDialog
        open={showTransactionForm}
        onClose={() => setShowTransactionForm(false)}
        accountId={accountId}
        accountCdiPercent={data.cdi_percent}
        openedOn={data.opened_on}
        transactionCount={transactions.data?.length}
      />

      <DepositDetailsDialog
        open={showDepositDetails}
        onClose={() => setShowDepositDetails(false)}
        details={depositDetails.data}
        isPending={depositDetails.isPending}
        isError={depositDetails.isError}
      />
    </div>
  )
}
