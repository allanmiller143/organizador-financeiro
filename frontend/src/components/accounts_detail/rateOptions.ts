import { formatCdi } from '../../lib/format'

export type RateOption = {
  key: string
  label: string
  cdiPercent: string
  termMonths: number
  locked: boolean
}

export const CUSTOM_LOCKED_RATE_KEY = 'custom-locked'

// Dinheiro trancado: rende mais durante a trava e depois volta ao padrão da caixinha.
const LOCKED_RATES = [
  { cdiPercent: '104.50', termMonths: 6, label: '104,5% do CDI · 6 meses trancado' },
  { cdiPercent: '105.00', termMonths: 12, label: '105% do CDI · 1 ano trancado' },
  { cdiPercent: '105.50', termMonths: 18, label: '105,5% do CDI · 1 ano e 6 meses trancado' },
  { cdiPercent: '106.00', termMonths: 24, label: '106% do CDI · 2 anos trancado' },
]

// Só caixinhas de até 100% do CDI aceitam dinheiro trancado.
export function canLockMoney(accountCdiPercent: string): boolean {
  return Number(accountCdiPercent) <= 100
}

export function rateOptions(accountCdiPercent: string): RateOption[] {
  const base: RateOption = {
    key: 'base',
    label: `${formatCdi(accountCdiPercent)} · liquidez diária`,
    cdiPercent: accountCdiPercent,
    termMonths: 24,
    locked: false,
  }
  if (!canLockMoney(accountCdiPercent)) return [base]
  return [
    base,
    ...LOCKED_RATES.map((rate) => ({
      key: `${rate.cdiPercent}-${rate.termMonths}`,
      label: rate.label,
      cdiPercent: rate.cdiPercent,
      termMonths: rate.termMonths,
      locked: true,
    })),
  ]
}

// Qual opção do seletor corresponde a um aporte já salvo.
export function optionKeyFor(
  accountCdiPercent: string,
  transaction: { locked: boolean; cdi_percent: string; term_months: number },
): string {
  if (!transaction.locked) return 'base'
  const match = rateOptions(accountCdiPercent).find(
    (option) =>
      option.locked &&
      Number(option.cdiPercent) === Number(transaction.cdi_percent) &&
      option.termMonths === transaction.term_months,
  )
  return match?.key ?? CUSTOM_LOCKED_RATE_KEY
}
