import { Loader2, Sparkles } from 'lucide-react'

export function LoadingState({ message }: { message: string }) {
  return (
    <div className="flex min-h-24 items-center justify-center rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 px-5 py-6 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="relative grid h-10 w-10 place-items-center rounded-xl bg-teal-50 text-teal-600 ring-1 ring-teal-100">
          <Loader2 size={20} className="animate-spin" />
          <Sparkles size={10} className="absolute right-1 top-1 text-sky-500" />
        </span>
        <div>
          <p className="text-sm font-semibold text-slate-700">{message}</p>
          <p className="mt-0.5 text-xs text-slate-400">Só um instante, estamos atualizando seus números.</p>
        </div>
      </div>
    </div>
  )
}
