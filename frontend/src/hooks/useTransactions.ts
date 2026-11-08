import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { transactionsApi } from '../api/transactions'
import type { TransactionInput } from '../api/types'

// LER: o histórico de uma caixinha.
export function useTransactions(accountId: string) {
  return useQuery({
    queryKey: ['transactions', accountId],
    queryFn: () => transactionsApi.list(accountId),
  })
}

// Uma mudança no histórico deixa três coisas velhas: o próprio histórico,
// o resumo desta caixinha e o dashboard. Buscamos as três de novo.
function useRefreshAfterChange(accountId: string) {
  const queryClient = useQueryClient()
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: ['transactions', accountId] }),
      queryClient.invalidateQueries({ queryKey: ['summary', accountId] }),
      queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
    ])
}

// GRAVAR: registrar um aporte ou uma retirada.
export function useCreateTransaction(accountId: string) {
  const refresh = useRefreshAfterChange(accountId)
  return useMutation({
    mutationFn: (data: TransactionInput) => transactionsApi.create(accountId, data),
    onSuccess: refresh,
  })
}

// GRAVAR: apagar um lançamento.
export function useDeleteTransaction(accountId: string) {
  const refresh = useRefreshAfterChange(accountId)
  return useMutation({
    mutationFn: transactionsApi.remove,
    onSuccess: refresh,
  })
}