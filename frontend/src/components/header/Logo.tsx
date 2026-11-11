import { Link } from 'react-router-dom'
import { PiggyBank } from 'lucide-react'

export function Logo() {
  return (
    <Link
      to="/"
      aria-label="NuBox — ir para a visão geral"
      className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-sky-400 to-teal-600 text-white shadow-sm transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2"
    >
      <PiggyBank size={20} />
    </Link>
  )
}
