import type { MonthlyYield } from '../../api/types'
import type { useAccountSummary, useMonthlyYields } from '../../hooks/useAccounts'
import type { useDeleteTransaction, useTransactions } from '../../hooks/useTransactions'

// Os tipos saem dos próprios hooks, então ficam sempre iguais ao que a API devolve.
export type SummaryQuery = ReturnType<typeof useAccountSummary>
export type MonthlyQuery = ReturnType<typeof useMonthlyYields>
export type TransactionsQuery = ReturnType<typeof useTransactions>
export type DeleteTransactionMutation = ReturnType<typeof useDeleteTransaction>

// Um mês da série. Os campos extras ainda não existem na API: quando existirem, os
// gráficos de saldo e o alternador bruto/líquido passam a funcionar sozinhos.
export type MonthPoint = MonthlyYield & {
  net_yield_amount?: string | null // rendimento do mês, depois do IR
  gross_balance?: string | null // saldo bruto no fim do mês
  net_balance?: string | null // saldo líquido no fim do mês
}