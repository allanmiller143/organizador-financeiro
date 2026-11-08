import type { InputHTMLAttributes } from 'react'

type FieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  error?: string
  hint?: string // texto de ajuda, aparece quando não há erro
}

export function Field({ label, error, hint, id, name, className = '', ...props }: FieldProps) {
  const inputId = id ?? name

  return (
    <div>
      <label htmlFor={inputId} className="mb-1.5 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={inputId}
        name={name}
        aria-invalid={error ? true : undefined}
        className={`w-full rounded-xl border bg-white px-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 outline-none transition hover:border-slate-400 focus:ring-2 ${
          error
            ? 'border-red-400 focus:border-red-500 focus:ring-red-500/20'
            : 'border-slate-300 focus:border-teal-500 focus:ring-teal-500/20'
        } ${className}`}
        {...props}
      />
      {error ? (
        <p className="mt-1 text-xs text-red-600">{error}</p>
      ) : (
        hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>
      )}
    </div>
  )
}