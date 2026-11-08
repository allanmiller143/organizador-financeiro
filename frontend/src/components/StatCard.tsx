import type { LucideIcon } from 'lucide-react'

type StatCardProps = {
  label: string
  value: string
  hint?: string
  icon?: LucideIcon
}

export function StatCard({ label, value, hint, icon: Icon }: StatCardProps) {
  return (
    <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        {Icon && (
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-teal-50 text-teal-600">
            <Icon size={16} />
          </span>
        )}
      </div>
      <p className="mt-3 text-2xl font-semibold tabular-nums text-slate-900">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  )
}