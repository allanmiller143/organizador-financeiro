import { useState, type InputHTMLAttributes } from 'react'
import { Eye, EyeOff, type LucideIcon } from 'lucide-react'

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  error?: string
  icon?: LucideIcon
}

export function TextField({
  label,
  error,
  icon: Icon,
  type = 'text',
  id,
  name,
  ...props
}: TextFieldProps) {
  const [visible, setVisible] = useState(false)
  const isPassword = type === 'password'
  const inputId = id ?? name

  return (
    <div>
      <label htmlFor={inputId} className="sr-only">
        {label}
      </label>
      <div className="relative">
        <input
          id={inputId}
          name={name}
          type={isPassword && visible ? 'text' : type}
          placeholder={label}
          className="w-full rounded-xl border border-white/40 bg-white/5 px-4 py-3 pr-12 text-sm text-white placeholder-white/70 outline-none transition hover:border-white/70 hover:bg-white/10 focus:border-white focus:bg-white/15 focus:ring-2 focus:ring-white/30"
          {...props}
        />

        {isPassword ? (
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? 'Ocultar senha' : 'Mostrar senha'}
            className="absolute right-2 top-1/2 -translate-y-1/2 cursor-pointer rounded-lg p-1.5 text-sky/70 transition hover:bg-white/15 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
          >
            {visible ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        ) : (
          Icon && (
            <Icon
              size={18}
              className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[#ff8800]/70"
            />
          )
        )}
      </div>
      {error && <p className="mt-1 text-xs text-red-300">{error}</p>}
    </div>
  )
}