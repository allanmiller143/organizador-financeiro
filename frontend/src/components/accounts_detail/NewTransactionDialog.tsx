import { useEffect, useRef } from 'react'
import { Plus } from 'lucide-react'

import { Dialog } from '../Dialog'
import { TransactionForm } from '../TransactionForm'

// Fecha o dialog quando aparece um lançamento novo na lista.
function CloseWhenCreated({ count, onClose }: { count?: number; onClose: () => void }) {
  const initialCount = useRef(count) // quantos havia quando o dialog abriu

  useEffect(() => {
    if (initialCount.current !== undefined && count !== undefined && count > initialCount.current) {
      onClose()
    }
  }, [count, onClose])

  return null
}

type NewTransactionDialogProps = {
  open: boolean
  onClose: () => void
  accountId: string
  openedOn: string
  transactionCount?: number
}

export function NewTransactionDialog({
  open,
  onClose,
  accountId,
  openedOn,
  transactionCount,
}: NewTransactionDialogProps) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      icon={Plus}
      title="Novo lançamento"
      subtitle="Registre um aporte ou uma retirada"
    >
      <CloseWhenCreated count={transactionCount} onClose={onClose} />
      <TransactionForm accountId={accountId} openedOn={openedOn} />
    </Dialog>
  )
}