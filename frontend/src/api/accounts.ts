import { api } from './client'
import type { Account, AccountInput } from './types'

export const accountsApi = {
  list: () => api.get<{ accounts: Account[] }>('/accounts').then((r) => r.accounts),

  create: (data: AccountInput) =>
    api.post<{ account: Account }>('/accounts', data).then((r) => r.account),

  remove: (id: string) => api.delete<void>(`/accounts/${id}`),
}