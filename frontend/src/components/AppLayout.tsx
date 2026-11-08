import { Outlet } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'

export function AppLayout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <span className="font-semibold">Organizador Financeiro</span>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-slate-600">{user?.name}</span>
            <button onClick={logout} className="text-slate-600 hover:text-slate-900">
              Sair
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        {/* <Outlet /> = "aqui entra a tela da vez" (dashboard, caixinhas...) */}
        <Outlet />
      </main>
    </div>
  )
}