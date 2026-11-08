import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import type { Account } from '../api/types'
import { useUpdateAccount } from '../hooks/useAccounts'
import { describeError, noErrors, toFormErrors } from '../lib/errors'
import { formatCdi, formatDate } from '../lib/format'
import { Button } from '../components/Button'
import { Field } from '../components/Field'

type AccountHeaderProps = {
  account: Account
}

export function AccountHeader({ account }: AccountHeaderProps) {
  // Duas gravações independentes: salvar a edição e arquivar/reativar.
  const edit = useUpdateAccount()
  const archive = useUpdateAccount()

  // O cabeçalho tem dois modos: só mostrando, ou editando.
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(account.name)
  const [institution, setInstitution] = useState(account.institution)

  // Estado derivado: os erros saem direto do erro da gravação.
  const errors = edit.error ? toFormErrors(edit.error) : noErrors

  function startEditing() {
    setName(account.name) // sempre começa com os valores atuais
    setInstitution(account.institution)
    edit.reset() // limpa erros de uma edição anterior
    setEditing(true)
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      await edit.mutateAsync({ id: account.id, data: { name, institution } })
      setEditing(false) // deu certo: volta ao modo "só mostrando"
    } catch {
      // o erro já ficou em edit.error e aparece embaixo dos campos
    }
  }

  function toggleArchive() {
    const message = account.is_active
      ? 'Arquivar esta caixinha? Ela some do dashboard e da projeção, mas o histórico continua guardado.'
      : 'Reativar esta caixinha?'
    if (window.confirm(message)) {
      archive.mutate({ id: account.id, data: { is_active: !account.is_active } })
    }
  }

  return (
    <div>
      <Link to="/caixinhas" className="text-sm text-slate-500 hover:text-slate-900">
        ← Caixinhas
      </Link>

      {editing ? (
        <form
          onSubmit={handleSave}
          className="mt-3 space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              label="Nome da caixinha"
              name="name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              error={errors.fields.name}
            />
            <Field
              label="Instituição"
              name="institution"
              required
              value={institution}
              onChange={(e) => setInstitution(e.target.value)}
              error={errors.fields.institution}
            />
          </div>
          <p className="text-xs text-slate-500">
            O rendimento ({formatCdi(account.cdi_percent)}) e a data de abertura não podem ser
            alterados.
          </p>

          {errors.general && <p className="text-sm text-red-600">{errors.general}</p>}

          <div className="flex items-center gap-4">
            <Button type="submit" loading={edit.isPending}>
              Salvar
            </Button>
            <button
              type="button"
              onClick={() => setEditing(false)}
              className="text-sm text-slate-600 hover:text-slate-900"
            >
              Cancelar
            </button>
          </div>
        </form>
      ) : (
        <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold">{account.name}</h1>
            <p className="mt-1 text-sm text-slate-500">
              {account.institution} · {formatCdi(account.cdi_percent)} · aberta em{' '}
              {formatDate(account.opened_on)}
              {!account.is_active && ' · arquivada'}
            </p>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <button onClick={startEditing} className="font-medium text-emerald-700 hover:underline">
              Editar
            </button>
            <button
              onClick={toggleArchive}
              disabled={archive.isPending}
              className="text-slate-600 hover:text-slate-900 disabled:opacity-50"
            >
              {account.is_active ? 'Arquivar' : 'Reativar'}
            </button>
          </div>
        </div>
      )}

      {archive.isError && (
        <p className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {describeError(archive.error)}
        </p>
      )}
    </div>
  )
}