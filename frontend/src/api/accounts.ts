import { api } from './client'
import type { Account, AccountInput, AccountSummary } from './types'

export const accountsApi = {
  list: () => api.get<{ accounts: Account[] }>('/accounts').then((r) => r.accounts),

  create: (data: AccountInput) =>
    api.post<{ account: Account }>('/accounts', data).then((r) => r.account),

    // Uma caixinha só.
  get: (id: string) => api.get<{ account: Account }>(`/accounts/${id}`).then((r) => r.account),

  // O resumo calculado pelo motor (saldo, rendimento, imposto).
  summary: (id: string) =>
    api.get<{ summary: AccountSummary }>(`/accounts/${id}/summary`).then((r) => r.summary),

  remove: (id: string) => api.delete<void>(`/accounts/${id}`),
}