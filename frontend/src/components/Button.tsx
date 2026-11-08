import type { ButtonHTMLAttributes } from 'react'
import { Loader2 } from 'lucide-react'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean
  // primary/secondary = dentro do app · glass = login/cadastro (sobre a foto)
  variant?: 'primary' | 'secondary' | 'glass'
}

const base =
  'inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl font-semibold transition duration-200 focus-visible:outline-none focus-visible:ring-2 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60'

const variants = {
  primary:
    'bg-teal-600 px-4 py-2.5 text-sm text-white shadow-sm hover:bg-teal-700 focus-visible:ring-teal-500 focus-visible:ring-offset-2',
  secondary:
    'bg-white px-4 py-2.5 text-sm text-slate-700 ring-1 ring-slate-300 hover:bg-slate-50 focus-visible:ring-teal-500 focus-visible:ring-offset-2',
  glass:
    'bg-gradient-to-r from-sky-300/70 to-teal-700/70 px-4 py-3 text-base text-white shadow-lg hover:-translate-y-0.5 hover:shadow-xl hover:brightness-110 focus-visible:ring-white/70 active:translate-y-0 disabled:hover:translate-y-0 disabled:hover:brightness-100',
}

export function Button({
  loading,
  variant = 'primary',
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={`${base} ${variants[variant]} ${className}`}
      {...props}
    >
      {loading && <Loader2 size={18} className="animate-spin" />}
      {children}
    </button>
  )
}