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

export function formatDate(iso: string): string {
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