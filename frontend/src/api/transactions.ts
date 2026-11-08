import { api } from './client'
import type { Transaction, TransactionInput } from './types'

export const transactionsApi = {
  // O histórico de uma caixinha (o backend já devolve do mais novo para o mais antigo).
  list: (accountId: string) =>
    api
      .get<{ transactions: Transaction[] }>(`/accounts/${accountId}/transactions`)
      .then((r) => r.transactions),

  create: (accountId: string, data: TransactionInput) =>
    api
      .post<{ transaction: Transaction }>(`/accounts/${accountId}/transactions`, data)
      .then((r) => r.transaction),

  // Repare: para apagar, o endereço usa o id da transação, sem a caixinha.
  remove: (transactionId: string) => api.delete<void>(`/transactions/${transactionId}`),
}