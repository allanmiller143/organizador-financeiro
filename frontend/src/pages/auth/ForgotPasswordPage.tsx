import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { authApi } from '../../api/auth'
import { Button } from '../../components/Button'
import { AuthLayout } from '../../components/layout/AuthLayout'
import { TextField } from '../../components/TextField'
import { describeError } from '../../lib/errors'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [debugUrl, setDebugUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setMessage('')
    setError('')
    setDebugUrl('')
    setSubmitting(true)
    try {
      const response = await authApi.requestPasswordReset(email)
      setMessage(response.message)
      setDebugUrl(response.debug_reset_url ?? '')
    } catch (requestError) {
      setError(describeError(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout title="Recuperar senha" subtitle="Enviaremos um link para o e-mail da sua conta.">
      <form onSubmit={handleSubmit} className="space-y-4">
        <TextField
          label="E-mail cadastrado"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        {message && <p role="status" className="text-sm text-emerald-100">{message}</p>}
        {error && <p role="alert" className="text-sm text-red-200">{error}</p>}
        {debugUrl && (
          <p className="break-all text-xs text-amber-100">
            Link local de teste: <a className="underline" href={debugUrl}>{debugUrl}</a>
          </p>
        )}
        <Button type="submit" variant="glass" loading={submitting} className="w-full">
          Enviar link de recuperação
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-white/80">
        <Link to="/login" className="font-semibold text-white underline-offset-4 hover:underline">
          Voltar para entrar
        </Link>
      </p>
    </AuthLayout>
  )
}
