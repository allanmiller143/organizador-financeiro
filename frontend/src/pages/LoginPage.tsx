import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { AuthLayout } from '../components/AuthLayout'
import { Button } from '../components/Button'
import { TextField } from '../components/TextField'
import { useAuth } from '../hooks/useAuth'
import { noErrors, toFormErrors } from '../lib/errors'

export default function LoginPage() {
  const { login } = useAuth()

  // Uma "caixinha de memória" para cada coisa que a tela precisa lembrar.
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState(noErrors)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault() // impede o navegador de recarregar a página
    setErrors(noErrors)
    setSubmitting(true)
    try {
      await login({ email, password })
      // Deu certo: a portaria (PublicOnlyRoute) leva para dentro sozinha.
    } catch (error) {
      setErrors(toFormErrors(error)) // deu errado: mostra a mensagem no lugar certo
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout title="Entrar" subtitle="Acesse suas caixinhas e projeções.">
      <form onSubmit={handleSubmit} className="space-y-4">
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
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.fields.password}
        />

        {errors.general && <p className="text-sm text-red-600">{errors.general}</p>}

        <Button type="submit" loading={submitting} className="w-full">
          Entrar
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-600">
        Não tem conta?{' '}
        <Link to="/register" className="font-medium text-emerald-700 hover:underline">
          Cadastre-se
        </Link>
      </p>
    </AuthLayout>
  )
}