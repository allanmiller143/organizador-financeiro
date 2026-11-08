import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'

function Loading() {
  return (
    <main className="grid min-h-screen place-items-center text-sm text-slate-500">
      Carregando...
    </main>
  )
}

// PORTARIA 1: só deixa entrar quem está logado.
export function ProtectedRoute() {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  // 1) O app ainda está conferindo o login? Espera.
  if (isLoading) return <Loading />

  // 2) Sem usuário? Manda para o login, anotando de onde a pessoa veio.
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  // 3) Tudo certo: <Outlet /> significa "pode entrar, mostre a tela de dentro".
  return <Outlet />
}

// PORTARIA 2: só deixa ver login/cadastro quem NÃO está logado.
export function PublicOnlyRoute() {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) return <Loading />

  // Já está logado? Leva de volta para onde a pessoa queria ir (ou para o início).
  if (user) {
    const from = (location.state as { from?: string } | null)?.from ?? '/'
    return <Navigate to={from} replace />
  }

  return <Outlet />
}