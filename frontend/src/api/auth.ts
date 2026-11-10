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
  requestPasswordReset: (email: string) =>
    request<{ message: string; debug_reset_url?: string }>(
      '/auth/password-reset/request',
      { method: 'POST', body: { email }, auth: false },
    ),
  confirmPasswordReset: (data: { token: string; password: string }) =>
    request<{ message: string }>(
      '/auth/password-reset/confirm',
      { method: 'POST', body: data, auth: false },
    ),
}
