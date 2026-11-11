import { tokens } from './tokens'
import type { ApiErrorBody, ApiFieldError } from './types'

export class ApiError extends Error {
  status: number
  code: string
  details?: ApiFieldError[]

  constructor(status: number, code: string, message: string, details?: ApiFieldError[]) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  auth?: boolean
}

let sessionExpiredHandler: (() => void) | null = null

const API_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')
const REQUEST_TIMEOUT_MS = 20_000
const NETWORK_ERROR_MESSAGE = 'Não foi possível acessar o servidor. Verifique sua conexão e tente novamente.'

export function setSessionExpiredHandler(handler: (() => void) | null) {
  sessionExpiredHandler = handler
}

async function send(path: string, options: RequestOptions, token: string | null): Promise<Response> {
  const headers: Record<string, string> = {}
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  try {
    return await fetch(`${API_URL}/api${path}`, {
      method: options.method ?? 'GET',
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    })
  } catch {
    throw new ApiError(0, 'network_error', NETWORK_ERROR_MESSAGE)
  }
}

async function parseError(response: Response): Promise<ApiError> {
  let body: Partial<ApiErrorBody> | null = null
  try {
    body = await response.json()
  } catch {
    // Corpo vazio ou inesperado.
  }
  const error = body?.error
  return new ApiError(
    response.status,
    error?.code ?? 'unknown_error',
    error?.message ?? 'O servidor não conseguiu concluir a solicitação. Tente novamente.',
    error?.details,
  )
}

async function doRefresh(): Promise<boolean> {
  const refreshToken = tokens.getRefresh()
  if (!refreshToken) return false

  const response = await send('/auth/refresh', { method: 'POST' }, refreshToken)
  if (!response.ok) return false

  const data = (await response.json()) as { access_token: string }
  tokens.setAccess(data.access_token)
  return true
}

let refreshPromise: Promise<boolean> | null = null

export function refreshAccessToken(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = doRefresh().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const useAuth = options.auth !== false
  let response = await send(path, options, useAuth ? tokens.getAccess() : null)

  if (response.status === 401 && useAuth) {
    if (await refreshAccessToken()) {
      response = await send(path, options, tokens.getAccess())
    } else {
      tokens.clear()
      sessionExpiredHandler?.()
    }
  }

  if (!response.ok) throw await parseError(response)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export async function requestBlob(path: string): Promise<Blob> {
  let response = await send(path, {}, tokens.getAccess())
  if (response.status === 401) {
    if (await refreshAccessToken()) {
      response = await send(path, {}, tokens.getAccess())
    } else {
      tokens.clear()
      sessionExpiredHandler?.()
    }
  }
  if (!response.ok) throw await parseError(response)
  return response.blob()
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
