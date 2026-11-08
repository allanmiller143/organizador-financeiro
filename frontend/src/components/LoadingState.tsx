import { Loader2 } from 'lucide-react'

export function LoadingState({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-2 text-slate-500">
      <Loader2 size={18} className="animate-spin text-teal-600" />
      <p>{message}</p>
    </div>
  )
}