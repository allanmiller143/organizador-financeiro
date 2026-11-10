import { CUSTOM_LOCKED_RATE_KEY, rateOptions } from './rateOptions'

type RateSelectProps = {
  id: string
  accountCdiPercent: string
  value: string
  onChange: (key: string) => void
  customCdiPercent: string
  onCustomCdiPercentChange: (value: string) => void
}

export function RateSelect({ id, accountCdiPercent, value, onChange, customCdiPercent, onCustomCdiPercentChange }: RateSelectProps) {
  const options = rateOptions(accountCdiPercent)

  // Caixinha acima de 100% do CDI: não existe dinheiro trancado, só o rendimento padrão.
  if (options.length === 1) {
    return (
      <div className="space-y-1">
        <span className="block text-sm font-medium text-slate-700">Rentabilidade</span>
        <p className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
          {options[0].label}
        </p>
        <p className="text-xs text-slate-500">
          Esta caixinha rende acima de 100% do CDI e não aceita dinheiro trancado.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-sm font-medium text-slate-700">
        Rentabilidade
      </label>
      <select
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
      >
        {options.map((option) => (
          <option key={option.key} value={option.key}>
            {option.label}
          </option>
        ))}
        <option value={CUSTOM_LOCKED_RATE_KEY}>Outra taxa histórica · 6 meses trancado</option>
      </select>
      {value === CUSTOM_LOCKED_RATE_KEY && (
        <div className="mt-2">
          <label htmlFor={`${id}_custom`} className="block text-xs font-medium text-slate-600">
            Percentual histórico do CDI
          </label>
          <input
            id={`${id}_custom`}
            type="number"
            min="0.01"
            max="1000"
            step="0.01"
            required
            value={customCdiPercent}
            onChange={(event) => onCustomCdiPercentChange(event.target.value)}
            placeholder="Ex.: 101,50"
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
          />
        </div>
      )}
      <p className="text-xs text-slate-500">
        Dinheiro trancado rende mais, mas só pode ser retirado quando o prazo acaba; depois volta a
        render o padrão da caixinha. Todo aporte é reaplicado em 2 anos.
      </p>
    </div>
  )
}
