import { formatMoney } from '../../lib/format'
import type { Totals } from './types'

// Uma cor por caixinha, usada na barra de distribuição e nos pontinhos da lista.
const ACCOUNT_COLORS = [
  'bg-teal-500',
  'bg-sky-500',
  'bg-emerald-500',
  'bg-cyan-500',
  'bg-indigo-400',
  'bg-violet-400',
]

export function accountColor(index: number): string {
  return ACCOUNT_COLORS[index % ACCOUNT_COLORS.length]
}

export function greeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Bom dia'
  if (hour < 18) return 'Boa tarde'
  return 'Boa noite'
}

// Mantém um percentual entre 0 e 100, para as barras nunca vazarem.
export function clampPercent(value: number): number {
  if (!Number.isFinite(value)) return 0
  return Math.min(100, Math.max(0, value))
}

// Formata um número calculado aqui no front (os valores da API chegam como texto).
export function money(value: number): string {
  return formatMoney(String(value))
}

// Todas as contas da página ficam num lugar só.
export function summarize(totals: Totals) {
  const gross = Number(totals.gross_balance)
  const net = Number(totals.net_balance)
  const invested = Number(totals.invested)
  const grossYield = Number(totals.gross_yield)

  // Rendimento sobre o que foi aportado (evita dividir por zero).
  const yieldPercent = invested > 0 ? (grossYield / invested) * 100 : 0
  const yieldLabel = `${yieldPercent.toFixed(2).replace('.', ',')}%`

  // Rendimento depois do IR: o que sobra do líquido além do que foi aportado.
  const netYield = net - invested

  // Barra 1: quanto do saldo bruto é aporte e quanto é rendimento.
  const investedShare = gross > 0 ? clampPercent((invested / gross) * 100) : 0
  const yieldShare = gross > 0 ? 100 - investedShare : 0

  // Barra 2: quanto do saldo bruto fica com você e quanto vai para o IR.
  const netShare = gross > 0 ? clampPercent((net / gross) * 100) : 0
  const taxShare = gross > 0 ? 100 - netShare : 0

  return { yieldLabel, netYield, investedShare, yieldShare, netShare, taxShare }
}