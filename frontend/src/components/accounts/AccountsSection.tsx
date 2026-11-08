import type { ReactNode } from 'react'

type AccountsSectionProps = {
  title?: string
  muted?: boolean // para a lista de arquivadas
  children: ReactNode
}

export function AccountsSection({ title, muted = false, children }: AccountsSectionProps) {
  return (
    <section className="space-y-3">
      {title && <h2 className="text-sm font-medium text-slate-500">{title}</h2>}
      <ul
        className={`divide-y divide-slate-100 rounded-2xl bg-white shadow-sm ring-1 ring-slate-200 ${
          muted ? 'opacity-75' : ''
        }`}
      >
        {children}
      </ul>
    </section>
  )
}