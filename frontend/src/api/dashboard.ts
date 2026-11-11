import { api } from './client'
import type { Dashboard } from './types'

export const dashboardApi = {
  get: () => api.get<{ dashboard: Dashboard }>('/dashboard').then((response) => response.dashboard),
  syncCdi: () => api.post<{ inserted: number; latest_date: string | null; message: string }>('/cdi/sync'),
}
