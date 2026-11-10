import { useEffect, type ReactNode } from 'react'
import { X, type LucideIcon } from 'lucide-react'

type DrawerProps = {
  open: boolean
  onClose: () => void
  title: string
  subtitle?: string
  icon?: LucideIcon
  children: ReactNode
}

export function Drawer({ open, onClose, title, subtitle, icon: Icon, children }: DrawerProps) {
  useEffect(() => {
    if (!open) return
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="presentation">
      <button
        type="button"
        aria-label="Fechar detalhes dos depósitos"
        onClick={onClose}
        className="absolute inset-0 cursor-default bg-slate-900/50"
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="deposit-details-title"
        className="relative flex h-full w-full max-w-3xl flex-col bg-white shadow-2xl"
      >
        <header className="relative shrink-0 overflow-hidden bg-gradient-to-br from-sky-500 to-teal-600 px-6 py-5 text-white sm:px-8">
          <div className="pointer-events-none absolute -right-10 -top-12 h-40 w-40 rounded-full bg-white/10" />
          <div className="relative flex items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              {Icon && <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white/20 ring-1 ring-white/30"><Icon size={22} /></span>}
              <div>
                <h2 id="deposit-details-title" className="text-lg font-semibold leading-tight">{title}</h2>
                {subtitle && <p className="mt-0.5 text-sm text-white/80">{subtitle}</p>}
              </div>
            </div>
            <button type="button" onClick={onClose} aria-label="Fechar" className="grid h-9 w-9 shrink-0 place-items-center rounded-lg text-white/80 transition hover:bg-white/20 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white">
              <X size={19} />
            </button>
          </div>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto bg-slate-50 p-5 sm:p-8">{children}</div>
      </aside>
    </div>
  )
}
