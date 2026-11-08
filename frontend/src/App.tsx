import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from './components/AppLayout'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import AccountsPage from './pages/AccountsPage'
import AccountDetailPage from './pages/AccountDetailPage'
import { ProtectedRoute, PublicOnlyRoute } from './routes/guards'

export default function App() {
  return (
    <Routes>
      {/* Telas de visitante: só quem NÃO está logado vê. */}
      <Route element={<PublicOnlyRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Telas internas: só quem ESTÁ logado vê, todas dentro da moldura. */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/caixinhas" element={<AccountsPage />} />
          <Route path="/caixinhas/:accountId" element={<AccountDetailPage />} />
        </Route>
      </Route>

      {/* Qualquer endereço desconhecido volta para o início. */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}