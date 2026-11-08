import { createContext } from 'react'

import type { Credentials, RegisterData } from '../api/auth'
import type { User } from '../api/types'

export type AuthContextValue = {
  user: User | null
  isLoading: boolean
  login: (data: Credentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)