import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { authApi, type Credentials, type PasswordChangeData, type RegisterData } from '../api/auth'
import { ApiError, refreshAccessToken, setSessionExpiredHandler } from '../api/client'
import { tokens } from '../api/tokens'
import type { AuthResponse, User } from '../api/types'
import { AuthContext } from './auth-contexts'

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const startSession = useCallback((data: AuthResponse) => {
    tokens.setAccess(data.access_token)
    tokens.setRefresh(data.refresh_token)
    setUser(data.user)
  }, [])

  const logout = useCallback(() => {
    tokens.clear()
    setUser(null)
    queryClient.clear()
  }, [queryClient])

  useEffect(() => {
    setSessionExpiredHandler(() => {
      setUser(null)
      queryClient.clear()
    })

    let cancelled = false

    async function restoreSession() {
      try {
        if (!tokens.getRefresh()) return
        const refreshed = await refreshAccessToken()
        if (!refreshed) {
          tokens.clear()
          return
        }
        const { user: restoredUser } = await authApi.me()
        if (!cancelled) setUser(restoredUser)
      } catch (error) {
        // Uma falha de rede não deve deixar o spinner preso nem apagar a sessão local.
        if (!(error instanceof ApiError && error.code === 'network_error')) {
          tokens.clear()
        }
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    void restoreSession()

    return () => {
      cancelled = true
      setSessionExpiredHandler(null)
    }
  }, [queryClient])

  const changePassword = useCallback(async (data: PasswordChangeData) => {
    const response = await authApi.changePassword(data)
    tokens.setAccess(response.access_token)
    tokens.setRefresh(response.refresh_token)
    return response.message
  }, [])

  const value = useMemo(
    () => ({
      user,
      isLoading,
      login: async (data: Credentials) => startSession(await authApi.login(data)),
      register: async (data: RegisterData) => startSession(await authApi.register(data)),
      changePassword,
      logout,
    }),
    [user, isLoading, startSession, changePassword, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
