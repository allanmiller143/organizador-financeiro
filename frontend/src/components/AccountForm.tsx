import { useState, type FormEvent } from 'react'

import { useCreateAccount } from '../hooks/useAccounts'
import { noErrors, toFormErrors } from '../lib/errors'
import { Button } from './Button'
import { Field } from './Field'

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
        opened_on: openedOn,
      })
      onDone() // deu certo: avisa a tela
    } catch (error) {
      setErrors(toFormErrors(error)) // deu errado: mostra no campo certo
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
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
      </div>

      {errors.general && <p className="text-sm text-red-600">{errors.general}</p>}

      <div className="flex items-center gap-4">
        <Button type="submit" loading={createAccount.isPending}>
          Salvar caixinha
        </Button>
        <button
          type="button"
          onClick={onCancel}
          className="text-sm text-slate-600 hover:text-slate-900"
        >
          Cancelar
        </button>
      </div>
    </form>
  )
}