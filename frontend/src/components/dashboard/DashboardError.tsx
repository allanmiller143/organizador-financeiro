import { AlertCircle } from 'lucide-react'

import { ApiError } from '../../api/client'

// Transforma o erro técnico numa frase que ajuda a pessoa.
function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === 'cdi_not_synced' || error.code === 'cdi_incomplete') {
      return 'Os dados do CDI ainda não estão completos. Rode "flask --app wsgi sync-cdi" no backend e recarregue a página.'
    }
    return error.message
  }
  return 'Não foi possível conectar ao servidor.'
}

export function DashboardError({ error }: { error: unknown }) {
  return (
    <div className="flex items-start gap-3 rounded-2xl bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-100">
      <AlertCircle size={18} className="mt-0.5 shrink-0" />
      <p>{errorMessage(error)}</p>
    </div>
  )
}