export type Basis = 'gross' | 'net'

type BasisSwitchProps = {
  value: Basis
  onChange: (value: Basis) => void
}

const options: { value: Basis; label: string }[] = [
  { value: 'gross', label: 'Bruto' },
  { value: 'net', label: 'Líquido' },
]

export function BasisSwitch({ value, onChange }: BasisSwitchProps) {
  return (
    <div
      role="group"
      aria-label="Tipo de valor"
      className="inline-flex shrink-0 rounded-lg bg-slate-100 p-0.5 text-xs font-medium"
    >
      {options.map((option) => {
        const active = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            aria-pressed={active}
            className={`cursor-pointer rounded-md px-2.5 py-1 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 ${
              active
                ? 'bg-white text-teal-700 shadow-sm'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}