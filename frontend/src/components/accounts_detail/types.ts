import type { MonthlyYield, Reapplication, Transaction } from '../../api/types'
import type { useAccountSummary, useMonthlyYields } from '../../hooks/useAccounts'
import type {
  useDeleteTransaction,
  useTransactions,
  useUpdateTransaction,
} from '../../hooks/useTransactions'

// Os tipos saem dos próprios hooks, então ficam sempre iguais ao que a API devolve.
export type SummaryQuery = ReturnType<typeof useAccountSummary>
export type MonthlyQuery = ReturnType<typeof useMonthlyYields>
export type TransactionsQuery = ReturnType<typeof useTransactions>
export type DeleteTransactionMutation = ReturnType<typeof useDeleteTransaction>
export type UpdateTransactionMutation = ReturnType<typeof useUpdateTransaction>

export type MonthPoint = MonthlyYield
export type HistoryEntry =
  | { type: 'transaction'; transaction: Transaction; occurred_on: string; id: string }
  | { type: 'reapplication'; reapplication: Reapplication; occurred_on: string; id: string }