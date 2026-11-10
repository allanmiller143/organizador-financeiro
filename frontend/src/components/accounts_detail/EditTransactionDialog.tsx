import { useState, type FormEvent } from 'react'
import { Pencil } from 'lucide-react'

import type { Transaction } from '../../api/types'
import { noErrors, toFormErrors } from '../../lib/errors'
import { todayIso } from '../../lib/format'
import type { UpdateTransactionMutation } from './types'
import { Button } from '../Button'
import { Dialog } from '../Dialog'
import { ErrorMessage } from '../ErrorMessage'
import { Field } from '../Field'
import { RateSelect } from './RateSelect'
import { CUSTOM_LOCKED_RATE_KEY, optionKeyFor, rateOptions } from './rateOptions'

type EditTransactionDialogProps = {
  transaction: Transaction | null
  accountCdiPercent: string
  openedOn: string
  updateTransaction: UpdateTransactionMutation
  onClose: () => void
}

function EditTransactionForm({
  transaction,
  accountCdiPercent,
  openedOn,
  updateTransaction,
  onClose,
}: Omit<EditTransactionDialogProps, 'transaction'> & { transaction: Transaction }) {
  const [amount, setAmount] = useState(transaction.amount)
  const [occurredOn, setOccurredOn] = useState(transaction.occurred_on)
  const [note, setNote] = useState(transaction.note ?? '')
  const [rateKey, setRateKey] = useState(optionKeyFor(accountCdiPercent, transaction))
  const [customCdiPercent, setCustomCdiPercent] = useState(transaction.cdi_percent)
  const [errors, setErrors] = useState(noErrors)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrors(noErrors)
    const options = rateOptions(accountCdiPercent)
    const option = options.find((item) => item.key === rateKey) ?? options[0]
    const isDeposit = transaction.kind === 'DEPOSIT'
    try {
      await updateTransaction.mutateAsync({
        id: transaction.id,
        data: {
          amount,
          occurred_on: occurredOn,
          note: note.trim() || null,
          cdi_percent: isDeposit ? (rateKey === CUSTOM_LOCKED_RATE_KEY ? customCdiPercent : option.cdiPercent) : accountCdiPercent,
          term_months: isDeposit ? (rateKey === CUSTOM_LOCKED_RATE_KEY ? 6 : option.termMonths) : 24,
          locked: isDeposit && (rateKey === CUSTOM_LOCKED_RATE_KEY || option.locked),
        },
      })
      onClose()
    } catch (error) {
      setErrors(toFormErrors(error))
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field
          label="Valor (R$)"
          name="amount"
          type="number"
          required
          min="0.01"
          step="0.01"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
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
          onChange={(event) => setOccurredOn(event.target.value)}
          error={errors.fields.occurred_on}
        />
        {transaction.kind === 'DEPOSIT' && (
          <RateSelect
            id="edit_cdi_percent"
            accountCdiPercent={accountCdiPercent}
            value={rateKey}
            onChange={setRateKey}
            customCdiPercent={customCdiPercent}
            onCustomCdiPercentChange={setCustomCdiPercent}
          />
        )}
        <div className="sm:col-span-2">
          <Field
            label="Observação (opcional)"
            name="note"
            maxLength={255}
            value={note}
            onChange={(event) => setNote(event.target.value)}
            error={errors.fields.note}
          />
        </div>
      </div>

      {errors.general && <ErrorMessage message={errors.general} />}

      <div className="flex items-center gap-3">
        <Button type="submit" variant="primary" loading={updateTransaction.isPending}>
          Salvar alterações
        </Button>
        <Button type="button" variant="secondary" onClick={onClose}>
          Cancelar
        </Button>
      </div>
    </form>
  )
}

export function EditTransactionDialog(props: EditTransactionDialogProps) {
  const { transaction, accountCdiPercent, openedOn, updateTransaction, onClose } = props
  const transactionLabel = transaction?.kind === 'DEPOSIT' ? 'aporte' : 'retirada'
  return (
    <Dialog
      open={transaction !== null}
      onClose={onClose}
      icon={Pencil}
      title={`Editar ${transactionLabel}`}
      subtitle="Corrija o valor, a data ou a observação"
    >
      {transaction && (
        <EditTransactionForm
          key={transaction.id}
          transaction={transaction}
          accountCdiPercent={accountCdiPercent}
          openedOn={openedOn}
          updateTransaction={updateTransaction}
          onClose={onClose}
        />
      )}
    </Dialog>
  )
}
