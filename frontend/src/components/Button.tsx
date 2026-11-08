import type { ButtonHTMLAttributes } from 'react'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean
}

export function Button({ loading, children, disabled, className = '', ...props }: ButtonProps) {
  return (
    <button
      disabled={disabled || loading} // enquanto carrega, não deixa clicar de novo
      className={`rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:opacity-60 ${className}`}
      {...props}
    >
      {loading ? 'Aguarde...' : children}
    </button>
  )
}