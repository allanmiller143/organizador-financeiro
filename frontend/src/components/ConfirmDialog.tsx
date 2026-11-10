import { AlertTriangle } from 'lucide-react'

import { Button } from './Button'
import { Dialog } from './Dialog'

type ConfirmDialogProps = {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  loading?: boolean
  onConfirm: () => void
  onClose: () => void
}

export function ConfirmDialog({ open, title, message, confirmLabel = 'Excluir', loading = false, onConfirm, onClose }: ConfirmDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} icon={AlertTriangle} title={title} subtitle="Esta ação não pode ser desfeita">
      <p className="text-sm leading-6 text-slate-600">{message}</p>
      <div className="mt-6 flex flex-wrap justify-end gap-3">
        <Button type="button" variant="secondary" onClick={onClose} disabled={loading}>Cancelar</Button>
        <Button type="button" variant="primary" onClick={onConfirm} loading={loading} className="!bg-rose-600 hover:!bg-rose-700 focus-visible:!ring-rose-500">
          {confirmLabel}
        </Button>
      </div>
    </Dialog>
  )
}
