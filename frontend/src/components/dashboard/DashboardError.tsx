import { AlertCircle, RefreshCw } from 'lucide-react'

import { ApiError } from '../../api/client'
import { useSyncCdi } from '../../hooks/useDashboard'

// Transforma o erro técnico numa frase que ajuda a pessoa.
function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === 'cdi_not_synced' || error.code === 'cdi_incomplete') {
      return 'Os dados do CDI ainda não estão completos. O NuBox tenta atualizá-los automaticamente ao abrir; se necessário, tente de novo abaixo.'
    }
    return error.message
  }
  return 'Não foi possível conectar ao servidor.'
}

export function DashboardError({ error }: { error: unknown }) {
  const syncCdi = useSyncCdi()
  return (
    <div className="flex items-start gap-3 rounded-2xl bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-100">
      <AlertCircle size={18} className="mt-0.5 shrink-0" />
      <div className="space-y-2">
        <p>{errorMessage(error)}</p>
        <button
          type="button"
          onClick={() => syncCdi.mutate()}
          disabled={syncCdi.isPending}
          className="inline-flex items-center gap-2 rounded-lg bg-white px-3 py-2 font-medium text-teal-800 ring-1 ring-teal-200 hover:bg-teal-50 disabled:opacity-60"
        >
          <RefreshCw size={15} className={syncCdi.isPending ? 'animate-spin' : ''} />
          {syncCdi.isPending ? 'Consultando Banco Central…' : 'Tentar atualizar CDI'}
        </button>
        {syncCdi.data && <p role="status">{syncCdi.data.message}</p>}
        {syncCdi.error && <p role="alert">Não foi possível consultar o Banco Central. Tente novamente mais tarde.</p>}
      </div>
    </div>
  )
}
