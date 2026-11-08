import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { AuthLayout } from '../../components/layout/AuthLayout'
import { Button } from '../../components/Button'
import { TextField } from '../../components/TextField'
import { useAuth } from '../../hooks/useAuth'
import { noErrors, toFormErrors } from '../../lib/errors'

export default function RegisterPage() {
  const { register } = useAuth()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState(noErrors)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrors(noErrors)
    setSubmitting(true)
    try {
      await register({ name, email, password })
    } catch (error) {
      setErrors(toFormErrors(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout title="Criar conta" subtitle="Organize e projete os seus investimentos.">
      <form onSubmit={handleSubmit} className="space-y-4">
        <TextField
          label="Nome"
          name="name"
          autoComplete="name"
          required
          minLength={2}
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.fields.name}
        />
        <TextField
          label="E-mail"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.fields.email}
        />
        <TextField
          label="Senha"
          name="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.fields.password}
        />

        {errors.general && <p className="text-sm text-red-600">{errors.general}</p>}

        <Button type="submit" variant="glass" loading={submitting} className="w-full">
          Criar conta
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-600 text-white ">
        Já tem conta?{' '}
        <Link to="/login" className="font-semibold text-white underline-offset-4 transition hover:underline hover:text-sky-200">
            Entrar
        </Link>
      </p>
    </AuthLayout>
  )
}