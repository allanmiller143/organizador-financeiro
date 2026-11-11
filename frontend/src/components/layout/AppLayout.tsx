import { Outlet } from 'react-router-dom'

import { Header } from '../header/Header'

export function AppLayout() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 to-slate-50 text-slate-900">
      <Header />

      <main className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          O NuBox é uma simulação das Caixinhas do Nubank. Regras e arredondamentos podem fazer os valores divergirem dos valores reais.
        </div>
        <Outlet />
      </main>
    </div>
  )
}
