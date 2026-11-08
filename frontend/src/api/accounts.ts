import { api } from './client'
import type { Account, AccountInput, AccountSummary, AccountUpdate, MonthlyYields } from './types'

export const accountsApi = {
  // O backend devolve { accounts: [...] }; entregamos só a lista.
  list: () => api.get<{ accounts: Account[] }>('/accounts').then((r) => r.accounts),

  create: (data: AccountInput) =>
    api.post<{ account: Account }>('/accounts', data).then((r) => r.account),

  // Apagar não devolve nada (o backend responde 204, "feito, sem conteúdo").
  remove: (id: string) => api.delete<void>(`/accounts/${id}`),

  // Uma caixinha só.
  get: (id: string) => api.get<{ account: Account }>(`/accounts/${id}`).then((r) => r.account),

  // O resumo calculado pelo motor (saldo, rendimento, imposto).
  summary: (id: string) =>
    api.get<{ summary: AccountSummary }>(`/accounts/${id}/summary`).then((r) => r.summary),

  // Rendimento de cada mês (para o gráfico de barras).
  monthlyYields: (id: string) =>
    api
      .get<{ monthly_yields: MonthlyYields }>(`/accounts/${id}/monthly-yields`)
      .then((r) => r.monthly_yields),

  update: (id: string, data: AccountUpdate) =>
    api.patch<{ account: Account }>(`/accounts/${id}`, data).then((r) => r.account),
}