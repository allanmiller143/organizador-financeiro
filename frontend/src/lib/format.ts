const money = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const percent = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
})

export function formatMoney(value: string): string {
  return money.format(Number(value))
}

export function formatPercent(value: string): string {
  return `${percent.format(Number(value))}%`
}

export function formatDate(iso?: string | null): string {
  if (!iso || !/^\d{4}-\d{2}-\d{2}$/.test(iso)) return '—'
  const [year, month, day] = iso.split('-')
  return `${day}/${month}/${year}`
}

export function formatCdi(value: string): string {
  const number = Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 2 })
  return `${number}% do CDI`
}

// A data de hoje no formato do <input type="date">: "AAAA-MM-DD".
// O formato sueco (sv-SE) é exatamente esse, e usa o fuso do seu computador.
export function todayIso(): string {
  return new Date().toLocaleDateString('sv-SE')
}

const moneyCompact = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  notation: 'compact', // 1.200.000 vira "R$ 1,2 mi"
  maximumFractionDigits: 1,
})

// Para os números do eixo do gráfico, que precisam ser curtos.
export function formatMoneyCompact(value: number): string {
  return moneyCompact.format(value)
}

export function formatDuration(totalMonths: number): string {
  const years = Math.floor(totalMonths / 12)
  const months = totalMonths % 12
  const parts: string[] = []
  if (years > 0) parts.push(`${years} ${years === 1 ? 'ano' : 'anos'}`)
  if (months > 0) parts.push(`${months} ${months === 1 ? 'mês' : 'meses'}`)
  return parts.join(' e ') || '0 meses'
}

const MONTH_NAMES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

// "2025-01" -> "jan/25"
export function formatMonth(month: string): string {
  const [year, monthNumber] = month.split('-')
  return `${MONTH_NAMES[Number(monthNumber) - 1]}/${year.slice(2)}`
}
