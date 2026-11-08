import { useState, type FormEvent } from 'react'

import type { TransactionKind } from '../api/types'
import { useCreateTransaction } from '../hooks/useTransactions'
import { noErrors, toFormErrors } from '../lib/errors'
import { todayIso } from '../lib/format'
import { Button } from './Button'
import { Field } from './Field'

type TransactionFormProps = {
  accountId: string
  openedOn: string // a data não pode ser anterior à abertura da caixinha
}

export function TransactionForm({ accountId, openedOn }: TransactionFormProps) {
  const createTransaction = useCreateTransaction(accountId)

  const [kind, setKind] = useState<TransactionKind>('DEPOSIT')
  const [amount, setAmount] = useState('')
  const [occurredOn, setOccurredOn] = useState(todayIso())
  const [note, setNote] = useState('')
  const [errors, setErrors] = useState(noErrors)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrors(noErrors)
    try {
      await createTransaction.mutateAsync({
        kind,
        amount,
        occurred_on: occurredOn,
        note: note.trim() || null, // texto vazio vira "sem observação"
      })
      // Deu certo: limpamos só valor e observação (tipo e data costumam se repetir).
      setAmount('')
      setNote('')
    } catch (error) {
      setErrors(toFormErrors(error))
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1">
          <label htmlFor="kind" className="block text-sm font-medium text-slate-700">
            Tipo
          </label>
          <select
            id="kind"
            value={kind}
            onChange={(e) => setKind(e.target.value as TransactionKind)}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"          >
            <option value="DEPOSIT">Aporte (dinheiro entrando)</option>
            <option value="WITHDRAWAL">Retirada (dinheiro saindo)</option>
          </select>
        </div>

        <Field
          label="Valor (R$)"
          name="amount"
          type="number"
          required
          min="0.01"
          step="0.01"
          placeholder="0,00"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          error={errors.fields.amount}
        />

        <Field
          label="Data"
          name="occurred_on"
          type="date"
          required
          min={openedOn}
          max={todayIso()}
          value={occurredOn}
          onChange={(e) => setOccurredOn(e.target.value)}
          error={errors.fields.occurred_on}
        />

        <Field
          label="Observação (opcional)"
          name="note"
          maxLength={255}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          error={errors.fields.note}
        />
      </div>

      {errors.general && <p className="text-sm text-red-600">{errors.general}</p>}

      <Button type="submit" loading={createTransaction.isPending}>
        Registrar lançamento
      </Button>
    </form>
  )
}