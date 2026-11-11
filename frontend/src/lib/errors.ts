import { ApiError } from '../api/client'

export type FormErrors = {
  fields: Record<string, string>
  general: string
}

export const noErrors: FormErrors = { fields: {}, general: '' }

export function toFormErrors(error: unknown): FormErrors {
  if (!(error instanceof ApiError)) {
    return { fields: {}, general: 'Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.' }
  }

  const fields: Record<string, string> = {}
  for (const detail of error.details ?? []) {
    fields[detail.field] = 'Confira este campo.'
  }

  if (error.code === 'email_taken') {
    fields.email = error.message
    return { fields, general: '' }
  }

  if (error.code === 'date_in_future' || error.code === 'date_before_opening') {
    fields.occurred_on = error.message
    return { fields, general: '' }
  }

  const hasFieldErrors = Object.keys(fields).length > 0
  return { fields, general: hasFieldErrors ? '' : describeError(error) }
}

export function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === 'network_error') {
      return 'Não foi possível acessar o servidor agora. Verifique sua internet e tente novamente.'
    }
    if (error.code === 'cdi_not_synced' || error.code === 'cdi_incomplete') {
      return 'Faltam dados do CDI para este período. Sincronize o CDI no backend e tente novamente.'
    }
    if (error.status >= 500 && error.code === 'unknown_error') {
      return 'O serviço está temporariamente indisponível. Tente novamente em instantes.'
    }
    return error.message
  }
  return 'Não foi possível acessar o servidor. Verifique sua conexão e tente novamente.'
}
