import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { transactionsApi } from '../api/transactions'
import type { TransactionInput, TransactionUpdate } from '../api/types'

// LER: o histórico de uma caixinha.
export function useTransactions(accountId: string) {
  return useQuery({
    queryKey: ['transactions', accountId],
    queryFn: () => transactionsApi.list(accountId),
    staleTime: 30_000,
    placeholderData: (previousData) => previousData,
  })
}

// Uma mudança no histórico deixa cinco coisas velhas: o próprio histórico,
// o resumo, o gráfico mensal, o dashboard e os detalhes individuais dos lotes.
function useRefreshAfterChange(accountId: string) {
  const queryClient = useQueryClient()
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: ['transactions', accountId] }),
      queryClient.invalidateQueries({ queryKey: ['summary', accountId] }),
      queryClient.invalidateQueries({ queryKey: ['monthly-yields', accountId] }),
      queryClient.invalidateQueries({ queryKey: ['deposit-details', accountId] }),
      queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
    ])
}

// GRAVAR: registrar um aporte ou uma retirada.
export function useCreateTransaction(accountId: string) {
  const refresh = useRefreshAfterChange(accountId)
  return useMutation({
    mutationFn: (data: TransactionInput) => transactionsApi.create(accountId, data),
    onSuccess: () => { void refresh() },
  })
}

// GRAVAR: apagar um lançamento.
export function useDeleteTransaction(accountId: string) {
  const refresh = useRefreshAfterChange(accountId)
  return useMutation({
    mutationFn: transactionsApi.remove,
    onSuccess: () => { void refresh() },
  })
}

export function useUpdateTransaction(accountId: string) {
  const refresh = useRefreshAfterChange(accountId)
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TransactionUpdate }) =>
      transactionsApi.update(id, data),
    onSuccess: () => { void refresh() },
  })
}

export function useReorderTransactions(accountId: string) {
  const refresh = useRefreshAfterChange(accountId)
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (transactionIds: string[]) =>
      transactionsApi.reorder(accountId, transactionIds),
    onMutate: async (transactionIds) => {
      await queryClient.cancelQueries({ queryKey: ['transactions', accountId] })
      const previous = queryClient.getQueryData<import('../api/types').Transaction[]>([
        'transactions',
        accountId,
      ])
      if (previous) {
        const rank = new Map(transactionIds.map((id, index) => [id, index]))
        queryClient.setQueryData(
          ['transactions', accountId],
          previous.map((transaction) =>
            rank.has(transaction.id)
              ? { ...transaction, sort_order: rank.get(transaction.id)! }
              : transaction,
          ),
        )
      }
      return { previous }
    },
    onError: (_error, _ids, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['transactions', accountId], context.previous)
      }
    },
    onSuccess: async () => {
      await refresh()
      // A ordem altera a distribuição dos saques entre os lotes. Force uma
      // nova resposta mesmo quando o drawer de detalhes já estiver aberto.
      await queryClient.refetchQueries({ queryKey: ['deposit-details', accountId] })
    },
  })
}

export function useReorderReapplications(accountId: string) {
  const refresh = useRefreshAfterChange(accountId)
  return useMutation({
    mutationFn: (transactionIds: string[]) =>
      transactionsApi.reorderReapplications(accountId, transactionIds),
    onSuccess: () => { void refresh() },
  })
}
