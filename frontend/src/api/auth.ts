import { request } from './client'
import type { AuthResponse, User } from './types'

export type Credentials = {
  email: string
  password: string
}

export type RegisterData = Credentials & {
  name: string
}

export const authApi = {
  register: (data: RegisterData) =>
    request<AuthResponse>('/auth/register', { method: 'POST', body: data, auth: false }),
  login: (data: Credentials) =>
    request<AuthResponse>('/auth/login', { method: 'POST', body: data, auth: false }),
  me: () => request<{ user: User }>('/auth/me'),
}