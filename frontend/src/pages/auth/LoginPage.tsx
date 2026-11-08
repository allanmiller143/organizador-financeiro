import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Mail } from 'lucide-react'
import { AuthLayout } from '../../components/layout/AuthLayout'
import { Button } from '../../components/Button'
import { TextField } from '../../components/TextField'
import { useAuth } from '../../hooks/useAuth'
import { noErrors, toFormErrors } from '../../lib/errors'

export default function LoginPage() {
  const { login } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState(noErrors)
  const [submitting, setSubmitting] = useState(false)
  const [remember, setRemember] = useState(true)


  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault() // impede o navegador de recarregar a página
    setErrors(noErrors)
    setSubmitting(true)
    try {
      await login({ email, password })
    } catch (error) {
      setErrors(toFormErrors(error)) 
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
            icon={Mail}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.fields.password}
        />
        <label className="flex w-fit cursor-pointer items-center gap-2 text-sm text-white/90 transition hover:text-white">
            <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="h-4 w-4 cursor-pointer rounded accent-teal-600"
            />
            Lembrar de mim
        </label>

        {errors.general && <p className="text-sm text-red-300">{errors.general}</p>}

        <Button type="submit" loading={submitting} className="w-full">
            Entrar
        </Button>
        </form>

        <p className="mt-6 text-center text-sm text-white/80">
        Não tem conta?{' '}
        <Link
            to="/register"
            className="font-semibold text-white underline-offset-4 transition hover:underline hover:text-sky-200"
            >
            Cadastre-se
        </Link>
        </p>
    </AuthLayout>
    )
}