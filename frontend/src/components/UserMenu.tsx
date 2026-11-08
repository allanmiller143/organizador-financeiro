import { useEffect, useRef, useState } from 'react'
import { ChevronDown, LogOut } from 'lucide-react'

import { useAuth } from '../hooks/useAuth'

function getInitials(name?: string) {
  if (!name) return '?'
  const parts = name.trim().split(/\s+/)
  const first = parts[0]?.[0] ?? ''
  const last = parts.length > 1 ? parts[parts.length - 1][0] : ''
  return (first + last).toUpperCase()
}

export function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return

    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') setOpen(false)
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [open])

  const initials = getInitials(user?.name)

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex cursor-pointer items-center gap-1.5 rounded-full p-1 pr-2 transition hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500"
      >
        <span className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-sky-400 to-teal-600 text-sm font-semibold text-white">
          {initials}
        </span>
        <ChevronDown
          size={16}
          className={`text-slate-500 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {/* sempre renderizado, para poder animar a abertura e o fechamento */}
      <div
        role="menu"
        className={`absolute right-0 mt-2 w-60 origin-top-right overflow-hidden rounded-2xl bg-white shadow-lg ring-1 ring-slate-200 transition duration-150 ${
          open
            ? 'visible translate-y-0 scale-100 opacity-100'
            : 'invisible -translate-y-1 scale-95 opacity-0'
        }`}
      >
        <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gradient-to-br from-sky-400 to-teal-600 text-sm font-semibold text-white">
            {initials}
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-900">{user?.name}</p>
            <p className="text-xs text-slate-500">Minha conta</p>
          </div>
        </div>

        <div className="p-1.5">
          <button
            role="menuitem"
            onClick={logout}
            className="flex w-full cursor-pointer items-center gap-3 rounded-xl px-3 py-2 text-left text-sm text-slate-700 transition hover:bg-slate-100 hover:text-slate-900"
          >
            <LogOut size={16} />
            Sair
          </button>
        </div>
      </div>
    </div>
  )
}