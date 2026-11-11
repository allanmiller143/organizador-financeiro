import { NavLink } from 'react-router-dom'
import { LayoutDashboard, PiggyBank, TrendingUp } from 'lucide-react'

import { Logo } from './Logo'
import { UserMenu } from './UserMenu'

// O NavLink avisa se o link é o da página atual (isActive), para destacá-lo.
function linkClass({ isActive }: { isActive: boolean }) {
  return `inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition ${
    isActive
      ? 'bg-teal-50 text-teal-700'
      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
  }`
}

export function Header() {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-3 sm:gap-6">
          <div className="flex items-center gap-2">
          <Logo />
            <span className="text-sm font-bold tracking-tight text-slate-900">NuBox</span>
          </div>
          <nav className="flex gap-1">
            <NavLink to="/" end className={linkClass}>
              <LayoutDashboard size={16} />
              <span className="hidden sm:inline">Visão geral</span>
            </NavLink>
            <NavLink to="/caixinhas" className={linkClass}>
              <PiggyBank size={16} />
              <span className="hidden sm:inline">Caixinhas</span>
            </NavLink>
            <NavLink to="/projecao" className={linkClass}>
              <TrendingUp size={16} />
              <span className="hidden sm:inline">Projeção</span>
            </NavLink>
          </nav>
        </div>

        <UserMenu />
      </div>
    </header>
  )
}
