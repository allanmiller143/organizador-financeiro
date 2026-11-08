import { PiggyBank } from 'lucide-react'

import { Button } from '../Button'

export function EmptyAccounts({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl bg-white px-6 py-10 text-center shadow-sm ring-1 ring-slate-200">
      <span className="grid h-12 w-12 place-items-center rounded-full bg-teal-50 text-teal-600">
        <PiggyBank size={24} />
      </span>
      <p className="text-sm text-slate-500">Você ainda não tem caixinhas.</p>
      <Button variant="primary" onClick={onCreate}>
        Cadastrar a primeira
      </Button>
    </div>
  )
}