import { useEffect, useRef, type ReactNode } from 'react'
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
  const ref = useRef<HTMLDialogElement>(null)

  // Abre e fecha o <dialog> nativo conforme a prop "open".
  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return

    if (open && !dialog.open) {
      dialog.showModal()
      // Foca o primeiro campo, em vez do botão X.
      dialog.querySelector<HTMLElement>('input, select, textarea')?.focus()
    }
    if (!open && dialog.open) {
      dialog.close()
    }
  }, [open])

  return (
    <dialog
      ref={ref}
      onClose={onClose} // dispara com Esc e com dialog.close()
      onClick={(event) => {
        // Clique no fundo escurecido (o próprio <dialog>) fecha.
        if (event.target === ref.current) onClose()
      }}
      className="m-auto max-h-[90vh] w-full max-w-lg flex-col overflow-hidden rounded-3xl bg-white p-0 shadow-2xl open:flex backdrop:bg-slate-900/50"
    >
      {/* Só monta o conteúdo quando aberto: o formulário sempre começa limpo. */}
      {open && (
        <>
          {/* Faixa de cima, com a cara do app */}
          <div className="relative shrink-0 overflow-hidden bg-gradient-to-br from-sky-500 to-teal-600 px-6 py-5 text-white">
            <div className="pointer-events-none absolute -right-10 -top-12 h-40 w-40 rounded-full bg-white/10" />
            <div className="pointer-events-none absolute -bottom-16 right-16 h-32 w-32 rounded-full bg-white/10" />

            <div className="relative flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                {Icon && (
                  <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white/20 ring-1 ring-white/30">
                    <Icon size={22} />
                  </span>
                )}
                <div>
                  <h2 className="text-lg font-semibold leading-tight">{title}</h2>
                  {subtitle && <p className="mt-0.5 text-sm text-white/80">{subtitle}</p>}
                </div>
              </div>

              <button
                type="button"
                onClick={onClose}
                aria-label="Fechar"
                className="grid h-8 w-8 shrink-0 cursor-pointer place-items-center rounded-lg text-white/80 transition hover:bg-white/20 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* Corpo branco, que rola sozinho se o conteúdo for grande */}
          <div className="overflow-y-auto p-6">{children}</div>
        </>
      )}
    </dialog>
  )
}