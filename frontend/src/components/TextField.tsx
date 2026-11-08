import type { InputHTMLAttributes } from 'react'

// Aceita tudo que um <input> normal aceita, mais três extras nossos.
type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string // o texto em cima do campo
  error?: string // a mensagem de erro (se houver)
  hint?: string // uma dica embaixo (ex.: "mínimo de 8 caracteres")
}

export function TextField({ label, error, hint, id, ...inputProps }: TextFieldProps) {
  const fieldId = id ?? inputProps.name

  return (
    <div className="space-y-1">
      <label htmlFor={fieldId} className="block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={fieldId}
        aria-invalid={error ? true : undefined}
        className={`w-full rounded-lg border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-emerald-500 ${
          error ? 'border-red-400' : 'border-slate-300'
        }`}
        {...inputProps}
      />
      {hint && !error && <p className="text-xs text-slate-500">{hint}</p>}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  )
}