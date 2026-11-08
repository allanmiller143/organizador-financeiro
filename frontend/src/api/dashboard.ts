import { api } from './client'
import type { Dashboard } from './types'

export const dashboardApi = {
  get: () => api.get<{ dashboard: Dashboard }>('/dashboard').then((response) => response.dashboard),
}