import type { InputHTMLAttributes } from 'react'

type FieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string // o texto em cima do campo
  error?: string // a mensagem de erro (se houver)
  hint?: string // uma dica embaixo
}

// Campo de formulário das telas INTERNAS (cartões brancos).
// O TextField continua sendo o das telas de login e cadastro.
export function Field({ label, error, hint, id, ...inputProps }: FieldProps) {
  const fieldId = id ?? inputProps.name

  return (
    <div className="space-y-1">
      <label htmlFor={fieldId} className="block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={fieldId}
        aria-invalid={error ? true : undefined}
        // Cores explícitas (texto escuro, fundo branco) e [color-scheme:light]
        // para o navegador não pintar data e número com o tema escuro do computador.
        className={`w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500 [color-scheme:light] ${
          error ? 'border-red-400' : 'border-slate-300'
        }`}
        {...inputProps}
      />
      {hint && !error && <p className="text-xs text-slate-500">{hint}</p>}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  )
}