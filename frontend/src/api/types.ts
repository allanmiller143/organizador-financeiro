export type User = {
  id: string
  name: string
  email: string
}

export type AuthResponse = {
  user: User
  access_token: string
  refresh_token: string
}

export type ApiFieldError = {
  field: string
  message: string
}

export type ApiErrorBody = {
  error: {
    code: string
    message: string
    details?: ApiFieldError[]
  }
}