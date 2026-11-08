import { AlertCircle } from 'lucide-react'

export function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-3 rounded-2xl bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-100">
      <AlertCircle size={18} className="mt-0.5 shrink-0" />
      <p>{message}</p>
    </div>
  )
}