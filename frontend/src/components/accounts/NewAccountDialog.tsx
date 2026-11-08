import { PiggyBank } from 'lucide-react'

import { Dialog } from '../Dialog'
import { AccountForm } from './AccountForm'

type NewAccountDialogProps = {
  open: boolean
  onClose: () => void
}

export function NewAccountDialog({ open, onClose }: NewAccountDialogProps) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      icon={PiggyBank}
      title="Nova caixinha"
      subtitle="Cadastre onde o seu dinheiro está rendendo"
    >
      <AccountForm onDone={onClose} onCancel={onClose} />
    </Dialog>
  )
}