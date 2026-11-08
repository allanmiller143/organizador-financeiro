import type { ButtonHTMLAttributes } from 'react'
import { Loader2 } from 'lucide-react'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean
}

export function Button({ loading, children, className = '', disabled, ...props }: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={`inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-sky-300/70 to-teal-700/70 px-4 py-3 text-base font-semibold text-white shadow-lg transition duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70 active:translate-y-0 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:hover:brightness-100 ${className}`}
      {...props}
    >
      {loading && <Loader2 size={18} className="animate-spin" />}
      {children}
    </button>
  )
}