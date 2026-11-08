import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { AccountUpdate } from '../api/types'
import { accountsApi } from '../api/accounts'

// LER: a lista de caixinhas.
export function useAccounts() {
  return useQuery({
    queryKey: ['accounts'],
    queryFn: accountsApi.list,
  })
}

// Depois de criar ou apagar, o que estava guardado ficou velho.
// Esta função manda buscar de novo a lista de caixinhas E o dashboard.
function useRefreshAfterChange() {
  const queryClient = useQueryClient()
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: ['accounts'] }),
      queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
    ])
}

// GRAVAR: criar uma caixinha.
export function useCreateAccount() {
  const refresh = useRefreshAfterChange()
  return useMutation({ mutationFn: accountsApi.create, onSuccess: refresh })
}

// GRAVAR: apagar uma caixinha.
export function useDeleteAccount() {
  const refresh = useRefreshAfterChange()
  return useMutation({ mutationFn: accountsApi.remove, onSuccess: refresh })
}

// LER: uma caixinha só.
export function useAccount(id: string) {
  return useQuery({
    queryKey: ['accounts', id],
    queryFn: () => accountsApi.get(id),
    retry: false,
  })
}

// LER: o resumo dela (saldo, rendimento, imposto).
export function useAccountSummary(id: string) {
  return useQuery({
    queryKey: ['summary', id],
    queryFn: () => accountsApi.summary(id),
    retry: false,
  })
}

// LER: o rendimento mês a mês de uma caixinha.
export function useMonthlyYields(id: string) {
  return useQuery({
    queryKey: ['monthly-yields', id],
    queryFn: () => accountsApi.monthlyYields(id),
    retry: false,
  })
}

export function useUpdateAccount() {
  const refresh = useRefreshAfterChange()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: AccountUpdate }) =>
      accountsApi.update(id, data),
    onSuccess: refresh,
  })
}