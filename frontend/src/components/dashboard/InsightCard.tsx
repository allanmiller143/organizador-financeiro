import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

type InsightCardProps = {
  icon: LucideIcon
  title: string
  subtitle: string
  action?: ReactNode // fica no canto direito do cabeçalho
  children: ReactNode
}

export function InsightCard({ icon: Icon, title, subtitle, action, children }: InsightCardProps) {
  return (
    <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-teal-50 text-teal-600">
            <Icon size={18} />
          </span>
          <div className="min-w-0">
            <h2 className="font-semibold text-slate-900">{title}</h2>
            <p className="truncate text-xs text-slate-500">{subtitle}</p>
          </div>
        </div>
        {action}
      </div>
      {children}
    </section>
  )
}