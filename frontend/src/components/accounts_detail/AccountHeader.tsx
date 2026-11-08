import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Archive,
  ArchiveRestore,
  ArrowLeft,
  CalendarDays,
  Landmark,
  Pencil,
  Percent,
  Plus,
  TrendingUp,
} from 'lucide-react'

import type { Account } from '../../api/types'
import { useUpdateAccount } from '../../hooks/useAccounts'
import { describeError } from '../../lib/errors'
import { formatCdi, formatDate, formatMoney } from '../../lib/format'
import { ErrorMessage } from '../ErrorMessage'
import { EditAccountDialog } from './EditAccountDialog'
import { yieldPercentLabel } from './helpers'
import type { SummaryQuery } from './types'

type AccountHeaderProps = {
  account: Account
  summary: SummaryQuery
  onNewTransaction: () => void
}

const iconButton =
  'grid h-9 w-9 cursor-pointer place-items-center rounded-xl bg-white/15 text-white ring-1 ring-white/40 transition hover:bg-white/25 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white disabled:cursor-not-allowed disabled:opacity-50'

const chip =
  'inline-flex items-center gap-1.5 rounded-full bg-white/15 px-2.5 py-1 text-xs font-medium ring-1 ring-white/25'

export function AccountHeader({ account, summary, onNewTransaction }: AccountHeaderProps) {
  const archive = useUpdateAccount()
  const [editing, setEditing] = useState(false)

  function toggleArchive() {
    const message = account.is_active
      ? 'Arquivar esta caixinha? Ela some do dashboard e da projeção, mas o histórico continua guardado.'
      : 'Reativar esta caixinha?'
    if (window.confirm(message)) {
      archive.mutate({ id: account.id, data: { is_active: !account.is_active } })
    }
  }

  const data = summary.data
  const archiveLabel = account.is_active ? 'Arquivar' : 'Reativar'

  return (
    <div className="space-y-3">
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-sky-500 to-teal-600 p-5 text-white shadow-lg sm:p-6">
        <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-white/10" />
        <div className="pointer-events-none absolute -bottom-24 right-24 h-56 w-56 rounded-full bg-white/10" />

        <div className="relative space-y-4">
          {/* Linha de cima: voltar e ações */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Link
              to="/caixinhas"
              className="inline-flex items-center gap-1.5 text-sm text-white/80 transition hover:text-white"
            >
              <ArrowLeft size={16} />
              Caixinhas
            </Link>

            <div className="flex items-center gap-2">
              <button
                onClick={onNewTransaction}
                className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-white px-3.5 py-2 text-sm font-semibold text-teal-700 shadow-sm transition hover:bg-teal-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-teal-600"
              >
                <Plus size={16} />
                Novo lançamento
              </button>
              <button
                onClick={() => setEditing(true)}
                aria-label="Editar caixinha"
                title="Editar"
                className={iconButton}
              >
                <Pencil size={16} />
              </button>
              <button
                onClick={toggleArchive}
                disabled={archive.isPending}
                aria-label={archiveLabel}
                title={archiveLabel}
                className={iconButton}
              >
                {account.is_active ? <Archive size={16} /> : <ArchiveRestore size={16} />}
              </button>
            </div>
          </div>

          {/* Nome e etiquetas à esquerda, saldos à direita */}
          <div className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-3xl font-semibold">{account.name}</h1>
                {!account.is_active && (
                  <span className="rounded-full bg-white/25 px-2.5 py-1 text-xs font-semibold">
                    Arquivada
                  </span>
                )}
              </div>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span className={chip}>
                  <Landmark size={14} />
                  {account.institution}
                </span>
                <span className={chip}>
                  <Percent size={14} />
                  {formatCdi(account.cdi_percent)}
                </span>
                <span className={chip}>
                  <CalendarDays size={14} />
                  aberta em {formatDate(account.opened_on)}
                </span>
                {data && (
                  <>
                    <span className="inline-flex items-center gap-1 rounded-full bg-white/25 px-2.5 py-1 text-xs font-semibold">
                      <TrendingUp size={14} />
                      {yieldPercentLabel(data.invested, data.gross_yield)} de rendimento
                    </span>
                    <span className="text-xs text-white/70">
                      Atualizado até {formatDate(data.as_of)}
                    </span>
                  </>
                )}
              </div>
            </div>

            <div className="lg:text-right">
              <p className="text-sm text-white/80">
                Saldo bruto <span className="text-white/60">· antes do IR</span>
              </p>
              {data ? (
                <>
                  <p className="mt-1 text-4xl font-semibold tabular-nums">
                    {formatMoney(data.gross_balance)}
                  </p>
                  <div className="mt-2 inline-flex items-baseline gap-2 rounded-xl bg-white/15 px-3 py-1.5 ring-1 ring-white/30">
                    <span className="text-xs text-white/80">Líquido · após o IR</span>
                    <span className="text-lg font-semibold tabular-nums">
                      {formatMoney(data.net_balance)}
                    </span>
                  </div>
                </>
              ) : summary.isError ? (
                <p className="mt-2 text-sm text-white/80">Não foi possível calcular o saldo.</p>
              ) : (
                <div className="mt-2 h-10 w-48 animate-pulse rounded-lg bg-white/20 lg:ml-auto" />
              )}
            </div>
          </div>
        </div>
      </section>

      {archive.isError && <ErrorMessage message={describeError(archive.error)} />}

      <EditAccountDialog account={account} open={editing} onClose={() => setEditing(false)} />
    </div>
  )
}