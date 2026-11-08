import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'

// O NavLink avisa se o link é o da página atual (isActive), para destacá-lo.
function linkClass({ isActive }: { isActive: boolean }) {
  return `rounded-md px-3 py-1.5 text-sm ${
    isActive ? 'bg-slate-100 font-medium text-slate-900' : 'text-slate-600 hover:text-slate-900'
  }`
}

export function AppLayout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-6">
            <span className="font-semibold">Organizador Financeiro</span>
            <nav className="flex gap-1">
              <NavLink to="/" end className={linkClass}>
                Visão geral
              </NavLink>
              <NavLink to="/caixinhas" className={linkClass}>
                Caixinhas
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-slate-600">{user?.name}</span>
            <button onClick={logout} className="text-slate-600 hover:text-slate-900">
              Sair
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}