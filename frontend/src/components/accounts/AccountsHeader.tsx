import { Plus } from 'lucide-react'

import { Button } from '../Button'

type AccountsHeaderProps = {
  activeCount: number
  archivedCount: number
  onNew: () => void
}

export function AccountsHeader({ activeCount, archivedCount, onNew }: AccountsHeaderProps) {
  return (
    <div className="flex items-center justify-between gap-4">
      <p className="text-sm text-slate-600">
        <span className="font-semibold text-slate-900">{activeCount}</span>{' '}
        {activeCount === 1 ? 'caixinha ativa' : 'caixinhas ativas'}
        {archivedCount > 0 && (
          <span className="text-slate-400">
            {' '}
            · {archivedCount} {archivedCount === 1 ? 'arquivada' : 'arquivadas'}
          </span>
        )}
      </p>

      <Button variant="primary" onClick={onNew}>
        <Plus size={16} />
        Nova caixinha
      </Button>
    </div>
  )
}