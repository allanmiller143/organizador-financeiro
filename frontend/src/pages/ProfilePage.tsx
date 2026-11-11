import { useState, type FormEvent } from 'react'

import { Button } from '../components/Button'
import { TextField } from '../components/TextField'
import { useAuth } from '../hooks/useAuth'
import { describeError } from '../lib/errors'

export default function ProfilePage() {
  const { user, changePassword } = useAuth()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (newPassword !== confirmation) {
      setError('A nova senha e a confirmação não são iguais.')
      return
    }
    if (currentPassword === newPassword) {
      setError('Escolha uma senha diferente da atual.')
      return
    }

    setSubmitting(true)
    try {
      const message = await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      setSuccess(message)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmation('')
    } catch (requestError) {
      setError(describeError(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm font-medium text-teal-700">Minha conta</p>
        <h1 className="mt-1 text-2xl font-semibold">Perfil e segurança</h1>
        <p className="mt-1 text-sm text-slate-500">Confira seus dados e mantenha sua senha atualizada.</p>
      </header>

      <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold">Dados do perfil</h2>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Nome</dt>
            <dd className="mt-1 text-sm font-medium text-slate-900">{user?.name ?? '—'}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">E-mail</dt>
            <dd className="mt-1 break-all text-sm font-medium text-slate-900">{user?.email ?? '—'}</dd>
          </div>
        </dl>
      </section>

      <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <div >
          <h2 className="text-lg font-semibold">Alterar senha</h2>
          <p className="mt-1 text-sm text-slate-500">
            Confirme sua senha atual e escolha uma nova com pelo menos 8 caracteres.
            As outras sessões da conta serão encerradas.
          </p>

          <form onSubmit={handleSubmit} className="mt-5 space-y-4">
            <TextField
              variant="light"
              label="Senha atual"
              name="current-password"
              type="password"
              autoComplete="current-password"
              required
              maxLength={128}
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
            />
            <TextField
              variant="light"
              label="Nova senha"
              name="new-password"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              maxLength={128}
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
            />
            <TextField
              variant="light"
              label="Confirme a nova senha"
              name="new-password-confirmation"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              maxLength={128}
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
            />
            {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
            {success && <p role="status" className="text-sm text-emerald-700">{success}</p>}
            <Button type="submit" loading={submitting}>
              Salvar nova senha
            </Button>
          </form>
        </div>
      </section>
    </div>
  )
}
