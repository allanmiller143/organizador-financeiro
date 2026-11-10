import { useEffect, type ReactNode } from 'react'
import { X, type LucideIcon } from 'lucide-react'

type DialogProps = {
  open: boolean
  onClose: () => void
  title: string
  subtitle?: string
  icon?: LucideIcon
  children: ReactNode
}

export function Dialog({ open, onClose, title, subtitle, icon: Icon, children }: DialogProps) {
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
    <div className="fixed inset-0 z-50 grid place-items-center p-4" role="presentation">
      <button
        type="button"
        aria-label="Fechar janela"
        onClick={onClose}
        className="absolute inset-0 cursor-default bg-slate-900/50"
      />
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        className="relative flex max-h-[90vh] w-full max-w-lg flex-col overflow-hidden rounded-3xl bg-white shadow-2xl"
      >
        <div className="relative shrink-0 overflow-hidden bg-gradient-to-br from-sky-500 to-teal-600 px-6 py-5 text-white">
          <div className="pointer-events-none absolute -right-10 -top-12 h-40 w-40 rounded-full bg-white/10" />
          <div className="pointer-events-none absolute -bottom-16 right-16 h-32 w-32 rounded-full bg-white/10" />
          <div className="relative flex items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              {Icon && <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white/20 ring-1 ring-white/30"><Icon size={22} /></span>}
              <div>
                <h2 id="dialog-title" className="text-lg font-semibold leading-tight">{title}</h2>
                {subtitle && <p className="mt-0.5 text-sm text-white/80">{subtitle}</p>}
              </div>
            </div>
            <button type="button" onClick={onClose} aria-label="Fechar" className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-white/80 transition hover:bg-white/20 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white">
              <X size={18} />
            </button>
          </div>
        </div>
        <div className="overflow-y-auto p-6">{children}</div>
      </section>
    </div>
  )
}
