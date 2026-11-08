import { useState, type FormEvent } from 'react'

import type { SimulationInput } from '../api/types'
import type { FormErrors } from '../lib/errors'
import { formatMoney } from '../lib/format'
import { Button } from './Button'
import { Field } from './Field'

type SimulationFormProps = {
  onSubmit: (input: SimulationInput) => void
  loading: boolean
  errors: FormErrors
  currentBalance?: string // o saldo bruto de hoje, para o botão de atalho
}

export function SimulationForm({ onSubmit, loading, errors, currentBalance }: SimulationFormProps) {
  // Uma caixinha de memória por campo (todos guardam texto, como o input entrega).
  const [initial, setInitial] = useState('0')
  const [deposit, setDeposit] = useState('500')
  const [withdrawal, setWithdrawal] = useState('0')
  const [withdrawalStart, setWithdrawalStart] = useState('1')
  const [years, setYears] = useState('10')
  const [cdiAnnual, setCdiAnnual] = useState('14')
  const [cdiPercent, setCdiPercent] = useState('100')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onSubmit({
      initial_amount: initial,
      monthly_deposit: deposit,
      monthly_withdrawal: withdrawal,
      withdrawal_start_month: Number(withdrawalStart),
      horizon_months: Number(years) * 12, // a tela fala em anos, o backend em meses
      expected_cdi_annual: cdiAnnual,
      cdi_percent: cdiPercent,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Field
          label="Valor inicial (R$)"
          name="initial_amount"
          type="number"
          required
          min="0"
          step="0.01"
          value={initial}
          onChange={(e) => setInitial(e.target.value)}
          error={errors.fields.initial_amount}
        />
        <Field
          label="Aporte mensal (R$)"
          name="monthly_deposit"
          type="number"
          required
          min="0"
          step="0.01"
          value={deposit}
          onChange={(e) => setDeposit(e.target.value)}
          error={errors.fields.monthly_deposit}
        />
        <Field
          label="Retirada mensal (R$)"
          name="monthly_withdrawal"
          type="number"
          required
          min="0"
          step="0.01"
          value={withdrawal}
          onChange={(e) => setWithdrawal(e.target.value)}
          error={errors.fields.monthly_withdrawal}
        />
        <Field
          label="Retiradas começam no mês nº"
          name="withdrawal_start_month"
          type="number"
          required
          min="1"
          step="1"
          hint="1 = já no primeiro mês."
          value={withdrawalStart}
          onChange={(e) => setWithdrawalStart(e.target.value)}
          error={errors.fields.withdrawal_start_month}
        />
        <Field
          label="Quanto tempo (anos)"
          name="years"
          type="number"
          required
          min="1"
          max="50"
          step="1"
          value={years}
          onChange={(e) => setYears(e.target.value)}
          error={errors.fields.horizon_months}
        />
        <Field
          label="CDI anual esperado (%)"
          name="expected_cdi_annual"
          type="number"
          required
          min="0.01"
          max="100"
          step="0.01"
          hint="É uma premissa sua: ninguém sabe o CDI do futuro."
          value={cdiAnnual}
          onChange={(e) => setCdiAnnual(e.target.value)}
          error={errors.fields.expected_cdi_annual}
        />
        <Field
          label="Rendimento da caixinha (% do CDI)"
          name="cdi_percent"
          type="number"
          required
          min="0.01"
          max="500"
          step="0.01"
          value={cdiPercent}
          onChange={(e) => setCdiPercent(e.target.value)}
          error={errors.fields.cdi_percent}
        />
      </div>

      {/* Atalho: só aparece se você já tem saldo. */}
      {currentBalance && Number(currentBalance) > 0 && (
        <button
          type="button"
          onClick={() => setInitial(currentBalance)}
          className="text-sm font-medium text-emerald-700 hover:underline"
        >
          Usar meu saldo atual ({formatMoney(currentBalance)}) como valor inicial
        </button>
      )}

      {errors.general && <p className="text-sm text-red-600">{errors.general}</p>}

      <div>
        <Button type="submit" loading={loading}>
          Simular
        </Button>
      </div>
    </form>
  )
}