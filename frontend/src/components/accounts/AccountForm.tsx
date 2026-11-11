import { useState, type FormEvent } from 'react'

import { useCreateAccount } from '../../hooks/useAccounts'
import { noErrors, toFormErrors } from '../../lib/errors'
import { Button } from '../Button'
import { ErrorMessage } from '../ErrorMessage'
import { Field } from '../Field'

type AccountFormProps = {
  onDone: () => void // o que fazer quando terminar (a tela fecha o formulário)
  onCancel: () => void
}

export function AccountForm({ onDone, onCancel }: AccountFormProps) {
  const createAccount = useCreateAccount()

  // Uma caixinha de memória para cada campo.
  const [name, setName] = useState('')
  const [institution, setInstitution] = useState('Nubank')
  const [cdiPercent, setCdiPercent] = useState('100')
  const [goalAmount, setGoalAmount] = useState('')
  const [openedOn, setOpenedOn] = useState('')
  const [errors, setErrors] = useState(noErrors)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrors(noErrors)
    try {
      await createAccount.mutateAsync({
        name,
        institution,
        cdi_percent: cdiPercent,
        goal_amount: goalAmount || null,
        opened_on: openedOn,
      })
      onDone() // deu certo: avisa a tela
    } catch (error) {
      setErrors(toFormErrors(error)) // deu errado: mostra no campo certo
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field
          label="Nome da caixinha"
          name="name"
          required
          placeholder="Ex.: Reserva de emergência"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.fields.name}
        />
        <Field
          label="Instituição"
          name="institution"
          required
          value={institution}
          onChange={(e) => setInstitution(e.target.value)}
          error={errors.fields.institution}
        />
        <Field
          label="Rendimento (% do CDI)"
          name="cdi_percent"
          type="number"
          required
          min="0.01"
          max="500"
          step="0.01"
          hint="100% significa que rende o mesmo que o CDI."
          value={cdiPercent}
          onChange={(e) => setCdiPercent(e.target.value)}
          error={errors.fields.cdi_percent}
        />
        <Field
          label="Data de abertura"
          name="opened_on"
          type="date"
          required
          value={openedOn}
          onChange={(e) => setOpenedOn(e.target.value)}
          error={errors.fields.opened_on}
        />
        <Field
          label="Meta de valor (opcional)"
          name="goal_amount"
          type="number"
          min="0.01"
          step="0.01"
          hint="Acompanhe o progresso e estime o prazo para alcançar a meta."
          value={goalAmount}
          onChange={(e) => setGoalAmount(e.target.value)}
          error={errors.fields.goal_amount}
        />
      </div>

      {errors.general && <ErrorMessage message={errors.general} />}

      <div className="flex items-center gap-3">
        <Button type="submit" variant="primary" loading={createAccount.isPending}>
          Salvar caixinha
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancelar
        </Button>
      </div>
    </form>
  )
}
