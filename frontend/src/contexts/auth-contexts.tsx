import { createContext } from 'react'

import type { Credentials, PasswordChangeData, RegisterData } from '../api/auth'
import type { User } from '../api/types'

export type AuthContextValue = {
  user: User | null
  isLoading: boolean
  login: (data: Credentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  changePassword: (data: PasswordChangeData) => Promise<string>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
