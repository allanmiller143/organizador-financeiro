import type { useDashboard } from '../../hooks/useDashboard'

// Os tipos saem do próprio hook, então ficam sempre iguais ao que a API devolve.
export type DashboardData = NonNullable<ReturnType<typeof useDashboard>['data']>
export type Totals = DashboardData['totals']
export type Account = DashboardData['accounts'][number]