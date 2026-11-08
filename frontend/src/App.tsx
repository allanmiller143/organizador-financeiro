import { useState } from 'react'

import { authApi } from './api/auth'
import { ApiError } from './api/client'
import { useAuth } from './hooks/useAuth'

export default function App() {
  const { user, isLoading, login, register, logout } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')

  async function run(action: () => Promise<string | void>) {
    setMessage('')
    try {
      const result = await action()
      if (result) setMessage(result)
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : 'Erro de conexão.')
    }
  }

  const input = 'w-full rounded-lg border border-slate-300 px-3 py-2 text-sm'
  const button = 'rounded-lg bg-slate-900 px-4 py-2 text-sm text-white'

  if (isLoading) {
    return <main className="grid min-h-screen place-items-center">Carregando...</main>
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 text-slate-900">
      <div className="w-80 space-y-3 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h1 className="text-xl font-semibold">Teste de autenticação</h1>

        {user ? (
          <>
            <p className="text-sm">
              Olá, {user.name} ({user.email})
            </p>
            <div className="flex gap-2">
              <button
                className={button}
                onClick={() => run(async () => `me: ${(await authApi.me()).user.email}`)}
              >
                Chamar /auth/me
              </button>
              <button className={button} onClick={logout}>
                Sair
              </button>
            </div>
          </>
        ) : (
          <>
            <input className={input} placeholder="Nome" value={name} onChange={(e) => setName(e.target.value)} />
            <input className={input} placeholder="E-mail" value={email} onChange={(e) => setEmail(e.target.value)} />
            <input
              className={input}
              type="password"
              placeholder="Senha (mín. 8 caracteres)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <div className="flex gap-2">
              <button className={button} onClick={() => run(() => login({ email, password }))}>
                Entrar
              </button>
              <button className={button} onClick={() => run(() => register({ name, email, password }))}>
                Cadastrar
              </button>
            </div>
          </>
        )}

        {message && <p className="text-sm text-red-600">{message}</p>}
      </div>
    </main>
  )
}