import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { authApi, type Credentials, type RegisterData } from '../api/auth'
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
    queryClient.clear() // o próximo usuário não pode ver dados do anterior
  }, [queryClient])

  useEffect(() => {
    setSessionExpiredHandler(() => {
      setUser(null)
      queryClient.clear()
    })

    let cancelled = false

    async function restoreSession() {
      if (tokens.getRefresh() && (await refreshAccessToken())) {
        try {
          const { user } = await authApi.me()
          if (!cancelled) setUser(user)
        } catch (error) {
          if (error instanceof ApiError) tokens.clear()
        }
      }
      if (!cancelled) setIsLoading(false)
    }

    restoreSession()

    return () => {
      cancelled = true
      setSessionExpiredHandler(null)
    }
  }, [queryClient])

  const value = useMemo(
    () => ({
      user,
      isLoading,
      login: async (data: Credentials) => startSession(await authApi.login(data)),
      register: async (data: RegisterData) => startSession(await authApi.register(data)),
      logout,
    }),
    [user, isLoading, startSession, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}