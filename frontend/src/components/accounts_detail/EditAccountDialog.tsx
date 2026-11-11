import { useState, type FormEvent } from 'react'
import { Info, Pencil } from 'lucide-react'

import type { Account } from '../../api/types'
import { useUpdateAccount } from '../../hooks/useAccounts'
import { noErrors, toFormErrors } from '../../lib/errors'
import { formatCdi } from '../../lib/format'
import { Button } from '../Button'
import { Dialog } from '../Dialog'
import { ErrorMessage } from '../ErrorMessage'
import { Field } from '../Field'

type EditFormProps = {
  account: Account
  onClose: () => void
}

function EditAccountForm({ account, onClose }: EditFormProps) {
  const edit = useUpdateAccount()
  const [name, setName] = useState(account.name)
  const [institution, setInstitution] = useState(account.institution)
  const [goalAmount, setGoalAmount] = useState(account.goal_amount ?? '')

  // Estado derivado: os erros saem direto do erro da gravação.
  const errors = edit.error ? toFormErrors(edit.error) : noErrors

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      await edit.mutateAsync({
        id: account.id,
        data: { name, institution, goal_amount: goalAmount || null },
      })
      onClose() // deu certo: fecha o dialog
    } catch {
      // o erro já ficou em edit.error e aparece embaixo dos campos
    }
  }

  return (
    <form onSubmit={handleSave} className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field
          label="Nome da caixinha"
          name="name"
          required
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
          label="Meta de valor (opcional)"
          name="goal_amount"
          type="number"
          min="0.01"
          step="0.01"
          hint="Deixe em branco para remover a meta."
          value={goalAmount}
          onChange={(e) => setGoalAmount(e.target.value)}
          error={errors.fields.goal_amount}
        />
      </div>

      <p className="flex items-start gap-2 rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-600">
        <Info size={14} className="mt-0.5 shrink-0 text-slate-400" />
        O rendimento ({formatCdi(account.cdi_percent)}) e a data de abertura não podem ser
        alterados.
      </p>

      {errors.general && <ErrorMessage message={errors.general} />}

      <div className="flex items-center gap-3">
        <Button type="submit" variant="primary" loading={edit.isPending}>
          Salvar
        </Button>
        <Button type="button" variant="secondary" onClick={onClose}>
          Cancelar
        </Button>
      </div>
    </form>
  )
}

type EditAccountDialogProps = {
  account: Account
  open: boolean
  onClose: () => void
}

export function EditAccountDialog({ account, open, onClose }: EditAccountDialogProps) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      icon={Pencil}
      title="Editar caixinha"
      subtitle="Mude o nome ou a instituição"
    >
      <EditAccountForm account={account} onClose={onClose} />
    </Dialog>
  )
}
