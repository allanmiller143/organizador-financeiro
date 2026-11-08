import { Button } from '../components/Button'
import { useAuth } from '../hooks/useAuth'

export default function DashboardPage() {
  const { user, logout } = useAuth()

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-slate-900">Olá, {user?.name}</h1>
          <Button onClick={logout}>Sair</Button>
        </div>
        <p className="mt-4 text-slate-600">O dashboard vai aparecer aqui.</p>
      </div>
    </main>
  )
}