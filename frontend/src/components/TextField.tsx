import { useState, type InputHTMLAttributes } from 'react'
import { Eye, EyeOff, type LucideIcon } from 'lucide-react'

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  error?: string
  icon?: LucideIcon
  // glass = login/cadastro (sobre a foto) · light = dentro do app (cartões brancos)
  variant?: 'glass' | 'light'
}

const styles = {
  glass: {
    label: 'sr-only',
    input:
      'rounded-xl border border-white/40 bg-white/5 py-3 text-white placeholder-white/70 hover:border-white/70 hover:bg-white/10 focus:border-white focus:bg-white/15 focus:ring-2 focus:ring-white/30',
    icon: 'text-white/70',
    eye: 'text-white/70 hover:bg-white/15 hover:text-white focus-visible:ring-white/60',
    error: 'text-red-300',
  },
  light: {
    label: 'mb-1.5 block text-sm font-medium text-slate-700',
    input:
      'rounded-xl border border-slate-300 bg-white py-2.5 text-slate-900 placeholder-slate-400 hover:border-slate-400 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20',
    icon: 'text-slate-400',
    eye: 'text-slate-500 hover:bg-slate-100 hover:text-slate-700 focus-visible:ring-teal-500',
    error: 'text-red-600',
  },
}

export function TextField({
  label,
  error,
  icon: Icon,
  variant = 'glass',
  type = 'text',
  id,
  name,
  ...props
}: TextFieldProps) {
  const [visible, setVisible] = useState(false)
  const isPassword = type === 'password'
  const inputId = id ?? name
  const s = styles[variant]

  return (
    <div>
      <label htmlFor={inputId} className={s.label}>
        {label}
      </label>
      <div className="relative">
        <input
          id={inputId}
          name={name}
          type={isPassword && visible ? 'text' : type}
          placeholder={variant === 'glass' ? label : undefined}
          className={`w-full px-4 pr-12 text-sm outline-none transition ${s.input}`}
          {...props}
        />

        {isPassword ? (
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? 'Ocultar senha' : 'Mostrar senha'}
            className={`absolute right-2 top-1/2 -translate-y-1/2 cursor-pointer rounded-lg p-1.5 transition focus-visible:outline-none focus-visible:ring-2 ${s.eye}`}
          >
            {visible ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        ) : (
          Icon && (
            <Icon
              size={18}
              className={`pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 ${s.icon}`}
            />
          )
        )}
      </div>
      {error && <p className={`mt-1 text-xs ${s.error}`}>{error}</p>}
    </div>
  )
}