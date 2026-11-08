import { ApiError } from '../api/client'

// Os erros que uma tela precisa mostrar: um texto por campo + um texto geral.
export type FormErrors = {
  fields: Record<string, string>
  general: string
}

// "Sem erros": o estado inicial de um formulário.
export const noErrors: FormErrors = { fields: {}, general: '' }

export function toFormErrors(error: unknown): FormErrors {
  // Se nem chegou a ser uma resposta do backend, foi problema de conexão.
  if (!(error instanceof ApiError)) {
    return { fields: {}, general: 'Não foi possível conectar ao servidor.' }
  }

  const fields: Record<string, string> = {}

  // Erro de validação: o backend diz quais campos estão errados.
  // As mensagens dele são técnicas (em inglês), então usamos uma frase simples.
  for (const detail of error.details ?? []) {
    fields[detail.field] = 'Confira este campo.'
  }

  // E-mail repetido: a mensagem fica embaixo do campo de e-mail.
  if (error.code === 'email_taken') {
    fields.email = error.message
    return { fields, general: '' }
  }

  // Se não há erro de campo, o erro é geral (ex.: senha incorreta).
  const hasFieldErrors = Object.keys(fields).length > 0
  return { fields, general: hasFieldErrors ? '' : error.message }
}