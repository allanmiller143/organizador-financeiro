import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

type InsightCardProps = {
  icon: LucideIcon
  title: string
  subtitle: string
  children: ReactNode
}

export function InsightCard({ icon: Icon, title, subtitle, children }: InsightCardProps) {
  return (
    <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-center gap-3">
        <span className="grid h-9 w-9 place-items-center rounded-lg bg-teal-50 text-teal-600">
          <Icon size={18} />
        </span>
        <div>
          <h2 className="font-semibold text-slate-900">{title}</h2>
          <p className="text-xs text-slate-500">{subtitle}</p>
        </div>
      </div>
      {children}
    </section>
  )
}