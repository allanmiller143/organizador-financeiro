import { Outlet } from 'react-router-dom'

import { Header } from '../header/Header'

export function AppLayout() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 to-slate-50 text-slate-900">
      <Header />

      <main className="mx-auto max-w-5xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}