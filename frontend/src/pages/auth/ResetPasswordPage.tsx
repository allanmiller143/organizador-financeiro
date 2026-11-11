import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { authApi } from '../../api/auth'
import { Button } from '../../components/Button'
import { AuthLayout } from '../../components/layout/AuthLayout'
import { TextField } from '../../components/TextField'
import { describeError } from '../../lib/errors'

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState('')
  const [complete, setComplete] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    if (password !== confirmation) {
      setError('As senhas não conferem.')
      return
    }
    if (!token) {
      setError('Este link está incompleto. Solicite um novo link de recuperação.')
      return
    }

    setSubmitting(true)
    try {
      await authApi.confirmPasswordReset({ token, password })
      setComplete(true)
    } catch (requestError) {
      setError(describeError(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout title="Criar nova senha" subtitle="Escolha uma senha com pelo menos 8 caracteres.">
      {complete ? (
        <div className="space-y-4">
          <p role="status" className="text-sm text-emerald-100">
            Senha redefinida. Entre usando a nova senha.
          </p>
          <Link to="/login" className="block text-center font-semibold text-white underline-offset-4 hover:underline">
            Ir para entrar
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <TextField
            label="Nova senha"
            name="password"
            type="password"
            autoComplete="new-password"
            minLength={8}
            maxLength={128}
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <TextField
            label="Confirme a nova senha"
            name="password-confirmation"
            type="password"
            autoComplete="new-password"
            minLength={8}
            maxLength={128}
            required
            value={confirmation}
            onChange={(event) => setConfirmation(event.target.value)}
          />
          {error && <p role="alert" className="text-sm text-red-200">{error}</p>}
          <Button type="submit" variant="glass" loading={submitting} className="w-full">
            Salvar nova senha
          </Button>
        </form>
      )}
    </AuthLayout>
  )
}
