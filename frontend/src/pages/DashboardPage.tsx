import { AccountsCard } from '../components/dashboard/AccountsCard'
import { DashboardError } from '../components/dashboard/DashboardError'
import { DashboardLoading } from '../components/dashboard/DashboardLoading'
import { GrossToNetCard } from '../components/dashboard/GrossToNetCard'
import { HeroCard } from '../components/dashboard/HeroCard'
import { InvestedYieldCard } from '../components/dashboard/InvestedYieldCard'
import { useAuth } from '../hooks/useAuth'
import { useDashboard } from '../hooks/useDashboard'

export default function DashboardPage() {
  const { user } = useAuth()
  const { data, isPending, isError, error } = useDashboard()

  if (isPending) return <DashboardLoading />
  if (isError) return <DashboardError error={error} />

  return (
    <div className="space-y-6">
      <HeroCard totals={data.totals} asOf={data.as_of} userName={user?.name} />

      <div className="grid gap-4 lg:grid-cols-2">
        <InvestedYieldCard totals={data.totals} />
        <GrossToNetCard totals={data.totals} />
      </div>

      <AccountsCard accounts={data.accounts} />
    </div>
  )
}