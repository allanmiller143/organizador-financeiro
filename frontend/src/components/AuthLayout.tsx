import type { ReactNode } from 'react'

type AuthLayoutProps = {
  title: string
  subtitle: string
  children: ReactNode
}

export function AuthLayout({ title, subtitle, children }: AuthLayoutProps) {
  return (
    <main
      className="grid min-h-screen place-items-center bg-cover bg-center px-4"
      style={{ backgroundImage: "url('/bg-neve.jpg')" }}
    >
      <div className="w-full max-w-md rounded-4xl border border-white/40 bg-slate-900/25 p-8 text-white shadow-2xl backdrop-blur-md">
        <h1 className="text-3xl font-semibold">{title}</h1>
        <p className="mt-1 text-sm text-white/80">{subtitle}</p>
        <div className="mt-6">{children}</div>
      </div>
    </main>
  )
}